from __future__ import annotations

import importlib
from pathlib import Path


def test_split_execution_modules_are_importable_without_compat_executor() -> None:
    selection_module = importlib.import_module("apps.data_hub.data_pipeline_ts.execution.selection")
    runner_module = importlib.import_module("apps.data_hub.data_pipeline_ts.execution.runner")
    infrastructure_module = importlib.import_module("apps.data_hub.data_pipeline_ts.execution.infrastructure")
    rendering_module = importlib.import_module("apps.data_hub.data_pipeline_ts.execution.rendering")
    execution_module = importlib.import_module("apps.data_hub.data_pipeline_ts.execution")
    pipeline_module = importlib.import_module("apps.data_hub.data_pipeline_ts")

    assert selection_module.select_job_specs is execution_module.select_job_specs
    assert selection_module.select_infrastructure_specs is execution_module.select_infrastructure_specs
    assert selection_module._parse_csv_values is execution_module._parse_csv_values
    assert runner_module.run_once is execution_module.run_once
    assert runner_module.run_once is pipeline_module.run_once
    assert runner_module.run_backfill is execution_module.run_backfill
    assert runner_module.run_backfill is pipeline_module.run_backfill
    assert infrastructure_module.run_infrastructure is execution_module.run_infrastructure
    assert infrastructure_module.run_infrastructure is pipeline_module.run_infrastructure
    assert callable(rendering_module._render_params)


def test_legacy_executor_module_has_been_deleted() -> None:
    executor_path = Path(__file__).resolve().parents[1] / "executor.py"
    assert not executor_path.exists()


def test_main_and_package_use_execution_package_directly() -> None:
    root = Path(__file__).resolve().parents[1]
    main_source = (root / "main.py").read_text(encoding="utf-8")
    init_source = (root / "__init__.py").read_text(encoding="utf-8")

    assert "from apps.data_hub.data_pipeline_ts.execution import (" in main_source
    assert "from apps.data_hub.data_pipeline_ts.execution import run_backfill, run_infrastructure, run_once" in init_source
