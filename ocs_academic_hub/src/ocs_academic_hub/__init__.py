from importlib_metadata import version

from .ocs_academic_hub import HubClient
from .util import timer

__version__ = version("ocs_academic_hub")


__all__ = ["HubClient", "timer", "__version__"]
