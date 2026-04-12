from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.ensemble import GradientBoostingRegressor

from apps.quant_platform.research.analyzer.ic_analysis import analyze_factor_ic
from .base import zscore_by_date

try:
    from lightgbm import LGBMRegressor
except ImportError:  # pragma: no cover - optional dependency
    LGBMRegressor = None

try:
    from xgboost import XGBRegressor
except ImportError:  # pragma: no cover - optional dependency
    XGBRegressor = None


def _normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    norm = sum(abs(weight) for weight in weights.values())
    if norm == 0:
        equal = 1 / max(len(weights), 1)
        return {key: equal for key in weights}
    return {key: weight / norm for key, weight in weights.items()}


def _build_ml_regressor() -> tuple[object, str]:
    if LGBMRegressor is not None:
        return (
            LGBMRegressor(
                n_estimators=200,
                learning_rate=0.05,
                subsample=0.9,
                colsample_bytree=0.9,
                random_state=7,
                verbosity=-1,
            ),
            "lightgbm",
        )
    if XGBRegressor is not None:
        return (
            XGBRegressor(
                n_estimators=200,
                max_depth=3,
                learning_rate=0.05,
                subsample=0.9,
                colsample_bytree=0.9,
                objective="reg:squarederror",
                random_state=7,
                n_jobs=1,
                verbosity=0,
            ),
            "xgboost",
        )
    return GradientBoostingRegressor(random_state=7), "gradient_boosting"


class CompositeFactorBuilder:
    def build(
        self,
        panel: pd.DataFrame,
        factor_cols: list[str],
        target_col: str = "overnight_return",
        method: str = "equal_weight",
    ) -> pd.DataFrame:
        available = [column for column in factor_cols if column in panel.columns]
        if not available:
            raise ValueError("no factor columns available for composite build")

        standardized = zscore_by_date(panel.copy(), available, date_col="trade_date")
        result = standardized.copy()

        if method == "equal_weight":
            weights = {column: 1 / len(available) for column in available}
            result["composite_factor"] = result[available].mean(axis=1)
        elif method == "ic_weighted":
            weights = _normalize_weights(
                {column: analyze_factor_ic(result, factor_col=column, target_col=target_col)["mean_ic"] for column in available}
            )
            result["composite_factor"] = sum(result[column] * weight for column, weight in weights.items())
        elif method == "icir_weighted":
            weights = _normalize_weights(
                {column: analyze_factor_ic(result, factor_col=column, target_col=target_col)["ic_ir"] for column in available}
            )
            result["composite_factor"] = sum(result[column] * weight for column, weight in weights.items())
        elif method == "orthogonal_equal":
            matrix = result[available].fillna(0.0).to_numpy()
            q_matrix, _ = np.linalg.qr(matrix)
            result["composite_factor"] = q_matrix.mean(axis=1)
            weights = {column: 1 / len(available) for column in available}
        elif method == "pca":
            pca = PCA(n_components=1)
            result["composite_factor"] = pca.fit_transform(result[available].fillna(0.0))[:, 0]
            weights = {column: float(weight) for column, weight in zip(available, pca.components_[0])}
            weights = _normalize_weights(weights)
        elif method == "ml":
            train = result.loc[:, [*available, target_col]].dropna()
            if len(train) < 2:
                weights = {column: 1 / len(available) for column in available}
                result["composite_factor"] = result[available].mean(axis=1)
                result.attrs["composite_ml_model"] = "fallback_equal_weight"
            else:
                model, model_name = _build_ml_regressor()
                model.fit(train[available], train[target_col])
                result["composite_factor"] = model.predict(result[available].fillna(0.0))
                importances = getattr(model, "feature_importances_", np.ones(len(available), dtype=float))
                weights = _normalize_weights({column: float(weight) for column, weight in zip(available, importances)})
                result.attrs["composite_ml_model"] = model_name
        else:
            raise ValueError(f"unsupported composite method: {method}")

        result["composite_factor_weight"] = np.mean(np.abs(list(weights.values())))
        for column, weight in weights.items():
            result[f"weight_{column}"] = weight
        return result
