from __future__ import annotations

from typing import Any


class AkShareClient:
    def __init__(self, module: Any = None):
        if module is not None:
            self.module = module
            return

        import akshare as ak

        self.module = ak
