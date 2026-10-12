from __future__ import annotations

import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Literal

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
DATA = ROOT / "data"

from swiss_financial_health.affordability import simulate_loan_affordability
from swiss_financial_health.credit_readiness import CREDIT_READINESS_WEIGHTS
from swiss_financial_health.presentation import SEGMENT_DESCRIPTIONS, category_label, merchant_name
from swiss_financial_health.scoring import SCORE_WEIGHTS

app = FastAPI(
    title="Swiss Financial Health Advisor API",
    description=(
        "Read-only access to precomputed financial health and credit readiness scores for the "
        "synthetic demo population, plus an on-demand loan affordability simulation. Educational "
        "prototype only: outputs are decision-support signals, not financial advice or a lending "
        "decision."
    ),
    version="0.2.0",
)

# The data behind this API is synthetic and read-only, so any origin may read it by default.
# Set PULSE_ALLOWED_ORIGINS (comma-separated) to lock it down to the deployed frontend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("PULSE_ALLOWED_ORIGINS", "*").split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

DIMENSION_LABELS = {
    "liquidity_score": "Liquidity",
    "income_stability_score": "Income stability",
    "savings_score": "Savings",
    "debt_score": "Debt",
    "income_reliability_score": "Income reliability",
    "debt_capacity_score": "Debt capacity",
    "cashflow_resilience_score": "Cashflow resilience",
    "savings_discipline_score": "Savings discipline",
    "spending_control_score": "Spending control",
}

SEGMENT_COMPARISON_METRICS = {
    "avg_savings_rate": "Savings rate",
    "avg_debt_to_income": "Debt-to-income",
    "avg_discretionary_ratio": "Discretionary spending",
    "income_cv": "Income variability",
}


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


class Transaction(BaseModel):
    date: str
    category: str
    category_label: str
    merchant: str
    transaction_type: str
    amount_chf: float = Field(description="Signed amount: positive for money in, negative for money out.")


class CategorySpend(BaseModel):
    category: str
    category_label: str
    amount_chf: float


class AccountOverview(BaseModel):
    user_id: str
    balance_chf: float
    month: str
    month_income: float
    month_spending: float
    month_savings: float
    previous_month_spending: float
    spending_by_category: list[CategorySpend]


class MonthlySummary(BaseModel):
    month: str
    income: float
    expense: float
    savings: float
    net_cashflow: float


class ScoreDimension(BaseModel):
    key: str
    label: str
    score: float
    weight: float


class ScoreBreakdown(BaseModel):
    score: float
    band: str
    dimensions: list[ScoreDimension]


class SegmentComparison(BaseModel):
    metric: str
    label: str
    user_value: float
    segment_value: float


class SegmentProfile(BaseModel):
    label: str
    description: str
    comparison: list[SegmentComparison]


class HealthProfile(BaseModel):
    user_id: str
    financial_health: ScoreBreakdown
    credit_readiness: ScoreBreakdown
    segment: SegmentProfile


class DemoUser(BaseModel):
    user_id: str
    segment_label: str
    financial_health_score: float
    health_band: str


@lru_cache(maxsize=1)
def _load_users() -> pd.DataFrame:
    return pd.read_csv(DATA / "scored_users.csv")


@lru_cache(maxsize=1)
def _load_recommendations() -> pd.DataFrame:
    return pd.read_csv(DATA / "recommendations.csv")


@lru_cache(maxsize=1)
def _load_risk_flags() -> pd.DataFrame:
    return pd.read_csv(DATA / "risk_flags.csv")


@lru_cache(maxsize=1)
def _load_transactions() -> pd.DataFrame:
    transactions = pd.read_csv(DATA / "synthetic_transactions.csv")
    sign = transactions["transaction_type"].map({"income": 1, "expense": -1, "savings": -1})
    transactions["signed_amount"] = transactions["amount_chf"] * sign
    return transactions


@lru_cache(maxsize=1)
def _load_monthly() -> pd.DataFrame:
    return pd.read_csv(DATA / "user_monthly_features.csv")


@lru_cache(maxsize=1)
def _load_centroids() -> pd.DataFrame:
    return pd.read_csv(DATA / "segment_centroids.csv")


def _breakdown(record: pd.Series, score_col: str, band_col: str, weights: dict[str, float]) -> ScoreBreakdown:
    return ScoreBreakdown(
        score=float(record[score_col]),
        band=record[band_col],
        dimensions=[
            ScoreDimension(key=col, label=DIMENSION_LABELS[col], score=float(record[col]), weight=weight)
            for col, weight in weights.items()
        ],
    )


def _get_user_or_404(user_id: str) -> pd.Series:
    users = _load_users()
    match = users.loc[users["user_id"] == user_id]
    if match.empty:
        raise HTTPException(status_code=404, detail=f"Unknown user_id: {user_id}")
    return match.iloc[0]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/demo-users", response_model=list[DemoUser])
