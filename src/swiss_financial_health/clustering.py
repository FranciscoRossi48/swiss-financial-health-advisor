from __future__ import annotations

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


CLUSTER_FEATURES = [
    "avg_income",
    "avg_savings_rate",
    "avg_debt_to_income",
    "avg_discretionary_ratio",
    "income_cv",
]


def fit_user_segments(scored_users: pd.DataFrame, n_clusters: int = 5, random_state: int = 42) -> tuple[pd.DataFrame, pd.DataFrame, float]:
    df = scored_users.copy()
    scaler = StandardScaler()
    matrix = scaler.fit_transform(df[CLUSTER_FEATURES])

    model = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=20)
    labels = model.fit_predict(matrix)
    df["segment"] = labels
    score = float(silhouette_score(matrix, labels))

    centroids = (
        df.groupby("segment")[CLUSTER_FEATURES + ["financial_health_score"]]
        .mean()
        .round(3)
        .reset_index()
    )
    centroids["segment_label"] = centroids.apply(label_segment, axis=1)
    df = df.merge(centroids[["segment", "segment_label"]], on="segment", how="left")
    return df, centroids, score


def label_segment(row: pd.Series) -> str:
    if row["avg_debt_to_income"] >= 0.18:
        return "Debt pressure"
    if row["income_cv"] >= 0.25:
        return "Variable income"
    if row["avg_savings_rate"] >= 0.20:
        return "Stable saver"
    if row["avg_discretionary_ratio"] >= 0.25:
        return "High discretionary"
    return "Balanced user"
