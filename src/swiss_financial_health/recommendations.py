from __future__ import annotations

import pandas as pd

DIMENSION_LABELS = {
    "liquidity_score": "liquidity",
    "income_stability_score": "income stability",
    "savings_score": "savings capacity",
    "debt_score": "debt exposure",
}

# When even the weakest dimension reaches the "strong" band, there is no problem to fix, so the
# coach suggests a next goal instead of pointing at a dimension that is already in good shape.
STRONG_DIMENSION_THRESHOLD = 80.0


def generate_recommendations(scored_users: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    score_cols = list(DIMENSION_LABELS)

    for record in scored_users.to_dict("records"):
        weakest = min(score_cols, key=lambda col: record[col])
        if record[weakest] >= STRONG_DIMENSION_THRESHOLD:
            rows.append(
                {
                    "user_id": record["user_id"],
                    "priority_dimension": "next goal",
                    "recommendation": (
                        "Your foundations are strong. Consider giving part of your monthly surplus a "
                        "long-term job, such as a pillar 3a retirement account."
                    ),
                    "explanation": (
                        "All four health dimensions score 80 or higher, and your reserves cover "
                        f"{record['reserve_months']:.1f} months of spending."
                    ),
                }
            )
            continue
        rows.append(
            {
                "user_id": record["user_id"],
                "priority_dimension": DIMENSION_LABELS[weakest],
                "recommendation": recommendation_for_dimension(weakest, record),
                "explanation": explanation_for_dimension(weakest, record),
            }
        )

    return pd.DataFrame(rows)


def recommendation_for_dimension(dimension: str, record: dict[str, object]) -> str:
    if dimension == "liquidity_score":
        return "Build a short-term cash buffer before increasing discretionary spending."
    if dimension == "income_stability_score":
        return "Use a conservative monthly baseline and route irregular income toward savings."
    if dimension == "savings_score":
        return "Automate a savings transfer near payday and target a first milestone of 10% of income."
    if dimension == "debt_score":
        return "Prioritize high-interest debt payments and avoid adding new recurring credit obligations."
    raise ValueError(f"Unknown dimension: {dimension}")


def explanation_for_dimension(dimension: str, record: dict[str, object]) -> str:
    if dimension == "liquidity_score":
        return (
            f"Your reserves cover {record['reserve_months']:.1f} months of spending, "
            "short of the 3-month buffer that absorbs unexpected expenses."
        )
    if dimension == "income_stability_score":
        return (
            f"Income coefficient of variation is {record['income_cv']:.2f}, "
            "indicating relatively uneven inflows."
        )
    if dimension == "savings_score":
        return (
            f"Average savings rate is {record['avg_savings_rate']:.1%}, below a sustainable long-term target."
        )
    if dimension == "debt_score":
        return f"Debt payments represent {record['avg_debt_to_income']:.1%} of monthly income."
    raise ValueError(f"Unknown dimension: {dimension}")
