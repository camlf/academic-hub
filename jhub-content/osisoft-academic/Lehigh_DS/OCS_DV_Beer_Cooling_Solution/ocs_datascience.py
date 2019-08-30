
import datetime
from dateutil.parser import parse
import functools
import io
import json
import re
import requests
import time
# For parallel HTTP requests
from concurrent.futures import ThreadPoolExecutor
from requests_futures.sessions import FuturesSession
import pandas as pd

'''
# Fermenter Vessel Dataview Explaination 

## Here are all the streams name of interest for Fermenter Vessel ID 31 with their target column in the Dataview 

| Stream Name | DV Column Name | Description | 
|-------------|----------------|-------------|
| acsbrew.BREWERY.B2_CL_C2_FV31_LT1360/PV.CV | `Volume` | Vessel Volume 
| acsbrew.BREWERY.B2_CL_C2_FV31_TIC1360C/PV.CV | `Top TIC PV` | Vessel Bottom Temperture Indicator Controller Process Value
| acsbrew.BREWERY.B2_CL_C2_FV31_TIC1360C/OUT.CV | `Top TIC OUT` | Vessel Top Temperature Indicator Controller Output
| acsbrew.BREWERY.B2_CL_C2_FV31/Plato | `Plato` | The specific gravity of the vessel in plato
| acsbrew.BREWERY.B2_CL_C2_FV31_TIC1360B/PV.CV | `Middle TIC PV` | Vessel Middle Temperature Indicator Controller Process 
| acsbrew.BREWERY.B2_CL_C2_FV31_TIC1360B/OUT.CV | `Middle TIC OUT` | Vessel Middle Temperature Indicator Controller Output
| acsbrew.BREWERY.B2_CL_C2_FV31/DcrsFvFullPlato | `FV Full Plato` | The specific gravity of the vessel in plato at the end of filling
| acsbrew.BREWERY.FV31.Fermentation ID.194fa814-869f-5f35-3501-0b9198ac52e1 | `Fermentation ID` | Unique ID for fermentation batch 
| acsbrew.BREWERY.B2_CL_C2_FV31/BRAND.CV | `Brand` | Vessel Brand
| acsbrew.BREWERY.B2_CL_C2_FV31_TIC1360A/PV.CV | `Bottom TIC PV` | Vessel Bottom Temperture Indicator Controller Process Value
| acsbrew.BREWERY.B2_CL_C2_FV31_TIC1360A/OUT.CV |`Bottom TIC OUT` | Vessel Bottom Temperature Indicator Controller Output
| acsbrew.BREWERY.FV31.ADF2 | `ADF` | Apparent Degree of Fermentation 
| acsbrew.BREWERY.B2_CL_C2_FV31/STATUS.CV | `Status` | * Vessel Status

The other 5 fermenter vessels (ID 32 up to 36) streams have a similar structure but yet all somewhat different. For example
below are all the stream names for the 'Volume' column: 

FVID Stream Name
32   acsbrew.BREWERY.B2_CL_C2_FV32_LT1380/PV.CV
33   acsbrew.BREWERY.B2_CL_C2_FV33_LT1400/PV.CV
34   acsbrew.BREWERY.B2_CL_C2_FV34_LT1420/PV.CV
35   acsbrew.BREWERY.B2_CL_C2_FV35_LT1440/PV.CV
36   acsbrew.BREWERY.B2_CL_C2_FV36_LT1460/PV.CV

Each fermenter has its own Dataview which is built within function fermenter_dataview_def. The mapping of streams to dataview
column is done by __dv_column_mappings which:
  1) extract all streams for a given fermenter vessel ID fv_id
  2) iterate over list of pairs called full_map (defined below) to:
        a) extract one stream using a filter (first item of pair)
        b) map extracted stream to its column (column name is second item of pair)
  3) end result of __dv_column_mappings is a JSON object describing all the columns for the given fermenter, including
       a special column for the timestamp
  

'''


# Stream match to column name for Fermenter Vessel Dataview  
full_map = [
    # filter, column
    ('_LT', 'Volume'),
    ('C/PV.CV', 'Top TIC PV'),
    ('C/OUT.CV', 'Top TIC OUT'),
    ('/Plato', 'Plato'),
    ('B/PV.CV', 'Middle TIC PV'),
    ('B/OUT.CV', 'Middle TIC OUT'),
    ('FullPlato', 'FV Full Plato'),
    ('Fermentation', 'Fermentation ID'),
    ('BRAND', 'Brand'),
    ('A/PV.CV', 'Bottom TIC PV'),
    ('A/OUT.CV', 'Bottom TIC OUT'),
    ('ADF2', 'ADF'),
    ('STATUS', 'Status'),
]

