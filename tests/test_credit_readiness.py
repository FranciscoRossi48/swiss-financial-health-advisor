import pandas as pd

from swiss_financial_health.credit_readiness import (
    build_risk_flags,
    compute_credit_readiness,
    risk_flags_for_user,
)


def _record(**overrides):
    record = {
        "user_id": "U1",
        "avg_income": 5000.0,
        "avg_net_cashflow": 500.0,
        "income_cv": 0.10,
        "avg_debt_to_income": 0.05,
        "avg_savings_rate": 0.15,
        "avg_discretionary_ratio": 0.10,
    }
    record.update(overrides)
    return record


def test_no_flags_for_a_healthy_profile():
    assert risk_flags_for_user(_record()) == []


def test_high_debt_burden_flag_above_threshold():
    flags = risk_flags_for_user(_record(avg_debt_to_income=0.30))
    assert any(f["flag"] == "High debt burden" and f["severity"] == "high" for f in flags)


def test_elevated_debt_burden_flag_between_thresholds():
    flags = risk_flags_for_user(_record(avg_debt_to_income=0.20))
    assert any(f["flag"] == "Elevated debt burden" and f["severity"] == "medium" for f in flags)


def test_negative_free_cashflow_flag_when_expenses_exceed_income():
    flags = risk_flags_for_user(_record(avg_net_cashflow=-100.0))
    assert any(f["flag"] == "Negative free cashflow" for f in flags)


def test_zero_income_does_not_raise_division_error():
    flags = risk_flags_for_user(_record(avg_income=0.0, avg_net_cashflow=0.0))
    assert any(f["flag"] == "Thin cashflow buffer" for f in flags)


def test_low_savings_discipline_flag():
    flags = risk_flags_for_user(_record(avg_savings_rate=0.02))
    assert any(f["flag"] == "Low savings discipline" for f in flags)


def test_high_discretionary_spend_flag():
    flags = risk_flags_for_user(_record(avg_discretionary_ratio=0.40))
    assert any(f["flag"] == "High discretionary spend" for f in flags)


def test_build_risk_flags_reports_no_major_flags_when_none_triggered():
    df = build_risk_flags(pd.DataFrame([_record()]))
    assert len(df) == 1
    assert df.iloc[0]["flag"] == "No major risk flags"
    assert df.iloc[0]["severity"] == "low"


def test_build_risk_flags_expands_one_row_per_flag():
    df = build_risk_flags(pd.DataFrame([_record(avg_debt_to_income=0.30, income_cv=0.35)]))
    assert len(df) == 2
    assert set(df["flag"]) == {"High debt burden", "Highly variable income"}


def test_compute_credit_readiness_is_bounded_between_zero_and_hundred():
    scored = compute_credit_readiness(pd.DataFrame([_record()]))
    assert 0 <= scored["credit_readiness_score"].iloc[0] <= 100
    assert scored["credit_readiness_band"].iloc[0] in {"not ready", "needs improvement", "moderate", "ready"}


def test_compute_credit_readiness_handles_zero_income_without_error():
    scored = compute_credit_readiness(pd.DataFrame([_record(avg_income=0.0)]))
    assert not scored["credit_readiness_score"].isna().any()
