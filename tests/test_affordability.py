import pytest

from swiss_financial_health.affordability import (
    AFFORDABILITY_CEILING,
    monthly_payment_for_loan,
    simulate_loan_affordability,
)


def test_monthly_payment_for_loan_matches_known_amortization_value():
    # CHF 10,000 at 5% APR over 2 years has a well-known standard amortization payment.
    payment = monthly_payment_for_loan(10_000, 0.05, 2)
    assert payment == pytest.approx(438.71, abs=0.01)


def test_monthly_payment_for_loan_handles_zero_rate():
    payment = monthly_payment_for_loan(12_000, 0.0, 2)
    assert payment == pytest.approx(500.0)


def test_monthly_payment_for_loan_is_zero_for_non_positive_principal_or_term():
    assert monthly_payment_for_loan(0, 0.05, 2) == 0.0
    assert monthly_payment_for_loan(10_000, 0.05, 0) == 0.0


def test_simulate_loan_affordability_marks_small_loan_as_affordable():
    result = simulate_loan_affordability(
        avg_income=6000.0,
        avg_net_cashflow=1000.0,
        avg_debt_to_income=0.05,
        loan_amount=5000.0,
        annual_rate=0.05,
        term_years=3,
    )
    assert result.verdict == "affordable"
    assert result.resulting_debt_to_income <= AFFORDABILITY_CEILING
    assert result.projected_free_cashflow >= 0


def test_simulate_loan_affordability_marks_oversized_loan_as_not_recommended():
    result = simulate_loan_affordability(
        avg_income=4000.0,
        avg_net_cashflow=200.0,
        avg_debt_to_income=0.20,
        loan_amount=100_000.0,
        annual_rate=0.08,
        term_years=3,
    )
    assert result.verdict == "not recommended"
    assert result.resulting_debt_to_income > AFFORDABILITY_CEILING


def test_simulate_loan_affordability_marks_marginal_when_within_ceiling_but_cashflow_negative():
    result = simulate_loan_affordability(
        avg_income=6000.0,
        avg_net_cashflow=100.0,
        avg_debt_to_income=0.10,
        loan_amount=15_000.0,
        annual_rate=0.06,
        term_years=2,
    )
    assert result.resulting_debt_to_income <= AFFORDABILITY_CEILING
    assert result.projected_free_cashflow < 0
    assert result.verdict == "marginal"


def test_simulate_loan_affordability_handles_zero_income_without_error():
    result = simulate_loan_affordability(
        avg_income=0.0,
        avg_net_cashflow=0.0,
        avg_debt_to_income=0.0,
        loan_amount=5000.0,
        annual_rate=0.05,
        term_years=2,
    )
    assert result.verdict == "not recommended"
