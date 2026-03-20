import importlib


def test_new_package_names_are_importable() -> None:
    assert importlib.import_module("apps.data_hub")
    assert importlib.import_module("apps.data_hub.data_explorer.backend.main")
    assert importlib.import_module("apps.data_hub.data_pipeline_ts")
    assert importlib.import_module("apps.data_hub.data_pipeline_ak")
