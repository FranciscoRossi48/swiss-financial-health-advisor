import pytest

from swiss_financial_health.explanations import dimension_driver, dimension_target, points_left
from swiss_financial_health.scoring import SCORE_WEIGHTS


def _record(**overrides):
    record = {
        "reserve_months": 1.5,
        "avg_expense": 5000.0,
        "avg_free_cashflow": 600.0,
        "income_cv": 0.12,
        "avg_income": 6000.0,
        "avg_savings_rate": 0.15,
        "avg_debt_to_income": 0.08,
        "liquidity_score": 25.0,
        "income_stability_score": 92.0,
        "savings_score": 33.3,
        "debt_score": 85.0,
    }
    record.update(overrides)
    return record


@pytest.mark.parametrize("dimension", list(SCORE_WEIGHTS))
def test_every_dimension_has_a_driver_and_a_target(dimension):
    assert dimension_driver(dimension, _record())
    assert dimension_target(dimension, _record())


def test_target_states_the_points_still_available():
    assert points_left("liquidity_score", _record()) == pytest.approx(22.5)
    assert dimension_target("liquidity_score", _record()).endswith("+22.5 pts")


def test_target_acknowledges_full_points():
    assert dimension_target("debt_score", _record(debt_score=100.0)).startswith("Full points")


def test_liquidity_driver_explains_negative_reserves():
    driver = dimension_driver("liquidity_score", _record(reserve_months=-0.5))
    assert "CHF 2,500 more than came in" in driver


def test_unknown_dimension_is_rejected():
    with pytest.raises(ValueError):
        dimension_driver("unknown_score", _record())
