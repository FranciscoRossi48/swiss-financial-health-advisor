from __future__ import annotations

import numpy as np
import pandas as pd

from swiss_financial_health.scoring import scale_higher_is_better, scale_lower_is_better

CREDIT_READINESS_WEIGHTS = {
    "income_reliability_score": 0.25,
    "debt_capacity_score": 0.25,
    "cashflow_resilience_score": 0.25,
    "savings_discipline_score": 0.15,
    "spending_control_score": 0.10,
}


def compute_credit_readiness(scored_users: pd.DataFrame) -> pd.DataFrame:
    df = scored_users.copy()
    free_cashflow_ratio = df["avg_net_cashflow"] / df["avg_income"].replace(0, np.nan)

    df["income_reliability_score"] = scale_lower_is_better(df["income_cv"], good=0.08, poor=0.30)
    df["debt_capacity_score"] = scale_lower_is_better(df["avg_debt_to_income"], good=0.08, poor=0.30)
    df["cashflow_resilience_score"] = scale_higher_is_better(free_cashflow_ratio, good=0.05, excellent=0.22)
    df["savings_discipline_score"] = scale_higher_is_better(df["avg_savings_rate"], good=0.08, excellent=0.22)
    df["spending_control_score"] = scale_lower_is_better(df["avg_discretionary_ratio"], good=0.16, poor=0.34)

    df["credit_readiness_score"] = sum(
        df[col] * weight for col, weight in CREDIT_READINESS_WEIGHTS.items()
    ).round(1)
    df["credit_readiness_band"] = pd.cut(
        df["credit_readiness_score"],
        bins=[-1, 39, 59, 74, 100],
        labels=["not ready", "needs improvement", "moderate", "ready"],
    ).astype(str)
    return df


def build_risk_flags(credit_users: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    for record in credit_users.to_dict("records"):
        flags = risk_flags_for_user(record)
        if not flags:
            rows.append(
                {
                    "user_id": record["user_id"],
                    "flag": "No major risk flags",
                    "severity": "low",
                    "explanation": (
                        "The synthetic profile does not show a dominant credit readiness weakness."
                    ),
                }
            )
            continue

        for flag in flags:
            rows.append({"user_id": record["user_id"], **flag})

    return pd.DataFrame(rows)


def risk_flags_for_user(record: dict[str, object]) -> list[dict[str, str]]:
    flags: list[dict[str, str]] = []

    if record["avg_debt_to_income"] >= 0.25:
        flags.append(
            {
                "flag": "High debt burden",
                "severity": "high",
                "explanation": (
                    f"Debt payments represent {record['avg_debt_to_income']:.1%} of average monthly income."
                ),
            }
        )
    elif record["avg_debt_to_income"] >= 0.18:
        flags.append(
            {
                "flag": "Elevated debt burden",
                "severity": "medium",
                "explanation": (
                    "Debt payments are above a conservative affordability threshold at "
                    f"{record['avg_debt_to_income']:.1%}."
                ),
            }
        )

    if record["income_cv"] >= 0.30:
        flags.append(
            {
                "flag": "Highly variable income",
                "severity": "high",
                "explanation": (
                    f"Income coefficient of variation is {record['income_cv']:.2f}, "
                    "reducing repayment predictability."
                ),
            }
        )
    elif record["income_cv"] >= 0.22:
        flags.append(
            {
                "flag": "Variable income",
                "severity": "medium",
                "explanation": (
                    "Income volatility is material with a coefficient of variation of "
                    f"{record['income_cv']:.2f}."
                ),
            }
        )

    free_cashflow_ratio = record["avg_net_cashflow"] / record["avg_income"] if record["avg_income"] else 0
    if free_cashflow_ratio < 0:
        flags.append(
            {
                "flag": "Negative free cashflow",
                "severity": "high",
                "explanation": "Average monthly expenses and savings transfers exceed income.",
            }
        )
    elif free_cashflow_ratio < 0.05:
        flags.append(
            {
                "flag": "Thin cashflow buffer",
                "severity": "medium",
                "explanation": f"Free cashflow is only {free_cashflow_ratio:.1%} of average income.",
            }
        )

    if record["avg_savings_rate"] < 0.05:
        flags.append(
            {
                "flag": "Low savings discipline",
                "severity": "medium",
                "explanation": f"Average savings rate is {record['avg_savings_rate']:.1%}.",
            }
        )

    if record["avg_discretionary_ratio"] >= 0.32:
        flags.append(
            {
                "flag": "High discretionary spend",
                "severity": "medium",
                "explanation": (
                    f"Discretionary spending represents {record['avg_discretionary_ratio']:.1%} of income."
                ),
            }
        )

    return flags
