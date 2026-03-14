from apps.stock_data_platform import DataFetch as _impl
from apps.stock_data_platform.DataFetch import *  # noqa: F401,F403

__all__ = getattr(_impl, "__all__", [])
__path__ = _impl.__path__
