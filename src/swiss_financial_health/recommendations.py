from __future__ import annotations

import pandas as pd


DIMENSION_LABELS = {
    "liquidity_score": "liquidity",
    "income_stability_score": "income stability",
    "savings_score": "savings capacity",
    "debt_score": "debt exposure",
}


def generate_recommendations(scored_users: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    score_cols = list(DIMENSION_LABELS)

    for record in scored_users.to_dict("records"):
        weakest = min(score_cols, key=lambda col: record[col])
        recommendation = recommendation_for_dimension(weakest, record)
        rows.append(
            {
                "user_id": record["user_id"],
                "priority_dimension": DIMENSION_LABELS[weakest],
                "recommendation": recommendation,
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
        return f"Average monthly net cashflow is CHF {record['avg_net_cashflow']:.0f}, limiting resilience to unexpected expenses."
    if dimension == "income_stability_score":
        return f"Income coefficient of variation is {record['income_cv']:.2f}, indicating relatively uneven inflows."
    if dimension == "savings_score":
        return f"Average savings rate is {record['avg_savings_rate']:.1%}, below a sustainable long-term target."
    if dimension == "debt_score":
        return f"Debt payments represent {record['avg_debt_to_income']:.1%} of monthly income."
    raise ValueError(f"Unknown dimension: {dimension}")
