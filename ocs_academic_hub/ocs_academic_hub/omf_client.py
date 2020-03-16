import requests
from typeguard import typechecked
import pandas as pd
from dateutil import parser
from dateutil.tz import *

requests.packages.urllib3.disable_warnings()

# OMF_ENDPOINT = "http://httpbin.org/post"
OMF_ENDPOINT = "https://academicpi.azure-api.net/csv-ingress/messages"
API_KEY = "dummy"

# Ref for OMF approach: https://pisquare.osisoft.com/people/gmoffett/blog/2018/11/06/osisoft-message-format-what-to-type


def omf_type(new_type):
    return (
        f"stream-{new_type}",
        {
            "id": f"stream-{new_type}",
            "description": "Timestamp and real-time value",
            "type": "object",
            "classification": "dynamic",
            "properties": {
                "IndexedDateTime": {
                    "type": "string",
                    "format": "date-time",
                    "isindex": True,
                },
                "value": {"type": f"{new_type}"},
            },
        },
    )


omf_number_typeid, omf_number_type = omf_type("number")


def container_id(asset, name):
    return f"{asset}.{name}"


def omf_container(asset, name, typeid):
    return {"id": container_id(asset, name), "typeid": f"{typeid}"}


def omf_data(asset, name, timestamp, value):
    ts = parser.parse(timestamp).astimezone(UTC)
    return {
        "containerid": container_id(asset, name),
        "values": [{"IndexedDateTime": f"{ts.isoformat()}", "value": value}],
    }


def omf_headers(message_type, api_key=API_KEY, producer_token="-not-set-"):
    # message_type is "type", "container" or "data"
    return {
        "producertoken": f"{producer_token}",
        "messagetype": f"{message_type}",
        "messageformat": "json",
        "omfversion": "1.0",
        "Ocp-Apim-Subscription-Key": api_key,
    }


def send_omf_message(
    message_type, data, api_key, producer_token, debug=False, printg=print
):
    if not isinstance(data, list):
        data = [data]

    if debug:
        printg(
            f"\nDBG>>> {OMF_ENDPOINT} {omf_headers(message_type, api_key, producer_token)} {data}\n"
        )
        return

    return requests.post(
        OMF_ENDPOINT,
        headers=omf_headers(message_type, api_key, producer_token),
        json=data,
    )


def normalize_for_omf(name):
    return (
        name.strip()
        .replace('"', "")
        .replace("(", "")
        .replace(")", "")
        .replace(".", "_")
        .replace(" ", "_")
        .replace("/", "_")
    )


class OMFClient:
    @typechecked
    def __init__(self, api_key: str, printg=print, row_batch_size=50):
        self._api_key = api_key
        self._init_ok = False
        self._row_batch_size = row_batch_size

        r = requests.get(
            f"https://data.academic.osisoft.com/omflistener/getconfig",
            params=dict(token=f"{api_key}-producertoken"),
            verify=False,
        )
        if r.status_code == 200:
            self._producer_token = r.text
        else:
            extra_message = (
                f" (bad API key: {api_key})" if r.status_code == 400 else ""
            )
            printg(
                f"@@ error from hub configuration server{extra_message}, please correct and retry (error code {r.status_code})"
            )
            return
        if "Unknown" in self._producer_token:
            printg("@@ API key {api_key} is not registered, please correct and retry")
            return
        r = send_omf_message(
            "type",
            omf_number_type,
            api_key,
            self._producer_token,
            debug=False,
            printg=printg,
        )
        if r.status_code != 200:
            if r.status_code == 401:
                printg(f"@@ please correct API key: current key is {api_key}\n")
            else:
                printg(
                    f"\n\n !#!# error with type definition: status={r.status_code}\n\n >>> {r.text}\n\n"
                )
            return
        else:
            printg(">> [OMF type definition OK]\n")
        self._init_ok = True

    def is_ok(self):
        return self._init_ok

    def update_tags(
        self, df, asset_name: str, printg=print, info_only=False, debug=False
    ):
        if not self._init_ok:
            printg(
                "@@ error: OMFClient not correcly initialized, please recreate object"
            )
            return
        if not isinstance(df, pd.core.frame.DataFrame):
            printg("@@ error: argument should be a Pandas dataframe")
            return
        first_column = [c for c in df.columns][0]
        if first_column != "Timestamp":
            printg(
                f"@@ error: first column of dataframe should be 'Timestamp', found {first_column}"
            )
            return
        fixed_column_names = [normalize_for_omf(column) for column in list(df.columns)]
        # if info_only:
        #     printg(f"df.columns={list(df.columns)}, fixed_columns={fixed_column_names}")
        df.columns = fixed_column_names
        containers = [
            omf_container(normalize_for_omf(asset_name), sensor, omf_number_typeid)
            for sensor in list(df.columns)[1:]
        ]
        # if info_only:
        #    printg(f"containers={containers}")
        # check column types
        for c in list(df.columns)[1:]:
            if str(df[c].dtype) not in ["float64", "int64"]:
                printg(
                    f'@@ error: column name "{c}" has not type float64 or int64 (current type: {str(df[c].dtype)})'
                )
                return
        tags = [f"{self._producer_token}.{c['id']}" for c in containers]
        printg(f">> new tag(s): {tags}")
        printg(f">> from {df.iloc[0].Timestamp} to {df.iloc[len(df)-1].Timestamp}")
        if info_only:
            printg(f"\n>> @@ info only requested, stopping (NO UPLOAD)")
            return
        r = send_omf_message(
            "container", containers, self._api_key, self._producer_token, debug, printg
        )
        if r.status_code != 200:
            printg(
                f"@@ error with column definition: status={r.status_code}\n\n >>> {r.text}\n"
            )
            return
        else:
            printg(">> [column definitions OK]")

        count = 0
        printg(">> processing row: ", end="")
        row_batch_data = []
        try:
            for r in df.itertuples():
                row_dict = r._asdict()
                t = parser.parse(str(r.Timestamp))
                # print(f"## {t.astimezone(UTC).isoformat()} \n")

                row_omf_data = [
                    omf_data(
                        self._equipment,
                        sensor,
                        t.astimezone(UTC).isoformat(),
                        row_dict[sensor],
                    )
                    for sensor in list(df.columns)[1:]
                ]
                # out.append_stdout(f"row omf data: {row_omf_data}\n")
                count += 1
                row_batch_data.extend(row_omf_data)
                if count % self._row_batch_size == 0:
                    printg(f"[{count}]", end="")
                    r = send_omf_message(
                        "data",
                        row_batch_data,
                        self._api_key,
                        self._producer_token,
                        debug,
                        printg,
                    )
                    row_batch_data = []
                    if r:
                        if r.status_code != 200:
                            printg(
                                f"\n\n@@ error with row #{count}: status={r.status_code}\n\n >>> {r.text}\n\n"
                            )
            printg(f"[last rows {len(row_batch_data)}]")
            if len(row_batch_data) > 0:
                r = send_omf_message(
                    "data",
                    row_batch_data,
                    self._api_key,
                    self._producer_token,
                    debug,
                    printg,
                )
                if r.status_code != 200:
                    printg(
                        f"\n\n !#!# error with last rows #{count}: status={r.status_code}\n\n >>> {r.text}\n\n"
                    )
                    return

            printg(
                f"\nLoading-Extract-Transfer to Hub done, status OK, #rows = {count}\n"
            )

        except Exception as e:
            printg(
                f"\n\n!!! Error processing CSV, exception={e}, contact hubsupport@osisoft.com"
            )
        finally:
            return