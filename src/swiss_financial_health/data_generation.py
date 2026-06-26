from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class UserProfile:
    name: str
    income_mean: float
    income_volatility: float
    fixed_expense_ratio: float
    discretionary_ratio: float
    debt_ratio: float
    savings_bias: float


PROFILES = [
    UserProfile("stable_saver", 7200, 0.08, 0.42, 0.18, 0.04, 0.22),
    UserProfile("balanced_user", 6200, 0.13, 0.47, 0.25, 0.08, 0.10),
    UserProfile("high_discretionary", 6800, 0.12, 0.43, 0.38, 0.07, 0.02),
    UserProfile("variable_income", 5900, 0.32, 0.45, 0.23, 0.09, 0.06),
    UserProfile("debt_pressure", 6400, 0.16, 0.48, 0.22, 0.24, -0.03),
]

EXPENSE_CATEGORIES = {
    "rent": "fixed",
    "groceries": "essential",
    "transport": "essential",
    "insurance": "fixed",
    "restaurants": "discretionary",
    "shopping": "discretionary",
    "travel": "discretionary",
    "subscriptions": "discretionary",
    "debt_payment": "debt",
}


def generate_synthetic_transactions(
    n_users: int = 120,
    start: str = "2025-01-01",
    periods: int = 12,
    seed: int = 42,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    months = pd.date_range(start=start, periods=periods, freq="MS")
    rows: list[dict[str, object]] = []

    for user_idx in range(1, n_users + 1):
        profile = PROFILES[(user_idx - 1) % len(PROFILES)]
        user_id = f"U{user_idx:04d}"

        for month in months:
            income = max(1200, rng.normal(profile.income_mean, profile.income_mean * profile.income_volatility))
            income_date = month + pd.Timedelta(days=int(rng.integers(0, 4)))
            rows.append(
                {
                    "user_id": user_id,
                    "date": income_date.date(),
                    "category": "salary",
                    "transaction_type": "income",
                    "amount_chf": round(income, 2),
                    "profile": profile.name,
                }
            )

            if profile.name == "variable_income" and rng.random() < 0.35:
                freelance_income = rng.uniform(300, 1800)
                rows.append(
                    {
                        "user_id": user_id,
                        "date": (month + pd.Timedelta(days=int(rng.integers(5, 25)))).date(),
                        "category": "freelance",
                        "transaction_type": "income",
                        "amount_chf": round(freelance_income, 2),
                        "profile": profile.name,
                    }
                )

            expense_plan = {
                "rent": income * profile.fixed_expense_ratio * rng.uniform(0.72, 0.82),
                "insurance": income * profile.fixed_expense_ratio * rng.uniform(0.10, 0.16),
                "groceries": income * rng.uniform(0.09, 0.15),
                "transport": income * rng.uniform(0.04, 0.08),
                "restaurants": income * profile.discretionary_ratio * rng.uniform(0.20, 0.34),
                "shopping": income * profile.discretionary_ratio * rng.uniform(0.24, 0.40),
                "travel": income * profile.discretionary_ratio * rng.uniform(0.10, 0.26),
                "subscriptions": income * profile.discretionary_ratio * rng.uniform(0.05, 0.10),
                "debt_payment": income * profile.debt_ratio * rng.uniform(0.80, 1.20),
            }

            planned_savings = max(0, income * (profile.savings_bias + rng.normal(0, 0.025)))
            expense_plan["savings_transfer"] = planned_savings

            for category, monthly_amount in expense_plan.items():
                if monthly_amount <= 0:
                    continue
                tx_count = 1 if category in {"rent", "insurance", "debt_payment", "savings_transfer"} else int(rng.integers(2, 8))
                splits = rng.dirichlet(np.ones(tx_count)) * monthly_amount
                tx_type = "savings" if category == "savings_transfer" else "expense"
                for amount in splits:
                    rows.append(
                        {
                            "user_id": user_id,
                            "date": (month + pd.Timedelta(days=int(rng.integers(1, 28)))).date(),
                            "category": category,
                            "transaction_type": tx_type,
                            "amount_chf": round(float(amount), 2),
                            "profile": profile.name,
                        }
                    )

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values(["user_id", "date"]).reset_index(drop=True)


def demo_generation_date() -> date:
    return date.today()
