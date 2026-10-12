import pytest
from api import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_users_returns_a_non_empty_list():
    response = client.get("/users")
    assert response.status_code == 200
    users = response.json()
    assert isinstance(users, list)
    assert len(users) > 0


def test_get_user_returns_scores_for_a_known_user():
    user_id = client.get("/users").json()[0]
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == user_id
    assert 0 <= body["financial_health_score"] <= 100
    assert 0 <= body["credit_readiness_score"] <= 100


def test_get_user_returns_404_for_unknown_user():
    response = client.get("/users/does-not-exist")
    assert response.status_code == 404


def test_get_user_risk_flags_returns_404_for_unknown_user():
    response = client.get("/users/does-not-exist/risk-flags")
    assert response.status_code == 404


def test_get_user_risk_flags_returns_a_list():
    user_id = client.get("/users").json()[0]
    response = client.get(f"/users/{user_id}/risk-flags")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_user_recommendation_returns_expected_fields():
    user_id = client.get("/users").json()[0]
    response = client.get(f"/users/{user_id}/recommendation")
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"priority_dimension", "recommendation", "explanation"}


def test_loan_affordability_returns_a_verdict_for_a_known_user():
    user_id = client.get("/users").json()[0]
    response = client.post(
        f"/users/{user_id}/loan-affordability",
        json={"loan_amount": 5000, "annual_rate": 0.05, "term_years": 3},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == user_id
    assert body["verdict"] in {"affordable", "marginal", "not recommended"}


def test_loan_affordability_returns_404_for_unknown_user():
    response = client.post(
        "/users/does-not-exist/loan-affordability",
        json={"loan_amount": 5000, "annual_rate": 0.05, "term_years": 3},
    )
    assert response.status_code == 404


@pytest.mark.parametrize(
    "payload",
    [
        {"loan_amount": -100, "annual_rate": 0.05, "term_years": 3},
        {"loan_amount": 5000, "annual_rate": 1.5, "term_years": 3},
        {"loan_amount": 5000, "annual_rate": 0.05, "term_years": 0},
    ],
)
def test_loan_affordability_rejects_invalid_input(payload):
    user_id = client.get("/users").json()[0]
    response = client.post(f"/users/{user_id}/loan-affordability", json=payload)
    assert response.status_code == 422


def test_demo_users_returns_one_customer_per_segment():
    response = client.get("/demo-users")
    assert response.status_code == 200
    segments = [user["segment_label"] for user in response.json()]
    assert len(segments) == len(set(segments)) > 0


def test_get_user_transactions_are_signed_and_newest_first():
    user_id = client.get("/users").json()[0]
    response = client.get(f"/users/{user_id}/transactions", params={"limit": 20})
    assert response.status_code == 200
    transactions = response.json()
    assert len(transactions) == 20
    dates = [tx["date"] for tx in transactions]
    assert dates == sorted(dates, reverse=True)
    for tx in transactions:
        assert (tx["amount_chf"] > 0) == (tx["transaction_type"] == "income")


def test_get_user_transactions_filters_by_type_and_month():
    user_id = client.get("/users").json()[0]
    response = client.get(
        f"/users/{user_id}/transactions", params={"type": "income", "month": "2025-03", "limit": 500}
    )
    assert response.status_code == 200
    transactions = response.json()
    assert transactions
    assert all(tx["transaction_type"] == "income" and tx["date"].startswith("2025-03") for tx in transactions)


def test_get_user_transactions_rejects_malformed_month():
    user_id = client.get("/users").json()[0]
    response = client.get(f"/users/{user_id}/transactions", params={"month": "March"})
    assert response.status_code == 422


def test_get_user_overview_spending_matches_its_categories():
    user_id = client.get("/users").json()[0]
    response = client.get(f"/users/{user_id}/overview")
    assert response.status_code == 200
    body = response.json()
    category_total = sum(item["amount_chf"] for item in body["spending_by_category"])
    assert category_total == pytest.approx(body["month_spending"], abs=0.05)


def test_get_user_monthly_is_chronological():
    user_id = client.get("/users").json()[0]
    response = client.get(f"/users/{user_id}/monthly")
    assert response.status_code == 200
    months = [row["month"] for row in response.json()]
    assert months == sorted(months)


def test_get_user_health_weights_reproduce_the_scores():
    user_id = client.get("/users").json()[0]
    response = client.get(f"/users/{user_id}/health")
    assert response.status_code == 200
    body = response.json()
    for key in ("financial_health", "credit_readiness"):
        breakdown = body[key]
        weighted = sum(dim["score"] * dim["weight"] for dim in breakdown["dimensions"])
        assert weighted == pytest.approx(breakdown["score"], abs=0.1)
    assert body["segment"]["description"]


@pytest.mark.parametrize("path", ["transactions", "overview", "monthly", "health"])
def test_new_user_endpoints_return_404_for_unknown_user(path):
    response = client.get(f"/users/does-not-exist/{path}")
    assert response.status_code == 404
