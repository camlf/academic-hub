#
__version__ = "0.67.0"


def version():
    return __version__


from .ocs_academic_hub import HubClient
from .hub_dataview import HubDataview
from .omf_client import OMFClient

from .util import timer, get_last_runtime, debug_requests_on, debug_requests_off

try:
    from ddtrace import tracer
except ImportError:
    from .dddummy import tracer 
