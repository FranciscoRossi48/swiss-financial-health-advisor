import pandas as pd
import pytest

from swiss_financial_health.features import build_monthly_features, build_user_summary, safe_ratio


def _transactions():
    return pd.DataFrame(
        [
            {
                "user_id": "U1",
                "date": "2025-01-05",
                "category": "salary",
                "transaction_type": "income",
                "amount_chf": 1000.0,
                "profile": "balanced_user",
            },
            {
                "user_id": "U1",
                "date": "2025-01-10",
                "category": "rent",
                "transaction_type": "expense",
                "amount_chf": 400.0,
                "profile": "balanced_user",
            },
            {
                "user_id": "U1",
                "date": "2025-01-15",
                "category": "shopping",
                "transaction_type": "expense",
                "amount_chf": 100.0,
                "profile": "balanced_user",
            },
            {
                "user_id": "U1",
                "date": "2025-01-20",
                "category": "debt_payment",
                "transaction_type": "expense",
                "amount_chf": 50.0,
                "profile": "balanced_user",
            },
            {
                "user_id": "U1",
                "date": "2025-01-25",
                "category": "savings_transfer",
                "transaction_type": "savings",
                "amount_chf": 150.0,
                "profile": "balanced_user",
            },
            {
                "user_id": "U1",
                "date": "2025-02-05",
                "category": "salary",
                "transaction_type": "income",
                "amount_chf": 1000.0,
                "profile": "balanced_user",
            },
            {
                "user_id": "U1",
                "date": "2025-02-10",
                "category": "rent",
                "transaction_type": "expense",
                "amount_chf": 400.0,
                "profile": "balanced_user",
            },
        ]
    )


def test_build_monthly_features_aggregates_categories_correctly():
    monthly = build_monthly_features(_transactions())

    jan = monthly.loc[monthly["month"] == pd.Timestamp("2025-01-01")].iloc[0]
    assert jan["income"] == 1000.0
    assert jan["expense"] == 550.0
    assert jan["savings"] == 150.0
    assert jan["debt_payments"] == 50.0
    assert jan["discretionary_spend"] == 100.0
    assert jan["net_cashflow"] == pytest.approx(1000.0 - 550.0 - 150.0)
    assert jan["debt_to_income"] == pytest.approx(50.0 / 1000.0)
    assert jan["discretionary_ratio"] == pytest.approx(100.0 / 1000.0)


def test_build_monthly_features_fills_missing_debt_and_discretionary_with_zero():
    monthly = build_monthly_features(_transactions())
    feb = monthly.loc[monthly["month"] == pd.Timestamp("2025-02-01")].iloc[0]

    assert feb["debt_payments"] == 0.0
    assert feb["discretionary_spend"] == 0.0
    assert feb["net_cashflow"] == pytest.approx(1000.0 - 400.0)


def test_build_monthly_features_computes_income_coefficient_of_variation():
    monthly = build_monthly_features(_transactions())
    assert monthly["income_cv"].nunique() == 1
    assert monthly["income_cv"].iloc[0] == pytest.approx(0.0)


def test_build_user_summary_averages_monthly_features():
    monthly = build_monthly_features(_transactions())
    summary = build_user_summary(monthly)

    assert len(summary) == 1
    row = summary.iloc[0]
    assert row["user_id"] == "U1"
    assert row["avg_income"] == pytest.approx(1000.0)
    assert row["avg_expense"] == pytest.approx((550.0 + 400.0) / 2)


def test_safe_ratio_returns_zero_on_zero_denominator():
    numerator = pd.Series([10.0, 5.0])
    denominator = pd.Series([0.0, 10.0])
    result = safe_ratio(numerator, denominator)
    assert result.tolist() == [0.0, 0.5]


def test_safe_ratio_clips_negative_results_to_zero():
    numerator = pd.Series([-10.0])
    denominator = pd.Series([5.0])
    result = safe_ratio(numerator, denominator)
    assert result.tolist() == [0.0]