dv_columns = ['Timestamp'] + [ column for (_, column) in full_map ]  

def csv_postproc(reply):
    # ds_map = [ (',255,', ',Bad Input,'), (',255,', ',Bad Input,'), (',307,', ',Bad,'),
    #          (',313,', ',Comm Fail,'), (',246,', ',I/O Timeout,'), (',249,', ',Calc Failed,')]
    # 255 Bad Input, 307 Bad, 313 Comm Fail, 246 I/O Timeout
    ds_map = [ (',,', ',Bad Input,'), (',,', ',Bad Input,') ]
    for s, ds in ds_map:
        reply = re.sub(s, ds, reply)
    return reply


# Request in parallel all the dataviews, return the concatenated dataframe
def get_ocs_dataframe(dataviews, headers, workers=8):
    ti = datetime.datetime.now()
    session = FuturesSession(executor=ThreadPoolExecutor(max_workers=workers))
    rs = [session.get(u, headers=headers) for u in dataviews]
    resps = [r.result() for r in rs]
    print('Requests completed in', datetime.datetime.now() - ti) 
    print(resps)
    for r in resps: 
        if r.status_code != 200:
            raise Exception(f'Failed to get access token endpoint from discovery URL: {r.status_code}: {r.text}')
    dfs = [pd.read_csv(io.StringIO(csv_postproc(r.text)), parse_dates=['Timestamp']) for r in resps]
    df = pd.concat(dfs, sort=True)
    return(df[dv_columns])


def timer(func):
    """Print the runtime of the decorated function"""
    @functools.wraps(func)
    def wrapper_timer(*args, **kwargs):
        start_time = time.perf_counter()
        value = func(*args, **kwargs)
        end_time = time.perf_counter()
        run_time = end_time - start_time
        function_info = f"  ==> Finished {func.__name__!r} in".ljust(50)
        print(f"{function_info} {run_time:.4f} secs")
        return value
    return wrapper_timer


