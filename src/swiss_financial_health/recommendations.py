from __future__ import annotations

import math
from itertools import pairwise

import pandas as pd

from swiss_financial_health.scoring import HEALTH_SCALES, SCORE_WEIGHTS

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


# ---------------------------------------------------------------------------------------------
# Action plan
#
# Each recommendation comes with three concrete steps. The points still available in the focus
# dimension are split into three equal milestones; each step names the change in the customer's
# own numbers (CHF, rates) that reaches its milestone, and carries the score gain it would earn.
# Amounts come from inverting the same scale the score uses, so the plan stays auditable.
# ---------------------------------------------------------------------------------------------

PRIORITY_DIMENSION_KEYS = {label: key for key, label in DIMENSION_LABELS.items()}
PLAN_HORIZON_MONTHS = 12


def plan_steps(priority_dimension: str, record: dict[str, float]) -> list[dict[str, object]]:
    if priority_dimension == "next goal":
        return _next_goal_steps(record)

    dimension = PRIORITY_DIMENSION_KEYS[priority_dimension]
    scale = HEALTH_SCALES[dimension]
    current_score = record[dimension]
    milestone_scores = [current_score + (100 - current_score) * k / 3 for k in (1, 2, 3)]
    values = [record[scale.metric]] + [scale.value_for_score(score) for score in milestone_scores]

    gains = [SCORE_WEIGHTS[dimension] * (score - current_score) for score in milestone_scores]
    # round the cumulative gain so the step points always add up to the rounded total
    points = [round(gain) - round(previous) for gain, previous in zip(gains, [0.0, *gains[:-1]], strict=True)]

    texts = _STEP_TEXT[dimension](values, record)
    return [
        {"title": title, "body": body, "points": pts}
        for (title, body), pts in zip(texts, points, strict=True)
    ]


def _round_up(amount: float, step: int = 10) -> int:
    return max(step, math.ceil(amount / step) * step)


def _discretionary_spend(record: dict[str, float]) -> float:
    return record["avg_discretionary_ratio"] * record["avg_income"]


def _liquidity_steps(values: list[float], record: dict[str, float]) -> list[tuple[str, str]]:
    expense = record["avg_expense"]
    monthly = [(after - before) * expense / PLAN_HORIZON_MONTHS for before, after in pairwise(values)]
    target = values[-1] * expense
    return [
        (
            f"Free up an extra CHF {_round_up(monthly[0])} a month for a buffer",
            "Move it to a separate pocket automatically on payday, "
            "so it never reaches your spending account.",
        ),
        (
            f"Trim dining, shopping and travel by CHF {_round_up(monthly[1])} a month",
            f"You average CHF {_discretionary_spend(record):,.0f} a month on these. "
            "Send what you save to the buffer.",
        ),
        (
            f"Reach a CHF {_round_up(target, 100):,} buffer",
            "Three months of your typical spending, the usual emergency-fund target.",
        ),
    ]


def _savings_steps(values: list[float], record: dict[str, float]) -> list[tuple[str, str]]:
    income = record["avg_income"]
    monthly = [(after - before) * income for before, after in pairwise(values)]
    return [
        (
            f"Automate a CHF {_round_up(monthly[0])} transfer to savings on payday",
            "Saving first, before spending starts, is the easiest habit to keep.",
        ),
        (
            f"Trim dining, shopping and travel by CHF {_round_up(monthly[1])} a month",
            f"You average CHF {_discretionary_spend(record):,.0f} a month on these. "
            "Move the difference to savings.",
        ),
        (
            f"Reach a {values[-1]:.0%} savings rate",
            f"About CHF {_round_up(values[-1] * income, 50):,} of your CHF {income:,.0f} monthly income.",
        ),
    ]


def _income_stability_steps(values: list[float], record: dict[str, float]) -> list[tuple[str, str]]:
    baseline = math.floor(record["avg_income"] * (1 - record["income_cv"]) / 50) * 50
    return [
        (
            f"Budget on CHF {baseline:,}, your typical low month",
            "Plan fixed costs around a weak month instead of an average one.",
        ),
        (
            "Route income above that baseline into a buffer pocket",
            "Irregular extras build a cushion instead of raising your spending.",
        ),
        (
            f"Pay yourself a steady CHF {baseline:,} a month from the buffer",
            f"A fixed monthly amount brings your income variation under {values[-1]:.0%}.",
        ),
    ]


def _debt_steps(values: list[float], record: dict[str, float]) -> list[tuple[str, str]]:
    income = record["avg_income"]
    cuts = [(before - after) * income for before, after in pairwise(values)]
    return [
        (
            f"Cut debt payments by CHF {_round_up(cuts[0])} a month",
            "Start with the highest interest rate. "
            "Refinancing or consolidating usually lowers the monthly cost.",
        ),
        (
            f"Clear another CHF {_round_up(cuts[1])} of monthly obligations",
            "Avoid new leases or credit while you pay down what you have.",
        ),
        (
            f"Get debt payments under CHF {_round_up(values[-1] * income):,} a month",
            f"That is {values[-1]:.0%} of your income, the level that earns full points.",
        ),
    ]


def _next_goal_steps(record: dict[str, float]) -> list[dict[str, object]]:
    # a quarter of the monthly free cashflow, capped near the employed pillar 3a yearly maximum
    contribution = math.floor(min(record["avg_free_cashflow"] * 0.25, 600) / 50) * 50
    return [
        {
            "title": "Keep at least three months in reserve",
            "body": f"You have {record['reserve_months']:.1f} months today. That is your safety net.",
            "points": 0,
        },
        {
            "title": "Open a pillar 3a account",
            "body": "Contributions are tax-deductible in Switzerland, up to a yearly limit.",
            "points": 0,
        },
        {
            "title": f"Automate CHF {max(contribution, 50)} a month into it",
            "body": "About a quarter of what you keep each month, invested for the long term.",
            "points": 0,
        },
    ]


_STEP_TEXT = {
    "liquidity_score": _liquidity_steps,
    "savings_score": _savings_steps,
    "income_stability_score": _income_stability_steps,
    "debt_score": _debt_steps,
}
