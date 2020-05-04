#
from .util import timer
import configparser
from dateutil.parser import parse
from datetime import datetime, timedelta
import requests
import io
import json
import os
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

    def __init__(self):
        config_file = os.environ.get("OCS_HUB_CONFIG", None)
        if config_file:
            config = configparser.ConfigParser()
            print(f"> configuration file: {config_file}")
            config.read(config_file)
            super().__init__(
                config.get("Access", "ApiVersion"),
                config.get("Access", "Tenant"),
                config.get("Access", "Resource"),
                config.get("Credentials", "ClientId"),
                config.get("Credentials", "ClientSecret"),
            )
        else:
            super().__init__("v1", "65292b6c-ec16-414a-b583-ce7ae04046d4", "https://dat-b.osisoft.com", "422e6002-9c5a-4651-b986-c7295bcf376c")


    @typechecked
    def dataview_definition(
        self, namespace_id: str, dataview_id: str, version: str = ""
    ):
        if version == "":
            column_key = (
                dataview_id[
                    dataview_id.find("HubDV_") + 6 : dataview_id.find("_fv")
                ].lower()
                + "_column"
            )
        else:
            return self.dataview_definition_v2(namespace_id, dataview_id, version)
        df = pd.DataFrame(columns=("OCS_StreamName", "DV_Column", "Value_Type"))
        i = 0
        for query in ["Asset_value", "Asset_digital"]:
            data_items = self.DataViews.getResolvedDataItems(
                namespace_id, dataview_id, query
            )
            for item in data_items.Items:
                # print(it.Name, it.Metadata["value_path"], it.Metadata[meta_key])
                df.loc[i] = [
                    item.Name,
                    item.Metadata[column_key],
                    f"Category"
                    if query == "Asset_digital"
                    else ("String" if item.TypeId == "PI-String" else "Float"),
                ]
                i += 1
        return df


    @typechecked
    def dataview_definition_v2(
        self, namespace_id: str, dataview_id: str, version: str
    ):
        df = pd.DataFrame(columns=("OCS_StreamName", "DV_Column", "Value_Type"))
        i = 0
        data_items = super().DataViews.getResolvedDataItems(
            namespace_id, dataview_id, "Asset_value"
        )
        for item in data_items.Items:
            df.loc[i] = [
                item.Name,
                item.Metadata["column_name"],
                f"Category"
                if item.TypeId == "PI-Digital"
                else ("String" if item.TypeId == "PI-String" else "Float"),
            ]
            i += 1
        return df        


    @typechecked
    def fermenter_dataview_ids(
        self,
        namespace_id: str,
        filter: str = "",
        fv_id: int = 0,
        first_fv: int = 0,
        last_fv: int = 0,
        version: str = "",
    ):
        dvs = super().DataViews.getDataViews(namespace_id, count=1000)
        dv_ids = [dv.Id for dv in dvs if f"hub{version}dv" in dv.Id.lower()]
        if len(filter) > 0:
            dv_ids = [dv_id for dv_id in dv_ids if filter.lower() in dv_id.lower()]
        if fv_id > 0:
            dv_ids = [dv_id for dv_id in dv_ids if f"fv{fv_id:02}" in dv_id]
        elif first_fv > 0 and last_fv > 0:
            fv_ids = [f"fv{fv_id:02}" for fv_id in range(first_fv, last_fv + 1)]
            dv_ids = [dv_id for dv_id in dv_ids if dv_id[-4:] in fv_ids]
        return dv_ids

    def __process_digital_states(self, df):
        ds_columns = [col for col in list(df.columns) if col[-4:] == "__ds"]
        if len(ds_columns) > 0:
            for ds_col in ds_columns:
                val_col = ds_col[:-4]
                index = df[val_col].index[df[val_col].apply(np.isnan)]
                df.loc[index, [ds_col]] = ""
            df = df.drop(columns=[ds_col[:-4] for ds_col in ds_columns])
            df = df.rename(columns={ds_col:ds_col[:-4] for ds_col in ds_columns})
        return df 

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
        next_page,
    ):
        return super().DataViews.getDataInterpolated(
            namespace_id,
            dataview_id,
            count=count,
            form=form,
            startIndex=start_index,
            endIndex=end_index,
            interval=interval,
            url=next_page,
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
        next_page = None
        while True:
            csv, next_page, _ = self.__get_data_interpolated(
                namespace_id=namespace_id,
                dataview_id=dataview_id,
                count=count,
                form="csvh",
                start_index=start_index,
                end_index=end_index,
                interval=interval,
                next_page=next_page,
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
            if next_page is None:
                if count != MAX_COUNT:
                    print()
                break
            print("+", end="", flush=True)

        if add_dv_column:
            df["Dataview_ID"] = pd.Series([dataview_id] * len(df.index), index=df.index)
        return self.__process_digital_states(df)

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
        count: int = MAX_COUNT,
        workers: int = 3,
        verbose: bool = False,
        raw: bool = False,
        skip_sort: bool = False,
        debug: bool = False,
    ):

        df = pd.DataFrame()
        dv_ids_counts = [(dv_id, count) for dv_id in dv_ids]
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
                            f.cancel()
                            # print(f"[cancelled? {t}]", end="", flush=True)
                        except Exception:
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