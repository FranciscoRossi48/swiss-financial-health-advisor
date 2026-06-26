from __future__ import annotations

import numpy as np
import pandas as pd


SCORE_WEIGHTS = {
    "liquidity_score": 0.30,
    "income_stability_score": 0.20,
    "savings_score": 0.30,
    "debt_score": 0.20,
}


def compute_financial_health_score(user_summary: pd.DataFrame) -> pd.DataFrame:
    df = user_summary.copy()
    liquidity_months = df["avg_net_cashflow"].clip(lower=0) / df["avg_expense"].replace(0, np.nan)

    df["liquidity_score"] = scale_higher_is_better(liquidity_months, good=0.25, excellent=0.75)
    df["income_stability_score"] = scale_lower_is_better(df["income_cv"], good=0.10, poor=0.35)
    df["savings_score"] = scale_higher_is_better(df["avg_savings_rate"], good=0.10, excellent=0.25)
    df["debt_score"] = scale_lower_is_better(df["avg_debt_to_income"], good=0.05, poor=0.25)

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
