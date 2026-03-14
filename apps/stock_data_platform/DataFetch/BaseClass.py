from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from apps.stock_data_platform.common.timing import timer

from .client import ClientConfig, TuShareClient


class BaseDataFetch(ABC):
    """
    Base class for data fetchers.

    Design goals:
    - `read_data()` SHOULD return the data (e.g., a DataFrame)
    - Keep backward compatibility: if subclasses still set `self.data`, it works
    - Centralize cross-cutting concerns (retry/cache/rate-limit) in `TuShareClient`
    """

    def __init__(self, client: Optional[TuShareClient] = None, client_config: Optional[ClientConfig] = None):
        if client is None:
            client = TuShareClient(config=client_config)
        self.client = client
        # Compatibility: older code calls `self.pro.xxx(...)`
        self.pro = client.pro
        self.data: Any = None

    @abstractmethod
    def read_data(self, **kwargs: Any) -> Any:
        """
        Implementations can either:
        - return the fetched object (recommended), OR
        - set `self.data` and return None (legacy style)
        """

    def fetch_data(self, name: str = "", **kwargs: Any) -> Any:
        """
        Backward compatible entry:
        - returns fetched data
        - also stores to `self.data`
        """
        label = f"获取: {name}" if name else "获取数据"
        with timer(label):
            result = self.read_data(**kwargs)
            print(f"fields: {self.fields}")
        if result is not None:
            self.data = result
        return self.data

    def fetch(self, **kwargs: Any) -> Any:
        """New-style alias without a label param."""

        return self.fetch_data(**kwargs)

    def summary_data(self) -> None:
        if self.data is not None:
            shape = getattr(self.data, "shape", None)
            cols = getattr(self.data, "columns", None)
            if shape is not None:
                print("Shape: " + str(shape))
            if cols is not None:
                print("Cols: " + str(cols))
