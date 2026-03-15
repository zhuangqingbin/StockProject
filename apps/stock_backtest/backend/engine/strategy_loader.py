from __future__ import annotations

import importlib.util
import inspect
import sys
import types
import uuid
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional

import backtrader as bt

from apps.stock_backtest.backend.infrastructure.settings import get_settings


@dataclass(frozen=True)
class StrategyTemplate:
    template_id: str
    name: str
    description: str
    required_feeds: list[str]
    parameters: dict[str, dict]
    source_code: str
    path: Path


def _load_module_from_path(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _find_strategy_class(module: types.ModuleType):
    for candidate in module.__dict__.values():
        if inspect.isclass(candidate) and issubclass(candidate, bt.Strategy) and candidate is not bt.Strategy:
            return candidate
    raise ValueError("No backtrader strategy class found")


def _build_template(path: Path) -> StrategyTemplate:
    source_code = path.read_text(encoding="utf-8")
    module = _load_module_from_path(path, f"stock_backtest_template_{path.stem}")
    metadata = getattr(module, "TEMPLATE_METADATA", {})
    strategy_class = _find_strategy_class(module)
    return StrategyTemplate(
        template_id=metadata.get("template_id", path.stem),
        name=metadata.get("name", strategy_class.__name__),
        description=metadata.get("description", ""),
        required_feeds=list(metadata.get("required_feeds", ["daily_kline"])),
        parameters=dict(metadata.get("parameters", {})),
        source_code=source_code,
        path=path,
    )


@lru_cache(maxsize=1)
def _load_strategy_templates() -> tuple[StrategyTemplate, ...]:
    settings = get_settings()
    templates: list[StrategyTemplate] = []
    for path in sorted(settings.templates_dir.glob("*.py")):
        if path.name.startswith("_"):
            continue
        templates.append(_build_template(path))
    return tuple(templates)


def list_strategy_templates() -> tuple[StrategyTemplate, ...]:
    return _load_strategy_templates()


def get_strategy_template(template_id: str) -> StrategyTemplate:
    for template in list_strategy_templates():
        if template.template_id == template_id:
            return template
    raise KeyError(f"Unknown strategy template: {template_id}")


@lru_cache(maxsize=32)
def load_template_strategy(template_id: str):
    template = get_strategy_template(template_id)
    module = _load_module_from_path(template.path, f"stock_backtest_template_runtime_{template_id}")
    return _find_strategy_class(module)


def load_custom_strategy(code: str):
    module_name = f"stock_backtest_custom_strategy_{uuid.uuid4().hex}"
    module = types.ModuleType(module_name)
    exec(code, module.__dict__)
    return _find_strategy_class(module)


def resolve_strategy_class(source_type: str, template_id: Optional[str], code: Optional[str]):
    if source_type == "template":
        if not template_id:
            raise ValueError("template_id is required for template strategies")
        return load_template_strategy(template_id)
    if not code:
        raise ValueError("code is required for custom strategies")
    return load_custom_strategy(code)


def clear_strategy_template_cache() -> None:
    _load_strategy_templates.cache_clear()
    load_template_strategy.cache_clear()
