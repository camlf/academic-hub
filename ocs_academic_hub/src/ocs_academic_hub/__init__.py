from .ocs_academic_hub import HubClient
from .util import timer

import importlib.metadata
__version__ = importlib.metadata.version('ocs_academic_hub')

__all__ = ["HubClient", "timer", "__version__"]
