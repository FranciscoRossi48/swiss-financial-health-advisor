from __future__ import annotations

from dataclasses import dataclass

# Swiss mortgage/consumer credit affordability guideline: total debt service should not
# exceed roughly one third of gross income (the "Tragbarkeit" rule of thumb). See
# docs/scoring-methodology.md for how this anchors the credit readiness thresholds too.
AFFORDABILITY_CEILING = 0.33


@dataclass(frozen=True)
class LoanAffordabilityResult:
    monthly_payment: float
    resulting_debt_to_income: float
    projected_free_cashflow: float
    verdict: str
    explanation: str


def monthly_payment_for_loan(principal: float, annual_rate: float, term_years: int) -> float:
    """Standard fixed-rate amortization payment. Assumes principal, rate, term are non-negative."""
    if principal <= 0 or term_years <= 0:
        return 0.0

    n_payments = term_years * 12
    monthly_rate = annual_rate / 12
    if monthly_rate == 0:
        return principal / n_payments

    growth = (1 + monthly_rate) ** n_payments
    return principal * monthly_rate * growth / (growth - 1)


def simulate_loan_affordability(
    avg_income: float,
    avg_net_cashflow: float,
    avg_debt_to_income: float,
    loan_amount: float,
    annual_rate: float,
    term_years: int,
) -> LoanAffordabilityResult:
    """Estimate whether a hypothetical new loan fits a user's current financial profile.

    This is a decision-support simulation, not a lending decision: it applies the same
    transparent affordability ceiling used elsewhere in the prototype to a user-chosen
    loan amount, rate, and term.
    """
    monthly_payment = monthly_payment_for_loan(loan_amount, annual_rate, term_years)
    current_debt_payments = avg_debt_to_income * avg_income
    resulting_debt_to_income = (current_debt_payments + monthly_payment) / avg_income if avg_income else 1.0
    projected_free_cashflow = avg_net_cashflow - monthly_payment

    if resulting_debt_to_income > AFFORDABILITY_CEILING:
        verdict = "not recommended"
        explanation = (
            f"Total debt service would reach {resulting_debt_to_income:.1%} of income, "
            f"above the {AFFORDABILITY_CEILING:.0%} affordability guideline."
        )
    elif projected_free_cashflow < 0:
        verdict = "marginal"
        explanation = (
            f"Debt service stays within the {AFFORDABILITY_CEILING:.0%} affordability guideline, "
            "but projected free cashflow turns negative after this payment."
        )
    else:
        verdict = "affordable"
        explanation = (
            f"Total debt service would be {resulting_debt_to_income:.1%} of income, within the "
            f"{AFFORDABILITY_CEILING:.0%} affordability guideline, with CHF {projected_free_cashflow:.0f} "
            "of free cashflow remaining."
        )

    return LoanAffordabilityResult(
        monthly_payment=round(monthly_payment, 2),
        resulting_debt_to_income=round(resulting_debt_to_income, 4),
        projected_free_cashflow=round(projected_free_cashflow, 2),
        verdict=verdict,
        explanation=explanation,
    )
