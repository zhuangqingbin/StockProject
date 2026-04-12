from __future__ import annotations

from collections import defaultdict

import pandas as pd
from sklearn.cluster import AgglomerativeClustering


def analyze_factor_correlation(
    panel: pd.DataFrame,
    factor_cols: list[str],
    factor_scores: dict[str, float] | None = None,
) -> dict[str, object]:
    available = [column for column in factor_cols if column in panel.columns]
    matrix = panel.loc[:, available].corr(method="pearson").fillna(0.0)

    if len(available) <= 1:
        clusters = {0: available}
    else:
        distance = 1 - matrix.abs()
        model = AgglomerativeClustering(
            metric="precomputed",
            linkage="average",
            distance_threshold=0.5,
            n_clusters=None,
        )
        labels = model.fit_predict(distance)
        grouped: dict[int, list[str]] = defaultdict(list)
        for column, label in zip(available, labels):
            grouped[int(label)].append(column)
        clusters = dict(grouped)

    scores = factor_scores or {}
    representatives = {
        cluster_id: max(columns, key=lambda column: scores.get(column, 0.0)) if columns else None
        for cluster_id, columns in clusters.items()
    }
    return {
        "correlation_matrix": matrix,
        "clusters": clusters,
        "representatives": representatives,
    }
