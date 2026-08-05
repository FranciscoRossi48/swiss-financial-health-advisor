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
