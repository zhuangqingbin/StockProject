from __future__ import annotations

import importlib
from pathlib import Path


def test_split_runtime_modules_are_importable_without_compat_layers() -> None:
    specs_module = importlib.import_module("apps.data_hub.data_pipeline_ts.jobs.specs")
    profiles_module = importlib.import_module("apps.data_hub.data_pipeline_ts.jobs.profiles")
    catalog_module = importlib.import_module("apps.data_hub.data_pipeline_ts.jobs.catalog")
    jobs_module = importlib.import_module("apps.data_hub.data_pipeline_ts.jobs")
    calendar_module = importlib.import_module("apps.data_hub.data_pipeline_ts.execution.calendar")
    context_module = importlib.import_module("apps.data_hub.data_pipeline_ts.execution.context")
    persistence_module = importlib.import_module("apps.data_hub.data_pipeline_ts.execution.persistence")

    assert specs_module.JobSpec is jobs_module.JobSpec
    assert profiles_module.PROFILE_SPECS is jobs_module.PROFILE_SPECS
    assert catalog_module.ALL_JOBS is jobs_module.ALL_JOBS
    assert hasattr(calendar_module, "get_trade_cal")
    assert hasattr(context_module, "ExecutionContext")
    assert hasattr(persistence_module, "DatabaseWriter")


def test_legacy_registry_and_runtime_modules_have_been_deleted() -> None:
    root = Path(__file__).resolve().parents[1]

    assert not (root / "registry.py").exists()
    assert not (root / "runtime.py").exists()
    assert not (root / "calendar.py").exists()
    assert not (root / "context.py").exists()
    assert not (root / "persistence.py").exists()
