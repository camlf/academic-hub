#
from .util import timer
from dateutil.parser import parse
from datetime import datetime, timedelta
import requests
import io
import json
import numpy as np
import pandas as pd
import concurrent.futures
import traceback
from typeguard import typechecked
from typing import List


try:
    from ddtrace import tracer
except ImportError:
    from .dddummy import tracer

from ocs_sample_library_preview import OCSClient, DataView, SdsError

MAX_COUNT = 250 * 1000


class HubClient(OCSClient):
    def request(self, method, url, params=None, headers=None, **kwargs):
        if url[:4] != "http":
            url = self.uri + url
        if not headers:
            headers = self._OCSClient__baseClient.sdsHeaders()
        return requests.request(method, url, params=params, headers=headers, **kwargs)

    @typechecked
    def dataview_definition(self, namespace_id: str, dataview_id: str):
        meta_key = (
            dataview_id[
                dataview_id.find("HubDV_") + 6 : dataview_id.find("_fv")
            ].lower()
            + "_column"
        )
        df = pd.DataFrame(columns=("OCS_StreamName", "DV_Column", "Value_Type"))
        i = 0
        for query in ["Asset_value", "Asset_digital"]:
            url = f"/api/v1-preview/Tenants/{self._OCSClient__baseClient.tenant}/Namespaces/{namespace_id}/DataViews/{dataview_id}/Resolved/DataItems/{query}"
            response = self.request("get", url)
            if response.status_code == 200:
                for stream in response.json()["Items"]:
                    df.loc[i] = [
                        stream["Name"],
                        stream["Metadata"][meta_key],
                        "Float" if query == "Asset_value" else "Category",
                    ]
                    i += 1
            else:
                print(
                    f"@@@@ Error getting definition of data view ID: {dataview_id}, (http code: {response.status_code})"
                )
                break
        return df

    @typechecked
    def fermenter_dataview_ids(
        self,
        namespace_id: str,
        filter: str = "",
        fv_id: int = 0,
        first_fv: int = 0,
        last_fv: int = 0,
    ):
        dvs = self._OCSClient__DataViews.getDataViews(namespace_id, count=1000)
        dv_ids = [dv.Id for dv in dvs if "HubDV" in dv.Id]
        if len(filter) > 0:
            dv_ids = [dv_id for dv_id in dv_ids if filter.lower() in dv_id.lower()]
        if fv_id > 0:
            dv_ids = [dv_id for dv_id in dv_ids if f"fv{fv_id:02}" in dv_id]
        elif first_fv > 0 and last_fv > 0:
            fv_ids = [f"fv{fv_id:02}" for fv_id in range(first_fv, last_fv + 1)]
            dv_ids = [dv_id for dv_id in dv_ids if dv_id[-4:] in fv_ids]
        return dv_ids

    @timer
    def __get_data_interpolated(
        self,
        namespace_id,
        dataview_id,
        form,
        start_index,
        end_index,
        interval,
        count,
        token,
    ):
        return self._OCSClient__DataViews.getDataInterpolated(
            namespace_id,
            dataview_id,
            form=form,
            startIndex=start_index,
            endIndex=end_index,
            interval=interval,
            count=count,
            continuationToken=token,
        )

    @tracer.wrap("dataview_interpolated_pd", "dataview")
    @timer
    @typechecked
    def dataview_interpolated_pd(
        self,
        namespace_id: str,
        dataview_id: str,
        start_index: str,
        end_index: str,
        interval: str,
        count: int = MAX_COUNT,
        add_dv_column: bool = False,
        raw: bool = False,
        verbose: bool = False,
    ):
        df = pd.DataFrame()
        try:
            datetime.strptime(interval, "%H:%M:%S")
        except ValueError as e:
            print(f"@Error: interval has invalid format: {e}")
            return df
        try:
            parse(end_index)
            parse(start_index)
        except ValueError as e:
            print(f"@Error: start_index and/or end_index has invalid format: {e}")
            return df
        if verbose:
            span = tracer.current_span()
            if span:
                summary = f"<@dataview_interpolated_pd/{dataview_id}/{start_index}/{end_index}/{interval}  t={datetime.now().isoformat()}"
                span.set_tag("summary", summary)
        token = None
        while True:
            csv, token = self.__get_data_interpolated(
                namespace_id,
                dataview_id,
                "csvh",
                start_index,
                end_index,
                interval,
                count,
                token,
                no_timer=not verbose,
            )
            with tracer.trace("append_df") as span:
                span.service = "append"
                df = df.append(
                    pd.read_csv(
                        io.StringIO(csv[csv.find("Time") :]), parse_dates=["Timestamp"]
                    ),
                    ignore_index=True,
                )
            if token is None:
                break
            else:
                print("+", end="", flush=True)
        with tracer.trace("merge_df") as span:
            span.service = "merge"
            cols = [c for c in df.columns if c + "__ds" in df.columns]
            if not raw:
                for col in cols:
                    col_ds = col + "__ds"
                    mask = df[col].isnull()
                    ds_num = np.sum(mask)
                    if ds_num > 0:
                        df[col] = df[col].astype("object")
                        for i in np.nditer(np.where(mask)):
                            try:
                                df.at[int(i), col] = df.at[int(i), col_ds]
                            except KeyError:
                                print(f"KeyError: {i}, col:{col}")
                                assert False, "Should not happen"
                df.drop([c + "__ds" for c in cols], axis=1, inplace=True)
            if add_dv_column:
                df["Dataview_ID"] = pd.Series(
                    [dataview_id] * len(df.index), index=df.index
                )
        return df

    @tracer.wrap("dataviews_interpolated_pd", "dataviews")
    @timer
    @typechecked
    def dataviews_interpolated_pd(
        self,
        namespace_id: str,
        dv_ids: List[str],
        start_index: str,
        end_index: str,
        interval: str,
        workers: int = 2,
        verbose: bool = False,
        raw: bool = False,
        skip_sort: bool = False,
        debug: bool = False,
    ):

        df = pd.DataFrame()
        dv_ids_counts = [(dv_id, MAX_COUNT) for dv_id in dv_ids]
        if verbose:
            summary = f"<@dataviews_interpolated_pd/{start_index}/{end_index}/{interval}/w{workers}/raw={raw} t={datetime.now().isoformat()}"
            dvs_info = f"dv_ids={dv_ids_counts}"
            print(summary)
            print(dvs_info)
            current_span = tracer.current_span()
            if current_span:
                current_span.set_tag("summary", summary)
                current_span.set_tag("dvs_info", dvs_info)
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_dv = {
                executor.submit(
                    self.dataview_interpolated_pd,
                    namespace_id,
                    dv_id,
                    start_index=start_index,
                    end_index=end_index,
                    interval=interval,
                    add_dv_column=True,
                    raw=raw,
                    count=count,
                    verbose=debug,
                    no_timer=not verbose,
                ): (dv_id, count)
                for (dv_id, count) in dv_ids_counts
            }
            for future in concurrent.futures.as_completed(future_to_dv):
                dv_id, count = future_to_dv[future]
                try:
                    dv_df = future.result()
                    with tracer.trace("append_df") as span:
                        span.service = "append"
                        df = df.append(dv_df, sort=False)
                except Exception as exc:
                    tb = traceback.format_exc()
                    print(
                        f"{dv_id}/{count} generated an exception: {exc} - if 408, increase interval\n{tb}"
                    )
                    for f, _ in future_to_dv.items():
                        try:
                            t = f.cancel()
                            # print(f"[cancelled? {t}]", end="", flush=True)
                        except Exception as e:
                            # print(f"[oops] {e} ", end="", flush=True)
                            pass
                    executor.shutdown(wait=False)
                    raise exc
                    # return pd.DataFrame()
                else:
                    # print(f"{dv_id}/{count} dataframe has {len(df)} lines")
                    pass
        if len(df) == 0 or skip_sort:
            return df
        with tracer.trace("sort_df") as span:
            span.service = "sort"
            df = df.sort_values(["Dataview_ID", "Timestamp"]).reset_index(drop=True)
        if verbose:
            buf = io.StringIO()
            df.info(max_cols=3, buf=buf)
            if current_span:
                current_span.set_tag("df_info", buf.getvalue())
        return df