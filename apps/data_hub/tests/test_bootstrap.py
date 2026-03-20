from __future__ import annotations

import importlib


def test_core_packages_are_importable():
    modules = (
        "apps.data_hub",
        "apps.data_hub.data_pipeline_ts",
        "apps.data_hub.data_pipeline_ak",
        "apps.data_hub.data_explorer",
    )

    for module_name in modules:
        module = importlib.import_module(module_name)
        assert module is not None
