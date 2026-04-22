from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StrategySpec:
    strategy_name: str
    strategy_description: str
    module_path: str


STRATEGY_REGISTRY: dict[str, StrategySpec] = {
    "bottom_volume_matrix": StrategySpec(
        strategy_name="bottom_volume_matrix",
        strategy_description="底部放量策略矩阵",
        module_path="apps.data_hub.data_pipeline_ts.analysis.bottom_val_strategies.bottom_volume_matrix",
    ),
    "flow_chip_northbound_matrix": StrategySpec(
        strategy_name="flow_chip_northbound_matrix",
        strategy_description="资金流 + 筹码 + 北向策略矩阵",
        module_path="apps.data_hub.data_pipeline_ts.analysis.flow_chip_northbound_strategies.flow_chip_northbound_matrix",
    ),
    "limit_inst_matrix": StrategySpec(
        strategy_name="limit_inst_matrix",
        strategy_description="涨跌停 + 龙虎榜事件矩阵",
        module_path="apps.data_hub.data_pipeline_ts.analysis.event_price_action_strategies.limit_inst_matrix",
    ),
    "supply_shock_matrix": StrategySpec(
        strategy_name="supply_shock_matrix",
        strategy_description="供给冲击与吸收修复矩阵",
        module_path="apps.data_hub.data_pipeline_ts.analysis.supply_shock_strategies.supply_shock_matrix",
    ),
    "top_list_matrix": StrategySpec(
        strategy_name="top_list_matrix",
        strategy_description="龙虎榜策略矩阵",
        module_path="apps.data_hub.data_pipeline_ts.analysis.top_list_strategies.top_list_matrix",
    ),
}


def list_strategy_names() -> list[str]:
    return list(STRATEGY_REGISTRY.keys())
