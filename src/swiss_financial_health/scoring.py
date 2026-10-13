from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

SCORE_WEIGHTS = {
    "liquidity_score": 0.30,
    "income_stability_score": 0.20,
    "savings_score": 0.30,
    "debt_score": 0.20,
}


@dataclass(frozen=True)
class DimensionScale:
    """How one dimension's metric maps to 0-100 points (rationale: docs/scoring-methodology.md)."""

    metric: str
    higher_is_better: bool
    zero_at: float  # metric value that earns 0 points
    full_at: float  # metric value that earns 100 points

    def score(self, value: float) -> float:
        scaled = (value - self.zero_at) / (self.full_at - self.zero_at)
        return round(min(max(scaled, 0.0), 1.0) * 100, 1)

    def value_for_score(self, score: float) -> float:
        """Inverse of score(): the metric value that earns `score` points."""
        return self.zero_at + (score / 100) * (self.full_at - self.zero_at)


HEALTH_SCALES = {
    "liquidity_score": DimensionScale("reserve_months", True, zero_at=1.0, full_at=3.0),
    "income_stability_score": DimensionScale("income_cv", False, zero_at=0.35, full_at=0.10),
    "savings_score": DimensionScale("avg_savings_rate", True, zero_at=0.10, full_at=0.25),
    "debt_score": DimensionScale("avg_debt_to_income", False, zero_at=0.25, full_at=0.05),
}


def compute_financial_health_score(user_summary: pd.DataFrame) -> pd.DataFrame:
    df = user_summary.copy()

    for col, scale in HEALTH_SCALES.items():
        if scale.higher_is_better:
            df[col] = scale_higher_is_better(df[scale.metric], good=scale.zero_at, excellent=scale.full_at)
        else:
            df[col] = scale_lower_is_better(df[scale.metric], good=scale.full_at, poor=scale.zero_at)

    df["financial_health_score"] = sum(df[col] * weight for col, weight in SCORE_WEIGHTS.items()).round(1)
    df["health_band"] = pd.cut(
        df["financial_health_score"],
        bins=[-1, 39, 59, 79, 100],
        labels=["critical", "fragile", "healthy", "strong"],
    ).astype(str)
    return df


def scale_higher_is_better(values: pd.Series, good: float, excellent: float) -> pd.Series:
    scaled = (values - good) / (excellent - good)
    return (scaled.clip(0, 1) * 100).fillna(0).round(1)


def scale_lower_is_better(values: pd.Series, good: float, poor: float) -> pd.Series:
    scaled = 1 - ((values - good) / (poor - good))
    return (scaled.clip(0, 1) * 100).fillna(0).round(1)
