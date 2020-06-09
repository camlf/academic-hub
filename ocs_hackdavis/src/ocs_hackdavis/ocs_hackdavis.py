#
import hashlib
import yaml
from typeguard import typechecked
from typing import List, Union
from ocs_sample_library_preview import OCSClient, SdsError
import pkg_resources
import backoff
from dateutil import parser
import datetime
import logging

resource_package = __name__
resource_path = "/".join((".", "ucd-building-ceeds-v2.yaml"))
data_file = pkg_resources.resource_stream(resource_package, resource_path)
building_ceeds_dvid = yaml.safe_load(data_file)

resource_path = "/".join((".", "ucd-building-ceeds-sds-final.yaml"))
data_file = pkg_resources.resource_stream(resource_package, resource_path)
building_ceeds_sds = yaml.safe_load(data_file)

logging.getLogger('backoff').addHandler(logging.StreamHandler())

@typechecked
def ucdavis_buildings() -> List[str]:
    return list(building_ceeds_dvid.keys())


@typechecked
def ucdavis_ceeds_of(building: str) -> Union[List[str], None]:
    try:
        return list(building_ceeds_dvid[building].keys())
    except KeyError:
        print(f'#warning: "{building}" is not a valid building name')
        return None


# Data View ID
@typechecked
def ucdavis_dataview_id(building: str, ceed: str) -> Union[str, None]:
    try:
        return building_ceeds_dvid[building][ceed]
    except KeyError:
        print(
            f'#warning: Building name "{building}" and/or CEED "{ceed}" are not valid'
        )
        raise KeyError


def ucdavis_streams_of(building: str, ceed: str = "Electricity") -> Union[str, None]:
    try:
        return building_ceeds_sds[building][ceed]
    except KeyError:
        print(
            f'#warning: Building name "{building}" and/or CEED "{ceed}" are not valid'
        )
        raise KeyError


def convert_config_data(value):
    try:
        return float(value)
    except:
        return value


def extract_config_data(d):
    # print(type(d), d)
    dd = eval(d)
    return {k: convert_config_data(dd[k]) for k in dd.keys()}


@typechecked
def ucdavis_building_metadata(
    ocs_client: OCSClient, namespace_id: str, building: str, ceed: str = "Electricity"
):
    try:
        meta_key = building_ceeds_dvid[building][ceed]
    except KeyError:
        print(
            f'#warning: Building name "{building}" and/or CEED "{ceed}" are not valid'
        )
        return None

    streams = ocs_client.Streams.getStreams(namespace_id, query=f"{meta_key}:*")
    if len(streams) >= 1:
        meta = ocs_client.Streams.getMetadata(
            namespace_id, streams[0].Id, f"{meta_key}"
        )
        return extract_config_data(meta)
    else:
        print(
            f"@@@Error: found {len(streams)} for meta key {meta_key} ({building}, {ceed})"
        )
        return None


@backoff.on_exception(backoff.expo, SdsError, max_tries=4, jitter=backoff.full_jitter)
def ocs_stream_interpolated_data(
    ocs_client: OCSClient,
    namespace_id: str,
    stream_id: str,
    start: str,
    end: str,
    interval: int,
    locust_name=None,
    override_limits=False,
):
    start_index = parser.parse(start)
    end_index = parser.parse(end)
    span = end_index - start_index
    if not override_limits:
        if span > datetime.timedelta(days=31):
            print(
                f"# Time difference between start and end time should be <= 31 days, now it is {span}"
            )
            return None
        if interval < 2:
            print(
                f"#error: parsing interval should be at least 2 minutes, it's now {interval}"
            )
            return None
    count = int((span.days * 24 * 60 + (span.seconds // 60)) / interval) + 1
    # print(f"count={count}")
    if locust_name:
        return ocs_client.Streams.getRangeValuesInterpolated(
            namespace_id,
            stream_id,
            None,
            start_index.isoformat(),
            end_index.isoformat(),
            count=count,
            locust_name=locust_name,
        )
    else:
        return ocs_client.Streams.getRangeValuesInterpolated(
            namespace_id,
            stream_id,
            None,
            start_index.isoformat(),
            end_index.isoformat(),
            count=count,
        )


@typechecked
def ucdavis_outside_temperature(
    ocs_client: OCSClient, namespace_id: str, start: str, end: str, interval: int
):
    return ocs_stream_interpolated_data(
        ocs_client, namespace_id, "PI_uni-pida-vm0_2603", start, end, interval
    )
