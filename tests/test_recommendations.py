import pandas as pd
import pytest

from swiss_financial_health.recommendations import (
    explanation_for_dimension,
    generate_recommendations,
    recommendation_for_dimension,
)


def _record(**overrides):
    record = {
        "user_id": "U1",
        "liquidity_score": 80.0,
        "income_stability_score": 80.0,
        "savings_score": 80.0,
        "debt_score": 80.0,
        "avg_net_cashflow": 500.0,
        "reserve_months": 2.0,
        "income_cv": 0.10,
        "avg_savings_rate": 0.15,
        "avg_debt_to_income": 0.05,
    }
    record.update(overrides)
    return record


def test_generate_recommendations_targets_the_weakest_dimension():
    df = pd.DataFrame([_record(debt_score=10.0)])
    result = generate_recommendations(df)
    assert result.iloc[0]["priority_dimension"] == "debt exposure"


def test_generate_recommendations_suggests_a_next_goal_when_every_dimension_is_strong():
    df = pd.DataFrame([_record(liquidity_score=100.0, income_stability_score=90.0, savings_score=85.0)])
    result = generate_recommendations(df).iloc[0]
    assert result["priority_dimension"] == "next goal"
    assert "2.0 months" in result["explanation"]


def test_generate_recommendations_still_targets_a_weak_dimension_below_the_threshold():
    df = pd.DataFrame([_record(savings_score=79.9)])
    result = generate_recommendations(df)
    assert result.iloc[0]["priority_dimension"] == "savings capacity"


def test_generate_recommendations_breaks_ties_by_dimension_order():
    df = pd.DataFrame([_record(liquidity_score=10.0, debt_score=10.0)])
    result = generate_recommendations(df)
    assert result.iloc[0]["priority_dimension"] == "liquidity"


@pytest.mark.parametrize(
    "dimension",
    ["liquidity_score", "income_stability_score", "savings_score", "debt_score"],
)
def test_recommendation_and_explanation_exist_for_every_dimension(dimension):
    record = _record()
    assert recommendation_for_dimension(dimension, record)
    assert explanation_for_dimension(dimension, record)


def test_recommendation_for_dimension_rejects_unknown_dimension():
    with pytest.raises(ValueError):
        recommendation_for_dimension("unknown_score", _record())
