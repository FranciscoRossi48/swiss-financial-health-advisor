import pandas as pd

from swiss_financial_health.scoring import (
    compute_financial_health_score,
    scale_higher_is_better,
    scale_lower_is_better,
)


def test_scale_higher_is_better_clips_to_zero_and_hundred():
    values = pd.Series([-1.0, 0.25, 0.5, 0.75, 2.0])
    result = scale_higher_is_better(values, good=0.25, excellent=0.75)
    assert result.tolist() == [0.0, 0.0, 50.0, 100.0, 100.0]


def test_scale_lower_is_better_clips_to_zero_and_hundred():
    values = pd.Series([0.0, 0.05, 0.15, 0.25, 1.0])
    result = scale_lower_is_better(values, good=0.05, poor=0.25)
    assert result.tolist() == [100.0, 100.0, 50.0, 0.0, 0.0]


def test_scale_functions_treat_nan_as_worst_case():
    values = pd.Series([float("nan")])
    assert scale_higher_is_better(values, good=0.1, excellent=0.5).tolist() == [0.0]
    assert scale_lower_is_better(values, good=0.1, poor=0.5).tolist() == [0.0]


def _summary(**overrides):
    row = {
        "user_id": "U1",
        "avg_net_cashflow": 500.0,
        "avg_expense": 2000.0,
        "income_cv": 0.10,
        "avg_savings_rate": 0.10,
        "avg_debt_to_income": 0.05,
    }
    row.update(overrides)
    return pd.DataFrame([row])


def test_compute_financial_health_score_is_bounded_between_zero_and_hundred():
    scored = compute_financial_health_score(_summary())
    assert 0 <= scored["financial_health_score"].iloc[0] <= 100


def test_compute_financial_health_score_handles_zero_expense_without_error():
    scored = compute_financial_health_score(_summary(avg_expense=0.0))
    assert scored["liquidity_score"].iloc[0] == 0.0
    assert not scored["financial_health_score"].isna().any()


def test_health_band_is_strong_for_best_case_profile():
    scored = compute_financial_health_score(
        _summary(
            avg_net_cashflow=2000.0,
            avg_expense=2000.0,
            income_cv=0.02,
            avg_savings_rate=0.30,
            avg_debt_to_income=0.0,
        )
    )
    assert scored["health_band"].iloc[0] == "strong"


def test_health_band_is_critical_for_worst_case_profile():
    scored = compute_financial_health_score(
        _summary(
            avg_net_cashflow=-500.0,
            avg_expense=2000.0,
            income_cv=0.50,
            avg_savings_rate=0.0,
            avg_debt_to_income=0.40,
        )
    )
    assert scored["health_band"].iloc[0] == "critical"
