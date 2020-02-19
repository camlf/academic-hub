#
from ocs_sample_library_preview import DataView
from .ocs_academic_hub import HubClient
from typeguard import typechecked
import collections
import json

TIMESTAMP_COLUMN = [
    {
        "Name": "Timestamp",
        "MappingRule": {"PropertyPaths": ["Timestamp"]},
        "IsKey": True,
        "DataType": "DateTime",
    }
]


class HubDataview:
    @typechecked
    def __init__(self, hub_client: HubClient):
        self._hub_client = hub_client

    def hub_dataview(
        self,
        namespace_id,
        dv_id,
        asset_id,
        column_tag,
        start_index,
        end_index,
        interval="00:05:00",
        description="-none-",
        verbose=False,
        skip_ds=False,
    ):
        dv_def = self._generic_dataview_def(
            namespace_id,
            dv_id,
            asset_id,
            column_tag,
            start_index,
            end_index,
            interval,
            description,
            skip_ds,
        )
        if verbose:
            print(f"Raw Dataview ID: {dv_id}\n", json.dumps(dv_def, indent=4))
        dataview = DataView.fromJson(dv_def)
        if verbose:
            print(f"Get Dataview ID: {dv_id}\n", json.dumps(dataview.toDictionary(), indent=4))
        return dataview

    def __dv_generic_column_mappings(
        self, namespace_id, asset_id, column_tag, preview=False, skip_ds=False
    ):
        # Get all the streams for the selected asset and columns identified with a tag
        streams = self._hub_client.Streams.getStreams(
            namespace_id, f"asset_id:{asset_id} AND {column_tag}_rank:*"
        )
        asset_streams = {}
        # For each stream, extract all metadata. To be filtered elsewhere.
        for stream in streams:
            column_meta = self._hub_client.Streams.getMetadata(
                namespace_id, stream.Id, ""
            )
            asset_streams[stream.Name] = column_meta
        columns_d = {}
        # Now for each stream, gather the necessary data for column view mapping
        for stream_name in asset_streams:
            column_rank = asset_streams[stream_name][f"{column_tag}_rank"]
            column_name = asset_streams[stream_name][f"{column_tag}_column"]
            value_path = asset_streams[stream_name]["value_path"]
            columns_d[int(column_rank)] = (stream_name, column_name, value_path)
            if not skip_ds and value_path == "Value":
                columns_d[int(column_rank) + len(asset_streams)] = (
                    stream_name,
                    column_name + "__ds",
                    "DigitalStateName",
                )
        if preview:
            return columns_d
        columns_ord = collections.OrderedDict(sorted(columns_d.items()))
        columns = []
        # Generate the dataview column mapping definitions, by ranking order so that column order is the same accross dataviews
        for k, (stream_name, column_name, value_path) in columns_ord.items():
            columns.append(self.__dv_column_def(column_name, stream_name, value_path))
        # Return data view column definitions, including the index (always timestamp for Bifrost data)
        return {"Columns": TIMESTAMP_COLUMN + columns}

    def __dv_column_def(self, column_name, stream_name, value_path):
        return {
            "Name": column_name,
            "MappingRule": {
                "PropertyPaths": [value_path],
                "ItemIdentifier": {
                    "Resource": "Streams",
                    "Field": "Name",
                    "Value": stream_name,
                    "Function": "Equals",
                },
            },
        }

    def _generic_dataview_def(
        self,
        namespace_id,
        dv_id,
        asset_id,
        column_tag,
        start_index,
        end_index,
        interval,
        description="-none-",
        skip_ds=False,
    ):
        return {
            "Id": dv_id,
            "Name": dv_id,
            "Description": description,
            "Queries": [{"Id": "Asset", "Query": f"name:*{asset_id}*"}],
            "GroupRules": [],
            "Mappings": self.__dv_generic_column_mappings(
                namespace_id, asset_id, column_tag, skip_ds=skip_ds
            ),
            "IndexDataType": "DateTime",
            "IndexConfig": {
                "StartIndex": start_index,
                "EndIndex": end_index,
                "Mode": "Interpolated",
                "Interval": interval,
            },
        }

        def preview_dataview(self, namespace_id, asset_id, column_tag, show_ds=False):
            asset_streams = self.__dv_generic_column_mappings(
                namespace_id, asset_id, column_tag, preview=True
            )
            df = pd.DataFrame(columns=("StreamName", "Column", "Path"))
            for k in asset_streams:
                stream, column, path = asset_streams[k]
                if not show_ds and "__ds" in column:
                    continue
                df.loc[k] = [stream, column, path]
            return df.sort_index()
