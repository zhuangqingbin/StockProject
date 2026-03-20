from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any

import pandas as pd
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from apps.data_hub.data_pipeline_ts.fetchers.base import ColumnDef, TableSchema
from apps.data_hub.data_pipeline_ts.jobs.specs import InfrastructureSpec, JobSpec


RuntimeSpec = JobSpec | InfrastructureSpec
PLACEHOLDER_PATTERN = re.compile(r"^\{([a-z_]+)\}$")
NUMERIC_PATTERN = re.compile(r"^-?\d+(?:\.\d+)?$")
DATE_LIKE_COLUMNS = {
    "ann_date",
    "cal_date",
    "delist_date",
    "div_listdate",
    "end_date",
    "f_ann_date",
    "imp_date",
    "ipo_date",
    "issue_date",
    "list_date",
    "pretrade_date",
    "pub_date",
    "release_date",
    "setup_date",
    "snapshot_date",
    "start_date",
    "trade_date",
}
STRING_CODE_COLUMNS = {"symbol"}
TEXT_HINTS = (
    "business_scope",
    "desc",
    "introduction",
    "main_business",
    "office",
    "reason",
    "scope",
    "summary",
    "website",
)
DEFAULT_MAX_SAMPLE_PARAMS = 6


def _nonnull_string_values(series: pd.Series) -> list[str]:
    values: list[str] = []
    for value in series.dropna().tolist():
        normalized = str(value).strip()
        if not normalized or normalized.lower() in {"nan", "none", "null"}:
            continue
        values.append(normalized)
    return values


def _varchar_dtype(max_length: int) -> str:
    if max_length <= 8:
        return "VARCHAR(8)"
    if max_length <= 16:
        return "VARCHAR(16)"
    if max_length <= 32:
        return "VARCHAR(32)"
    if max_length <= 64:
        return "VARCHAR(64)"
    if max_length <= 128:
        return "VARCHAR(128)"
    if max_length <= 255:
        return "VARCHAR(255)"
    return "TEXT"


def _varchar_length(dtype: str) -> int | None:
    upper = dtype.upper()
    if not upper.startswith("VARCHAR("):
        return None
    return int(upper.removeprefix("VARCHAR(").removesuffix(")"))


def _needs_dtype_change(current_dtype: str, inferred_dtype: str) -> bool:
    current = current_dtype.upper()
    inferred = inferred_dtype.upper()

    if current == inferred:
        return False

    current_varchar_length = _varchar_length(current)
    inferred_varchar_length = _varchar_length(inferred)
    if current_varchar_length is not None and inferred_varchar_length is not None:
        return inferred_varchar_length > current_varchar_length

    return True


def infer_column_def_from_series(column_name: str, series: pd.Series) -> ColumnDef:
    normalized_name = column_name.lower()
    values = _nonnull_string_values(series)

    if normalized_name == "ts_code":
        return ColumnDef("VARCHAR(16)", nullable=True)

    if not values:
        return ColumnDef("TEXT", nullable=True)

    if (
        normalized_name.endswith("_date")
        or normalized_name in DATE_LIKE_COLUMNS
    ) and all(len(value) == 8 and value.isdigit() for value in values):
        return ColumnDef("CHAR(8)", nullable=True)

    max_length = max(len(value) for value in values)

    if normalized_name in STRING_CODE_COLUMNS or normalized_name.endswith("_code"):
        return ColumnDef(_varchar_dtype(max_length), nullable=True)

    if normalized_name.endswith("_time") and all(value.isdigit() for value in values):
        return ColumnDef(_varchar_dtype(max_length), nullable=True)

    if normalized_name.endswith("_type"):
        return ColumnDef(_varchar_dtype(max_length), nullable=True)

    if normalized_name.endswith("_flag"):
        if all(value in {"0", "1"} for value in values):
            return ColumnDef("TINYINT", nullable=True)
        return ColumnDef(_varchar_dtype(max_length), nullable=True)

    if all(value in {"0", "1"} for value in values):
        return ColumnDef("TINYINT", nullable=True)

    if pd.api.types.is_numeric_dtype(series) or all(NUMERIC_PATTERN.match(value) for value in values):
        return ColumnDef("DOUBLE", nullable=True)

    if max_length > 255 or any(hint in normalized_name for hint in TEXT_HINTS):
        return ColumnDef("TEXT", nullable=True)

    return ColumnDef(_varchar_dtype(max_length), nullable=True)


