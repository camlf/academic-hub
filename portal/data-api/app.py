import datetime as dt
import dateutil.parser as dp
import os

# import redis
import responder
import requests

# r = redis.Redis(host='academichub.redis.cache.windows.net', port=6380, db=0,
#                password='<PASSWORD>', ssl=True)

api = responder.API(static_dir="static")  # , static_route='/datas/static')


# @flask.route('/<path:path>')
# def hello(path):
# print(req)
# return f"yo! {path}"
#    resp = requests.get(f'https://academicpi.azure-api.net/hub/api/{path}', auth=('reader0', 'OSIsoft2017'))
#    return resp.text, resp.status_code


data_access_url = "https://academic.osisoft.com/hub-data"


@api.route("/google3a8ba05497fdc1cd.html")
def google_verif(req, resp):
    resp.text = "google-site-verification: google3a8ba05497fdc1cd.html"


@api.route("/.well-known/microsoft-identity-association.json")
def verify_domain(req, resp):
    # req['content-type'] = 'application/json'
    resp.media = {
       "associatedApplications": [
          {
             "applicationId": "862fa9da-5cad-4222-b799-d5d27aa937ff"
          }
       ]
    }


@api.route("/version")
def version(req, resp):
    resp.text = "0.8skip.0"


@api.route("/recorded")
async def archived(req, resp):
    print("Request:", dir(req))
    print("URL:", req.url)
    print("FURL:", req.full_url)
    print("Headers:", req.headers)
    print("Params:", req.params)
    resp.status_code = api.status_codes.HTTP_400
    root = req.params.get("db", "Classroom Data\\Source Data")
    try:
        authorization = req.headers["Authorization"]
        print("Auth:", authorization)
    except KeyError as e:
        if req.params.get("skipAuth", None): 
            authorization = "Basic cmVhZGVyMDpPU0lzb2Z0MjAxNw=="
            print("AAuth:", authorization)
        else:
            resp.text = f"ERROR: authorization header missing. Please check {data_access_url}: {e}"
            resp.status_code = api.status_codes.HTTP_401
            return
    try:
        element = req.params["element"]
        start_time = req.params["startTime"]
        end_time = req.params["endTime"]
        validate = req.params.get("validate", None) is not None
        max_count = int(req.params.get("maxCount", 2000))
    except KeyError as e:
        resp.text = f"ERROR: Missing element/startTime/endTime, please consult {data_access_url}: {e}"
        return
    try:
        start_time_t = dp.parse(start_time)
        end_time_t = dp.parse(end_time)
    except ValueError as e:
        if not "*" in [start_time, end_time]:
            resp.text = f"ERROR: Bad format for startTime and/or endTime parameters, please consult {data_access_url}: {e}"
            return
    path = "\\\\PIAF-ACAD\\" + root + "\\" + element
    headers = {"Authorization": authorization}
    if "*" in [start_time, end_time]: 
        params = {
            "path": path,
            "startTime": start_time,
            "endTime": end_time,
            "maxCount": max_count,
        }
    else: 
        params = {
            "path": path,
            "startTime": start_time_t.isoformat() + "Z",
            "endTime": end_time_t.isoformat() + "Z",
            "maxCount": max_count,
        }
    print(f"req: headers={headers}, params={params}")
    response = requests.get(
        "https://academicpi.osisoft.com/piwebapi/Csv/ElementRecorded", 
        headers=headers,
        params=params,
    )
    print(
        "status=", response.status_code, len(response.text)
    )  # , 'text:', response.text)
    if response.status_code != 200:
        print("resp.text:", response.text)
        if "specified path was not found" in response.text:
            resp.text = f"ERROR: Element path not found, please review your request for typo (element requested: {path})"
            return
        elif response.status_code == 409:
            resp.text = f"ERROR: Bad credentials, please check username/password"
            resp.status_code = 401
            return
        else:
            resp.status_code = response.status_code
            resp.text = response.text
    else:
        resp.status_code = api.status_codes.HTTP_200
        resp.text = response.text
        # resp.headers.pop("content-type", None)
        # print(f"resp.pop={resp.headers}")
        resp.headers.update({"content-type": response.headers["content-type"]})


