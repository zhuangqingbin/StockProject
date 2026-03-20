from __future__ import annotations

from typing import Any

from apps.data_hub.data_pipeline_ak.provider.client import AkShareClient
from apps.data_hub.data_pipeline_ts.fetchers.base import (
    BaseFetcher as PipelineBaseFetcher,
    ColumnDef,
    TableSchema,
)


class BaseFetcher(PipelineBaseFetcher):
    def __init__(self, client: Any | None = None):
        resolved_client = client or AkShareClient().module
        super().__init__(client=resolved_client)
