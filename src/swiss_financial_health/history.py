"""Month-by-month Financial Health Score, for the score history shown in the app.

Each month's score is computed on an expanding window: everything observed from the first month
up to and including that month, run through the same feature summary and scoring as the headline
score. The last month therefore equals the current score, and earlier months show how the score
built up as the customer accumulated history (reserves in particular grow over time).
"""

from __future__ import annotations

import pandas as pd

from swiss_financial_health.features import build_user_summary, safe_ratio
from swiss_financial_health.scoring import compute_financial_health_score


def compute_score_history(monthly_features: pd.DataFrame) -> pd.DataFrame:
    months = sorted(monthly_features["month"].unique())
    frames = []
    for cutoff in months:
        window = monthly_features.loc[monthly_features["month"] <= cutoff].copy()
        # income_cv on the monthly table describes the full period, so recompute it for the window
        income = window.groupby("user_id")["income"]
        window["income_cv"] = window["user_id"].map(safe_ratio(income.std().fillna(0), income.mean()))
        scored = compute_financial_health_score(build_user_summary(window))
        frames.append(scored[["user_id", "financial_health_score"]].assign(month=cutoff))

    history = pd.concat(frames, ignore_index=True)
    return history[["user_id", "month", "financial_health_score"]].sort_values(["user_id", "month"])
