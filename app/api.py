from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
DATA = ROOT / "data"

from swiss_financial_health.affordability import simulate_loan_affordability

app = FastAPI(
    title="Swiss Financial Health Advisor API",
    description=(
        "Read-only access to precomputed financial health and credit readiness scores for the "
        "synthetic demo population, plus an on-demand loan affordability simulation. Educational "
        "prototype only: outputs are decision-support signals, not financial advice or a lending "
        "decision."
    ),
    version="0.1.0",
)


class UserScore(BaseModel):
    user_id: str
    financial_health_score: float
    health_band: str
    credit_readiness_score: float
    credit_readiness_band: str
    segment_label: str
    avg_income: float
    avg_net_cashflow: float
    avg_savings_rate: float
    avg_debt_to_income: float


class LoanAffordabilityRequest(BaseModel):
    loan_amount: float = Field(gt=0, description="Requested loan principal, in CHF.")
    annual_rate: float = Field(
        ge=0, le=1, description="Annual interest rate as a fraction, e.g. 0.05 for 5%."
    )
    term_years: int = Field(gt=0, le=30, description="Loan term in years.")


class LoanAffordabilityResponse(BaseModel):
    user_id: str
    monthly_payment: float
    resulting_debt_to_income: float
    projected_free_cashflow: float
    verdict: str
    explanation: str


def _load_users() -> pd.DataFrame:
    return pd.read_csv(DATA / "scored_users.csv")


def _load_recommendations() -> pd.DataFrame:
    return pd.read_csv(DATA / "recommendations.csv")


def _load_risk_flags() -> pd.DataFrame:
    return pd.read_csv(DATA / "risk_flags.csv")


def _get_user_or_404(user_id: str) -> pd.Series:
    users = _load_users()
    match = users.loc[users["user_id"] == user_id]
    if match.empty:
        raise HTTPException(status_code=404, detail=f"Unknown user_id: {user_id}")
    return match.iloc[0]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/users", response_model=list[str])
def list_users() -> list[str]:
    return _load_users()["user_id"].tolist()


@app.get("/users/{user_id}", response_model=UserScore)
def get_user(user_id: str) -> UserScore:
    record = _get_user_or_404(user_id)
    return UserScore(
        user_id=record["user_id"],
        financial_health_score=float(record["financial_health_score"]),
        health_band=record["health_band"],
        credit_readiness_score=float(record["credit_readiness_score"]),
        credit_readiness_band=record["credit_readiness_band"],
        segment_label=record["segment_label"],
        avg_income=float(record["avg_income"]),
        avg_net_cashflow=float(record["avg_net_cashflow"]),
        avg_savings_rate=float(record["avg_savings_rate"]),
        avg_debt_to_income=float(record["avg_debt_to_income"]),
    )


@app.get("/users/{user_id}/risk-flags")
def get_user_risk_flags(user_id: str) -> list[dict[str, str]]:
    _get_user_or_404(user_id)
    flags = _load_risk_flags()
    user_flags = flags.loc[flags["user_id"] == user_id, ["flag", "severity", "explanation"]]
    return user_flags.to_dict("records")


@app.get("/users/{user_id}/recommendation")
def get_user_recommendation(user_id: str) -> dict[str, str]:
    _get_user_or_404(user_id)
    recommendations = _load_recommendations()
    match = recommendations.loc[recommendations["user_id"] == user_id]
    return match.iloc[0][["priority_dimension", "recommendation", "explanation"]].to_dict()


@app.post("/users/{user_id}/loan-affordability", response_model=LoanAffordabilityResponse)
def loan_affordability(user_id: str, request: LoanAffordabilityRequest) -> LoanAffordabilityResponse:
    user = _get_user_or_404(user_id)

    result = simulate_loan_affordability(
        avg_income=float(user["avg_income"]),
        avg_net_cashflow=float(user["avg_net_cashflow"]),
        avg_debt_to_income=float(user["avg_debt_to_income"]),
        loan_amount=request.loan_amount,
        annual_rate=request.annual_rate,
        term_years=request.term_years,
    )
    return LoanAffordabilityResponse(
        user_id=user_id,
        monthly_payment=result.monthly_payment,
        resulting_debt_to_income=result.resulting_debt_to_income,
        projected_free_cashflow=result.projected_free_cashflow,
        verdict=result.verdict,
        explanation=result.explanation,
    )