def compare_frame_to_schema(frame: pd.DataFrame, schema: TableSchema) -> dict[str, ColumnDef]:
    return compare_frames_to_schema([frame], schema)


def compare_frames_to_schema(frames: list[pd.DataFrame], schema: TableSchema) -> dict[str, ColumnDef]:
    non_empty_frames = [frame for frame in frames if not frame.empty]
    if not non_empty_frames:
        return {}

    frame = pd.concat(non_empty_frames, ignore_index=True, sort=False)
    changed: dict[str, ColumnDef] = {}
    for column_name in frame.columns:
        current = schema.columns.get(column_name)
        if current is None:
            continue
        values = _nonnull_string_values(frame[column_name])
        if not values:
            continue
        inferred = infer_column_def_from_series(column_name, frame[column_name])
        if _needs_dtype_change(current.dtype, inferred.dtype):
            changed[column_name] = inferred
    return changed


def unobserved_schema_columns(frames: list[pd.DataFrame], schema: TableSchema) -> list[str]:
    non_empty_frames = [frame for frame in frames if not frame.empty]
    if not non_empty_frames:
        return list(schema.columns)

    frame = pd.concat(non_empty_frames, ignore_index=True, sort=False)
    unobserved: list[str] = []
    for column_name in schema.columns:
        if column_name not in frame.columns:
            unobserved.append(column_name)
            continue
        if not _nonnull_string_values(frame[column_name]):
            unobserved.append(column_name)
    return unobserved


def _table_columns(engine: Engine, table_name: str) -> set[str]:
    inspector = inspect(engine)
    if not inspector.has_table(table_name):
        return set()
    return {column["name"] for column in inspector.get_columns(table_name)}


def _latest_column_value(engine: Engine, table_name: str, column_name: str) -> str | None:
    if column_name not in _table_columns(engine, table_name):
        return None

    with engine.begin() as connection:
        row = connection.execute(
            text(
                f"""
                SELECT MAX(`{column_name}`) AS value
                FROM `{table_name}`
                WHERE `{column_name}` IS NOT NULL AND `{column_name}` <> ''
                """
            )
        ).mappings().first()
    if not row:
        return None
    value = row.get("value")
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _distinct_nonempty_values(
    engine: Engine,
    table_name: str,
    column_name: str,
    *,
    descending: bool = False,
) -> list[str]:
    if column_name not in _table_columns(engine, table_name):
        return []

    order = "DESC" if descending else "ASC"
    with engine.begin() as connection:
        rows = connection.execute(
            text(
                f"""
                SELECT DISTINCT `{column_name}` AS value
                FROM `{table_name}`
                WHERE `{column_name}` IS NOT NULL AND `{column_name}` <> ''
                ORDER BY `{column_name}` {order}
                """
            )
        ).mappings().all()

    return [normalized for row in rows if (normalized := str(row["value"]).strip())]


def _spread_sample(values: list[str], limit: int) -> list[str]:
    if limit <= 0 or not values:
        return []
    if len(values) <= limit:
        return values
    if limit == 1:
        return [values[-1]]

    indexes: list[int] = []
    for position in range(limit):
        index = round(position * (len(values) - 1) / (limit - 1))
        if index not in indexes:
            indexes.append(index)

    if len(indexes) < limit:
        for index in range(len(values)):
            if index not in indexes:
                indexes.append(index)
            if len(indexes) == limit:
                break

    return [values[index] for index in indexes]


def _successful_effective_dates(spec: RuntimeSpec, engine: Engine, *, max_samples: int) -> list[str]:
    if not inspect(engine).has_table("job_run_log"):
        return []

    columns = _table_columns(engine, "job_run_log")
    if "job_name" not in columns:
        return []

    if "effective_date" in columns and "as_of_date" in columns:
        date_expression = "COALESCE(`effective_date`, `as_of_date`)"
    elif "effective_date" in columns:
        date_expression = "`effective_date`"
    elif "as_of_date" in columns:
        date_expression = "`as_of_date`"
    else:
        return []

    predicates = ["`job_name` = :job_name", f"{date_expression} IS NOT NULL", f"{date_expression} <> ''"]
    params: dict[str, Any] = {"job_name": spec.name}
    if "status" in columns:
        predicates.append("`status` = :status")
        params["status"] = "success"
    if "rows_written" in columns:
        predicates.append("`rows_written` > 0")

    with engine.begin() as connection:
        rows = connection.execute(
            text(
                f"""
                SELECT DISTINCT {date_expression} AS value
                FROM `job_run_log`
                WHERE {' AND '.join(predicates)}
                ORDER BY value ASC
                """
            ),
            params,
        ).mappings().all()

    values = [normalized for row in rows if (normalized := str(row["value"]).strip())]
    return _spread_sample(values, max_samples)


