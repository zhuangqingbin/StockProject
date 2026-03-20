from __future__ import annotations

from collections.abc import Mapping

import pandas as pd

from apps.data_hub.data_pipeline_ts.execution.context import ExecutionContext


def _ensure_dataframe(value: object) -> pd.DataFrame:
    if value is None:
        return pd.DataFrame()
    if isinstance(value, pd.DataFrame):
        return value
    return pd.DataFrame(value)


def _render_value(value: object, context: ExecutionContext) -> object:
    if not isinstance(value, str):
        return value

    rendered = value
    for key, replacement in context.variables().items():
        rendered = rendered.replace(f"{{{key}}}", replacement)
    return context.render_value(rendered)


def _render_params(params: Mapping[str, object], context: ExecutionContext) -> dict[str, object]:
    return {key: _render_value(value, context) for key, value in params.items()}