@api.route("/interpolated")
async def interpolated(req, resp):
    print("Request:", dir(req))
    print("URL:", req.url)
    print("FURL:", req.full_url)
    print("Headers:", req.headers)
    print("Params:", req.params)
    resp.status_code = api.status_codes.HTTP_400
    root = req.params.get("db", "Classroom Data\\Source Data")
    try:
        authorization = req.headers["Authorization"]
        print("Auth:", authorization)
    except KeyError as e:
        if req.params.get("skipAuth", None):
            authorization = "Basic cmVhZGVyMDpPU0lzb2Z0MjAxNw=="
            print("AAuth:", authorization)
        else:
            resp.text = f"ERROR: authorization header missing. Please check https://academic.osisoft.com/mit-dataaccess"
            resp.status_code = api.status_codes.HTTP_401
            return
    try:
        element = req.params["element"]
        start_time = req.params["startTime"]
        end_time = req.params["endTime"]
        interval = req.params.get("interval", "5m")
        validate = req.params.get("validate", None) is not None
    except KeyError as e:
        resp.text = f"ERROR: Missing element/startTime/endTime, please consult {data_access_url}: {e}"
        return
    try:
        start_time_t = dp.parse(start_time)
        end_time_t = dp.parse(end_time)
    except ValueError as e:
        if not "*" in [start_time, end_time]:
            resp.text = f"ERROR: Bad format for startTime and/or endTime parameters, please consult {data_access_url}: {e}"
            return
    try:
        if interval[-1] not in ["h", "m", "s"]:
            raise (Exception("Bad interval suffix, must be 'h', 'm' or 's'"))
        if int(interval[0:-1]) < 0:
            raise (Exception("Interval value must be greater than 0"))
    except Exception as e:
        resp.text = f"ERROR: Bad interval, please consult {data_access_url}: {e}, current interval is {interval}"
        return
    if interval[-1] == "s":
        interval_t = dt.timedelta(seconds=int(interval[0:-1]))
    if interval[-1] == "m":
        interval_t = dt.timedelta(minutes=int(interval[0:-1]))
    if interval[-1] == "h":
        interval_t = dt.timedelta(hours=int(interval[0:-1]))
    if not "*" in [start_time, end_time]:
        number_rows = (end_time_t - start_time_t) / interval_t
        max_rows = int(os.environ.get("MAX_ROWS", "5500"))
        if number_rows > max_rows:
            resp.text = f"ERROR: Combination of startTime/endTime/interval returns more than {os.environ.get('MAX_ROWS', '5500')}, please change (current rows = {int(number_rows)})"
            return
    if validate:
        resp.text = "Request OK"
        resp.status_code = api.status_codes.HTTP_200
        return
    path = "\\\\PIAF-ACAD\\" + root + "\\" + element
    headers = {"Authorization": authorization}
    params = {
        "path": path,
        "startTime": start_time_t.isoformat() + "Z",
        "endTime": end_time_t.isoformat() + "Z",
        "interval": interval,
        "maxCount": max_rows,
    }
    response = requests.get(
        "https://academicpi.osisoft.com/piwebapi/Csv/ElementInterpolated",  # ?path={path}" +
        headers=headers,
        params=params,
    )
    # f"&startTime={start_time_t.isoformat() + 'Z'}" +
    # f"&endTime={end_time_t.isoformat() + 'Z'}" +
    # f"&interval={interval}&maxCount=5500",
    print(
        "status=", response.status_code, len(response.text)
    )  # , 'text:', response.text)
    if response.status_code != 200:
        print("resp.text:", response.text)
        if "specified path was not found" in response.text:
            resp.text = f"ERROR: Element path not found, please review your request for typo (element requested: {path})"
            return
        elif response.status_code == 409:
            resp.text = f"ERROR: Bad credentials, please check username/password"
            resp.status_code = 401
            return
        else:
            resp.status_code = response.status_code
            resp.text = response.text
    else:
        resp.status_code = api.status_codes.HTTP_200
        resp.text = response.text


if __name__ == "__main__":
    api.serve(
        address="0.0.0.0", port=int(os.environ.get("RESPONDER_PORT", "80")), debug=True
    )