def _table_sample_dates(
    spec: RuntimeSpec,
    engine: Engine,
    *,
    fallback_date: str,
    max_samples: int,
) -> list[str]:
    params = getattr(spec, "params", None) or {}
    candidates: list[str] = []

    for param_name, raw_value in params.items():
        if not isinstance(raw_value, str):
            continue
        placeholder_match = PLACEHOLDER_PATTERN.match(raw_value)
        if placeholder_match is None:
            continue
        for candidate in (param_name, placeholder_match.group(1), *spec.scope_columns):
            if candidate not in candidates:
                candidates.append(candidate)

    for candidate in candidates:
        values = _distinct_nonempty_values(engine, spec.table_name, candidate)
        if values:
            return _spread_sample(values, max_samples)

    latest = _resolve_single_sample_params(spec, engine, fallback_date=fallback_date)
    for value in latest.values():
        if isinstance(value, str) and value.strip():
            return [value]
    return [fallback_date]


def _dedupe_param_sets(param_sets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[tuple[str, Any], ...]] = set()
    for params in param_sets:
        key = tuple(sorted(params.items()))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(params)
    return deduped


def _resolve_pledge_detail_param_sets(engine: Engine, max_samples: int) -> list[dict[str, Any]]:
    sample_codes: list[str] = []
    for table_name in ("stock_pledge_detail", "stock_daily", "stock_basic"):
        for code in _distinct_nonempty_values(engine, table_name, "ts_code", descending=True):
            if code not in sample_codes:
                sample_codes.append(code)
            if len(sample_codes) == max_samples:
                return [{"ts_code": code} for code in sample_codes]
    return [{"ts_code": code} for code in sample_codes]


def _placeholder_params(spec: RuntimeSpec) -> dict[str, str]:
    params = getattr(spec, "params", None) or {}
    placeholder_params: dict[str, str] = {}
    for param_name, raw_value in params.items():
        if not isinstance(raw_value, str):
            continue
        placeholder_match = PLACEHOLDER_PATTERN.match(raw_value)
        if placeholder_match is None:
            continue
        placeholder_params[param_name] = placeholder_match.group(1)
    return placeholder_params


def _build_placeholder_param_set(spec: RuntimeSpec, sample_value: str) -> dict[str, Any]:
    params = getattr(spec, "params", None) or {}
    resolved_params: dict[str, Any] = {}
    for param_name, raw_value in params.items():
        if isinstance(raw_value, str) and PLACEHOLDER_PATTERN.match(raw_value):
            resolved_params[param_name] = sample_value
        else:
            resolved_params[param_name] = raw_value
    return resolved_params


def resolve_sparse_column_param_sets(
    spec: RuntimeSpec,
    engine: Engine,
    column_names: list[str],
    *,
    max_param_sets: int = DEFAULT_MAX_SAMPLE_PARAMS,
) -> list[dict[str, Any]]:
    if not column_names or max_param_sets <= 0:
        return []

    if spec.name == "trade_cal":
        return []

    if spec.name == "pledge_detail":
        return _resolve_pledge_detail_param_sets(engine, max_param_sets)

    placeholder_params = _placeholder_params(spec)
    if not placeholder_params:
        return []

    distinct_placeholders = set(placeholder_params.values())
    if len(distinct_placeholders) > 1:
        return []

    table_columns = _table_columns(engine, spec.table_name)
    candidate_value_columns: list[str] = []
    for param_name, placeholder_name in placeholder_params.items():
        for candidate in (param_name, placeholder_name, *spec.scope_columns):
            if candidate in table_columns and candidate not in candidate_value_columns:
                candidate_value_columns.append(candidate)

    if not candidate_value_columns:
        return []

    param_sets: list[dict[str, Any]] = []
    for column_name in column_names:
        if column_name not in table_columns:
            continue
        for candidate_value_column in candidate_value_columns:
            with engine.begin() as connection:
                rows = connection.execute(
                    text(
                        f"""
                        SELECT DISTINCT `{candidate_value_column}` AS value
                        FROM `{spec.table_name}`
                        WHERE `{column_name}` IS NOT NULL
                          AND CAST(`{column_name}` AS CHAR) <> ''
                          AND `{candidate_value_column}` IS NOT NULL
                          AND `{candidate_value_column}` <> ''
                        ORDER BY `{candidate_value_column}` ASC
                        """
                    )
                ).mappings().all()

            if not rows:
                continue

            for row in rows:
                sample_value = str(row["value"]).strip()
                if not sample_value:
                    continue
                param_sets.append(_build_placeholder_param_set(spec, sample_value))
                break
            if len(param_sets) >= max_param_sets:
                break
            if rows:
                break
        if len(param_sets) >= max_param_sets:
            break

    deduped = _dedupe_param_sets(param_sets)
    deduped.sort(key=lambda params: tuple(str(value) for _, value in sorted(params.items())))
    return deduped[:max_param_sets]


