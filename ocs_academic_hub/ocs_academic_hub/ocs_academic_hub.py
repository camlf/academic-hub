#
from .util import timer
import configparser
from dateutil.parser import parse
from datetime import datetime, timedelta
import requests
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import io
import json
import os
import numpy as np
import pandas as pd
import concurrent.futures
import traceback
from typeguard import typechecked
from typing import List, Union
import pkg_resources
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


from ocs_sample_library_preview import OCSClient, DataView, SdsError

MAX_COUNT = 250 * 1000
DESCHUTES_DB = "Deschutes-v1"
DESCHUTES_NAMESPACE = "fermenter_vessels"
UCDAVIS_FACILITIES_DB = "UCDavis.Facilities"
UCDAVIS_FACILITIES_NAMESPACE = "UC__Davis"

hub_db_namespaces = {
    DESCHUTES_DB: DESCHUTES_NAMESPACE,
    UCDAVIS_FACILITIES_DB: UCDAVIS_FACILITIES_NAMESPACE,
}

ocstype2hub = {
    "PI-Digital": "Category",
    "PI-String": "String",
    "PI-Timestamp": "Timestamp",
    "PI-Int16": "Integer",
    "PI-Int32": "Integer",
}

resource_package = __name__
resource_path = "/".join((".", "hub_datasets.json"))
default_hub_data = pkg_resources.resource_filename(resource_package, resource_path)


def initialize_hub_data(data_file):
    with open(data_file) as f:
        gqlh = json.loads(f.read())
    db_index = {}
    for i, database in enumerate(gqlh["Database"]):
        db_index[database["asset_db"]] = i
        hub_db_namespaces[database["name"]] = database["namespace"]
    return gqlh, gqlh["Database"][0]["asset_db"], db_index