def list_demo_users() -> list[DemoUser]:
    """One representative customer per segment: the member whose score is closest to the segment median."""
    users = _load_users()
    picks = []
    for _, members in users.groupby("segment_label"):
        distance = (members["financial_health_score"] - members["financial_health_score"].median()).abs()
        picks.append(members.loc[distance.idxmin()])
    picks.sort(key=lambda record: -record["financial_health_score"])
    return [
        DemoUser(
            user_id=record["user_id"],
            segment_label=record["segment_label"],
            financial_health_score=float(record["financial_health_score"]),
            health_band=record["health_band"],
        )
        for record in picks
    ]


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


@app.get("/users/{user_id}/transactions", response_model=list[Transaction])
def get_user_transactions(
    user_id: str,
    transaction_type: Literal["income", "expense", "savings"] | None = Query(default=None, alias="type"),
    month: str | None = Query(
        default=None, pattern=r"^\d{4}-\d{2}$", description="Filter by month, YYYY-MM."
    ),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[Transaction]:
    _get_user_or_404(user_id)
    transactions = _load_transactions()
    user_tx = transactions.loc[transactions["user_id"] == user_id]
    if transaction_type:
        user_tx = user_tx.loc[user_tx["transaction_type"] == transaction_type]
    if month:
        user_tx = user_tx.loc[user_tx["date"].str.startswith(month)]
    page = user_tx.sort_values("date", ascending=False, kind="stable").iloc[offset : offset + limit]
    return [
        Transaction(
            date=row.date,
            category=row.category,
            category_label=category_label(row.category),
            merchant=merchant_name(row.category),
            transaction_type=row.transaction_type,
            amount_chf=round(float(row.signed_amount), 2),
        )
        for row in page.itertuples()
    ]


@app.get("/users/{user_id}/overview", response_model=AccountOverview)
def get_user_overview(user_id: str) -> AccountOverview:
    _get_user_or_404(user_id)
    transactions = _load_transactions()
    user_tx = transactions.loc[transactions["user_id"] == user_id]
    months = user_tx["date"].str[:7]
    latest_month = months.max()
    months_sorted = sorted(months.unique())
    previous_month = months_sorted[-2] if len(months_sorted) > 1 else latest_month

    current = user_tx.loc[months == latest_month]
    expenses = current.loc[current["transaction_type"] == "expense"]
    previous_expenses = user_tx.loc[(months == previous_month) & (user_tx["transaction_type"] == "expense")]
    by_category = expenses.groupby("category")["amount_chf"].sum().sort_values(ascending=False)

    return AccountOverview(
        user_id=user_id,
        balance_chf=round(float(user_tx["signed_amount"].sum()), 2),
        month=latest_month,
        month_income=round(
            float(current.loc[current["transaction_type"] == "income", "amount_chf"].sum()), 2
        ),
        month_spending=round(float(expenses["amount_chf"].sum()), 2),
        month_savings=round(
            float(current.loc[current["transaction_type"] == "savings", "amount_chf"].sum()), 2
        ),
        previous_month_spending=round(float(previous_expenses["amount_chf"].sum()), 2),
        spending_by_category=[
            CategorySpend(
                category=category, category_label=category_label(category), amount_chf=round(amount, 2)
            )
            for category, amount in by_category.items()
        ],
    )


@app.get("/users/{user_id}/monthly", response_model=list[MonthlySummary])
def get_user_monthly(user_id: str) -> list[MonthlySummary]:
    _get_user_or_404(user_id)
    monthly = _load_monthly()
    user_monthly = monthly.loc[monthly["user_id"] == user_id].sort_values("month")
    return [
        MonthlySummary(
            month=row.month[:7],
            income=round(row.income, 2),
            expense=round(row.expense, 2),
            savings=round(row.savings, 2),
            net_cashflow=round(row.net_cashflow, 2),
        )
        for row in user_monthly.itertuples()
    ]


@app.get("/users/{user_id}/health", response_model=HealthProfile)
def get_user_health(user_id: str) -> HealthProfile:
    user = _get_user_or_404(user_id)
    centroids = _load_centroids()
    centroid = centroids.loc[centroids["segment_label"] == user["segment_label"]].iloc[0]
    return HealthProfile(
        user_id=user_id,
        financial_health=_breakdown(user, "financial_health_score", "health_band", SCORE_WEIGHTS),
        credit_readiness=_breakdown(
            user, "credit_readiness_score", "credit_readiness_band", CREDIT_READINESS_WEIGHTS
        ),
        segment=SegmentProfile(
            label=user["segment_label"],
            description=SEGMENT_DESCRIPTIONS.get(user["segment_label"], ""),
            comparison=[
                SegmentComparison(
                    metric=metric,
                    label=label,
                    user_value=float(user[metric]),
                    segment_value=float(centroid[metric]),
                )
                for metric, label in SEGMENT_COMPARISON_METRICS.items()
            ],
        ),
    )


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