def _resolve_date_placeholder(
    spec: RuntimeSpec,
    engine: Engine,
    *,
    param_name: str,
    placeholder_name: str,
    fallback_date: str,
) -> str:
    columns = _table_columns(engine, spec.table_name)
    candidates: list[str] = []

    for candidate in (param_name, placeholder_name, *spec.scope_columns):
        if candidate in columns and candidate not in candidates:
            candidates.append(candidate)

    for candidate in candidates:
        resolved = _latest_column_value(engine, spec.table_name, candidate)
        if resolved:
            return resolved

    return fallback_date


def _resolve_single_sample_params(spec: RuntimeSpec, engine: Engine, fallback_date: str = "20260318") -> dict[str, Any]:
    if spec.name == "trade_cal":
        end_date = _resolve_date_placeholder(
            spec,
            engine,
            param_name="end_date",
            placeholder_name="cal_date",
            fallback_date=fallback_date,
        )
        start_date = (datetime.strptime(end_date, "%Y%m%d") - timedelta(days=28)).strftime("%Y%m%d")
        return {"start_date": start_date, "end_date": end_date}

    if spec.name == "pledge_detail":
        for table_name in (spec.table_name, "stock_daily", "stock_basic"):
            stock_code = _latest_column_value(engine, table_name, "ts_code")
            if stock_code:
                return {"ts_code": stock_code}
        return {}

    params = getattr(spec, "params", None) or {}
    if not params:
        return {}

    resolved_params: dict[str, Any] = {}
    for param_name, raw_value in params.items():
        if not isinstance(raw_value, str):
            resolved_params[param_name] = raw_value
            continue

        placeholder_match = PLACEHOLDER_PATTERN.match(raw_value)
        if placeholder_match is None:
            resolved_params[param_name] = raw_value
            continue

        resolved_params[param_name] = _resolve_date_placeholder(
            spec,
            engine,
            param_name=param_name,
            placeholder_name=placeholder_match.group(1),
            fallback_date=fallback_date,
        )

    return resolved_params


def resolve_sample_params(spec: RuntimeSpec, engine: Engine, fallback_date: str = "20260318") -> dict[str, Any]:
    return _resolve_single_sample_params(spec, engine, fallback_date=fallback_date)


def resolve_sample_param_sets(
    spec: RuntimeSpec,
    engine: Engine,
    fallback_date: str = "20260318",
    max_samples: int = DEFAULT_MAX_SAMPLE_PARAMS,
) -> list[dict[str, Any]]:
    if spec.name == "trade_cal":
        return [_resolve_single_sample_params(spec, engine, fallback_date=fallback_date)]

    if spec.name == "pledge_detail":
        param_sets = _resolve_pledge_detail_param_sets(engine, max_samples)
        return param_sets or [{}]

    params = getattr(spec, "params", None) or {}
    if not params:
        return [{}]

    placeholder_params = {
        param_name: raw_value
        for param_name, raw_value in params.items()
        if isinstance(raw_value, str) and PLACEHOLDER_PATTERN.match(raw_value)
    }
    if not placeholder_params:
        return [dict(params)]

    sample_dates = _successful_effective_dates(spec, engine, max_samples=max_samples)
    if not sample_dates:
        sample_dates = _table_sample_dates(
            spec,
            engine,
            fallback_date=fallback_date,
            max_samples=max_samples,
        )

    param_sets: list[dict[str, Any]] = []
    for sample_date in sample_dates:
        resolved_params: dict[str, Any] = {}
        for param_name, raw_value in params.items():
            if isinstance(raw_value, str) and PLACEHOLDER_PATTERN.match(raw_value):
                resolved_params[param_name] = sample_date
            else:
                resolved_params[param_name] = raw_value
        param_sets.append(resolved_params)

    if not param_sets:
        param_sets.append(_resolve_single_sample_params(spec, engine, fallback_date=fallback_date))

    return _dedupe_param_sets(param_sets)