class HubClient(OCSClient):
    def __init__(self, hub_data="hub_datasets.json"):
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
            super().__init__(
                "v1",
                "65292b6c-ec16-414a-b583-ce7ae04046d4",
                "https://dat-b.osisoft.com",
                "422e6002-9c5a-4651-b986-c7295bcf376c",
            )
        data_file = hub_data if os.path.isfile(hub_data) else default_hub_data
        if data_file != default_hub_data:
            print(f"@ Hub data file: {data_file}")
        self.__gqlh, self.__current_db, self.__db_index = initialize_hub_data(data_file)
        self.__current_db_index = 0

    @typechecked
    def datasets(self) -> List[str]:
        return list(hub_db_namespaces.keys())

    @typechecked
    def current_dataset(self) -> str:
        return self.__gqlh["Database"][self.__current_db_index]["name"]

    @typechecked
    def namespace_of(self, dataset: str):
        try:
            return hub_db_namespaces[dataset]
        except KeyError:
            print(f"@@ Dataset {dataset} does not exist, please check hub.datasets()")

    @typechecked
    def assets(self, filter: str = "") -> List[str]:
        assets = [
            (i["name"])
            for i in self.__gqlh["Database"][self.__db_index[self.__current_db]][
                "asset_with_dv"
            ]
        ]
        return sorted([i for i in set(assets) if filter.lower() in i.lower()])

    @typechecked
    def asset_dataviews(
        self, filter: str = "", asset: str = "", single_asset=True
    ) -> Union[None, List[str]]:
        if len(asset) > 0:
            if asset.lower() not in [i.lower() for i in self.assets()]:
                print(
                    f"@@ error: asset {asset} not in dataset asset list, check hub.assets()"
                )
                return
        if single_asset:
            len_test = lambda l: len(l) == 1
        else:
            len_test = lambda l: len(l) > 1
        if asset == "":
            asset_test = lambda x, y: True
        else:
            asset_test = lambda asset, asset_list: asset.lower() in [
                i.lower() for i in asset_list
            ]

        dataviews = []
        for j in self.__gqlh["Database"][self.__db_index[self.__current_db]][
            "asset_with_dv"
        ]:
            dataviews.extend(j["has_dataview"])

        return sorted(
            list(
                set(
                    [
                        i["id"]
                        for i in dataviews
                        if (
                            filter.lower() in i["id"]
                            or filter.lower() in i["description"].lower()
                        )
                        and asset_test(asset, i["asset_id"])
                        and len_test(i["asset_id"])
                    ]
                )
            )
        )

    @typechecked
    def dataview_definition_v2(self, namespace_id: str, dataview_id: str, version: str):
        df = pd.DataFrame(
            columns=(
                "Asset_Id",
                "OCS_StreamName",
                "DV_Column",
                "Value_Type",
                "EngUnits",
            )
        )
        data_items = super().DataViews.getResolvedDataItems(
            namespace_id, dataview_id, "Asset_value?count=1000"
        )
        for i, item in enumerate(data_items.Items):
            df.loc[i] = [
                item.Metadata["asset_id"],
                item.Name,
                item.Metadata["column_name"],
                ocstype2hub.get(item.TypeId, "Float"),
                item.Metadata.get("engunits", "-n/a-"),
            ]
        return df

    def __process_digital_states(self, df):
        ds_columns = [col for col in list(df.columns) if col[-4:] == "__ds"]
        if len(ds_columns) > 0:
            for ds_col in ds_columns:
                val_col = ds_col[:-4]
                index = df[val_col].index[df[val_col].apply(np.isnan)]
                df.loc[index, [ds_col]] = ""
            df = df.drop(columns=[ds_col[:-4] for ds_col in ds_columns])
            df = df.rename(columns={ds_col: ds_col[:-4] for ds_col in ds_columns})
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
        count_arg = {} if count is None else {"count": count}
        return super().DataViews.getDataInterpolated(
            namespace_id,
            dataview_id,
            # count=count,
            form=form,
            startIndex=start_index,
            endIndex=end_index,
            interval=interval,
            url=next_page,
            **count_arg,
        )

    @timer
    @typechecked
    def dataview_interpolated_pd(
        self,
        namespace_id: str,
        dataview_id: str,
        start_index: str,
        end_index: str,
        interval: str,
        count: int = None,
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
            summary = f"<@dataview_interpolated_pd/{dataview_id}/{start_index}/{end_index}/{interval}  t={datetime.now().isoformat()}"
            print(summary)
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
            df = df.append(
                pd.read_csv(io.StringIO(csv), parse_dates=["Timestamp"]),
                ignore_index=True,
            )
            if next_page is None:
                print()
                break
            print("+", end="", flush=True)

        if add_dv_column:
            df["Dataview_ID"] = pd.Series([dataview_id] * len(df.index), index=df.index)
        return self.__process_digital_states(df)

    # EXPERIMENTAL

    def refresh_datasets(
        self, hub_data="hub_datasets.json", additional_status="production"
    ):
        sample_transport = RequestsHTTPTransport(
            url="https://data.academic.osisoft.com/graphql", verify=False, retries=3
        )
        client = Client(transport=sample_transport, fetch_schema_from_transport=True)
        db_query = gql(
            """
query Database($status: String) {
  Database(filter: { OR: [{ status: "production" }, { status: $status }] }) {
    name
    asset_db
    description
    informationURL
    status
    namespace
    version
    id
    asset_with_dv(orderBy: name_asc) {
      name
      has_dataview(filter: { ocs_sync: true }) {
        name
        description
        id
        asset_id
        columns
      }
    }
  }
}
            """
        )
        db = client.execute(db_query, variable_values={"status": additional_status})
        with open(hub_data, "w") as f:
            f.write(json.dumps(db, indent=2))
        print(f"@ Hub data file: {hub_data}")
        self.__gqlh, self.__current_db, self.__db_index = initialize_hub_data(hub_data)
        print(f"@ Current dataset: {self.current_dataset()}")

    # DEPRECATED

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
                try:
                    df.loc[i] = [
                        item.Name,
                        item.Metadata[column_key],
                        f"Category"
                        if query == "Asset_digital"
                        else ("String" if item.TypeId == "PI-String" else "Float"),
                    ]
                    i += 1
                except KeyError:
                    return self.dataview_definition_v2(
                        namespace_id, dataview_id, version
                    )
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
            print(summary)
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
        df = df.sort_values(["Dataview_ID", "Timestamp"]).reset_index(drop=True)
        return df