class OCSClient:
    def __init__(self, apiversion, tenant, url, clientId, clientSecret):
        self._resource_url = url
        self._tenant_id = tenant
        self._api_version = apiversion
        self._client_id = clientId
        self._client_secret = clientSecret
        self._namespace_id = None 
        self._headers = None
        
    def authorization_headers(self, namespace_id='fermenter__vessels'):
        self._namespace_id = namespace_id
        # Request a fresh authorization bearer token 
        discovery = requests.get(self._resource_url + '/identity/.well-known/openid-configuration', headers={'Accept': 'application/json'})
        if discovery.status_code < 200 or discovery.status_code >= 300:
            raise Exception(f'Failed to get access token endpoint from discovery URL: {discovery.status_code}: {discovery.text}')
        token_endpoint = discovery.json()['token_endpoint']
        authorization = requests.post(token_endpoint, data={'client_id': self._client_id, 
                                                            'client_secret': self._client_secret, 
                                                            'grant_type': 'client_credentials' })
        try: 
            headers = {
                'Authorization': 'bearer %s' % authorization.json()['access_token'],
                'Content-type': 'application/json',
                'Accept': 'text/plain', 
                'Request-Timeout': '60000' 
            }
        except KeyError:
            raise Exception("!!! Cannot get autorization token, please check client ID and secret")
        self._headers = headers
        return headers
    
    def namespace_url(self, namespace):
        self._namespace_id = namespace
        return self._resource_url + f'/api/{self._api_version}/Tenants/{self._tenant_id}/Namespaces/{namespace}' 
    
    def extract_streams_for_fermenter(self, fv_id):
        streams_url = self.namespace_url(self._namespace_id) + f'/Streams?query=name:*FV{fv_id}*'
        fv_streams = requests.get(streams_url, headers=self._headers)
        if fv_streams.status_code != 200:
            raise Exception(f'### Error: unable to get streams for FV {fv_id}, code {fv_streams.status_code} (url={streams_url})')
        streams = [stream['Name'] for stream in fv_streams.json()]
        stream_tags = { stream['Name']: stream['Id'] for stream in fv_streams.json() }  
        return streams, stream_tags
        
    def __dv_time_column(self):
        return [ 
            {
                "Name": "Timestamp",
                "MappingRule": {
                    "PropertyPaths": [
                        "Timestamp"
                    ]
                },
                "IsKey": True,
                "DataType": "DateTime"
            } ] 
    
    def __dv_column_def(self, column_def):
        name = column_def[1]
        tag = column_def[0]
        return {
            "Name": name,
            "MappingRule": {
                "PropertyPaths": [
                    "Value"
                ],
                "ItemIdentifier": {
                    "Resource": "Streams",
                    "Field": "Name",
                    "Value": tag,
                    "Function": "Equals"
                }
            }
        }
    
    def __dv_column_mappings(self, fv_id):
        streams, stream_tags = self.extract_streams_for_fermenter(fv_id)
        dv_names = [ (s, y) for (x, y) in full_map for s in streams if x in s] 
        return { "Columns": 
                    self.__dv_time_column() + 
                    [self.__dv_column_def(c) for c in dv_names]
               }

    
    def fermenter_dataview_def(self, fv_id, version='', start_index='2017-03-17T07:00:00Z', num_days=20, shift_period=0):
        dataview_id = f'DV{version}_FV{fv_id}'
        start_time = parse(start_index)
        period = datetime.timedelta(days=num_days)
        end_index = (start_time + period).isoformat()
        return dataview_id, {
            "Id": dataview_id, 
            "Name": dataview_id, 
            "Description": f'Fermentor {fv_id} DV',
            "Queries": [ {
                "Id": "Fermentor",
                "Query": {
                    "Resource": "Streams",
                    "Field": "Name",
                    "Value": f'FV{fv_id}',
                    "Function": "Contains"
                }
            } ],
            "GroupRules": [],
            "Mappings": self.__dv_column_mappings(fv_id),
            "IndexDataType": "DateTime",
            "IndexConfig": {
                "StartIndex": start_index,
                "EndIndex": end_index,
                "Mode": "Interpolated",
                "Interval": "00:01:00"
            }
        }
    
    def install_fermenter_dataviews(self, version='', last_fvid=36, num_days=20, verbose=False):
        dataview_url = self.namespace_url(self._namespace_id) + '/Dataviews/'
        dataviews = []
        for fv_id in range(31, last_fvid + 1):  
            dataview_id, dataview_def = self.fermenter_dataview_def(fv_id, version=version, num_days=num_days)
            dataviews.append(dataview_id)
            if verbose:
                print(f"DV ID: {dataview_id}, URL: {dataview_url + dataview_id}, \n  Defn: {json.dumps(dataview_def, indent=4, sort_keys=True)}")
            response = requests.post(dataview_url + dataview_id, headers=self._headers, json=dataview_def)
            print('Status:', response.status_code, 'Dataview Id:', dataview_id, response.text if response.status_code != 201 else '')
        dataview_urls = [dataview_url + f'{dv_id}/preview/interpolated?form=csvh&maxcount=100000' for dv_id in dataviews]
        return dataview_urls
    
    def create_fermenter_dataview(self, fv_id):
        dataview_url = self.namespace_url(self._namespace_id) + '/Dataviews/'
        dataview_id, dataview_def = self.fermenter_dataview_def(fv_id)
        # print(dataview_url, 'ID:', dataview_id, dataview_def)
        response = requests.post(dataview_url + dataview_id, headers=self._headers, json=dataview_def)
        print('Status:', response.status_code, 'Dataview Id:', dataview_id, 
                'Error: ' + response.text[:60] if response.status_code != 201 else '')
        return dataview_url + f'{dataview_id}'
    
    def get_single_fermenter_dataview(self, fv_id, start_index, end_index, interval='00:01:00'):
        dataview_id, _ = self.fermenter_dataview_def(fv_id)
        dataview_url = self.namespace_url(self._namespace_id) + \
            f'/Dataviews/{dataview_id}/preview/interpolated' + \
            f'?startIndex={start_index}&endIndex={end_index}' + \
            f'&interval={interval}&form=csvh&maxcount=200000'
        print('Url:', dataview_url)
        return get_ocs_dataframe([dataview_url], self._headers)
    
    def get_all_fermenters_dataviews(self, start_index, end_index, interval='00:01:00'):
        dataview_urls = []
        for fv_id in range(31, 37):
            dataview_id, _ = self.fermenter_dataview_def(fv_id)
            dataview_url = self.namespace_url(self._namespace_id) + \
                f'/Dataviews/{dataview_id}/preview/interpolated' + \
                f'?startIndex={start_index}&endIndex={end_index}' + \
                f'&interval={interval}&form=csvh&maxcount=200000'
            dataview_urls.append(dataview_url)
        print('Urls:', dataview_urls)
        return get_ocs_dataframe(dataview_urls, self._headers)
