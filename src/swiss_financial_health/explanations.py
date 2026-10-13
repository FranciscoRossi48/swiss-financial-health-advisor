"""Plain-language explanations for each Financial Health Score dimension.

For every dimension the app shows a *driver* (what in the customer's own numbers produces the
score) and a *target* (what would earn the remaining points). Both are derived from the same
scales as the score itself (HEALTH_SCALES), so the explanation can never disagree with the number.
"""

from __future__ import annotations

from collections.abc import Mapping

from swiss_financial_health.scoring import SCORE_WEIGHTS


def points_left(dimension: str, record: Mapping[str, float]) -> float:
    """Points of the composite score still available in this dimension."""
    return round(SCORE_WEIGHTS[dimension] * (100 - record[dimension]), 1)


def format_points(points: float) -> str:
    return f"{points:.1f}".removesuffix(".0")


def dimension_driver(dimension: str, record: Mapping[str, float]) -> str:
    if dimension == "liquidity_score":
        months = record["reserve_months"]
        if months < 0:
            shortfall = -months * record["avg_expense"]
            return (
                f"Over the last 12 months you spent CHF {shortfall:,.0f} more than came in, "
                "so there is no buffer for a surprise bill."
            )
        return (
            f"Your reserves cover {months:.1f} months of spending. Each month you keep about "
            f"CHF {record['avg_free_cashflow']:,.0f} after spending, savings included."
        )
    if dimension == "income_stability_score":
        return (
            f"Your monthly income moves about {record['income_cv']:.0%} around its average "
            f"of CHF {record['avg_income']:,.0f}."
        )
    if dimension == "savings_score":
        return f"You keep {record['avg_savings_rate']:.1%} of your income, in savings or left on the account."
    if dimension == "debt_score":
        if record["avg_debt_to_income"] == 0:
            return "You have no debt payments."
        return (
            f"Debt payments take {record['avg_debt_to_income']:.1%} of your income, "
            "against the 33% affordability guideline."
        )
    raise ValueError(f"Unknown dimension: {dimension}")


def dimension_target(dimension: str, record: Mapping[str, float]) -> str:
    left = points_left(dimension, record)
    if left == 0:
        return "Full points. Keep doing what you are doing."
    # each goal is the metric value at which HEALTH_SCALES awards full points
    goal = {
        "liquidity_score": "Build reserves to 3 months of spending",
        "income_stability_score": "Keep income variation under 10%",
        "savings_score": "Reach a 25% savings rate",
        "debt_score": "Bring debt payments under 5% of income",
    }[dimension]
    return f"{goal} → +{format_points(left)} pts"
