import pandas as pd
import pytest

from swiss_financial_health.features import build_monthly_features
from swiss_financial_health.validation import validate_transactions


def _valid_transaction(**overrides):
    row = {
        "user_id": "U1",
        "date": "2025-01-05",
        "category": "salary",
        "transaction_type": "income",
        "amount_chf": 1000.0,
        "profile": "balanced_user",
    }
    row.update(overrides)
    return pd.DataFrame([row])


def test_validate_transactions_accepts_a_well_formed_dataframe():
    validate_transactions(_valid_transaction())


def test_validate_transactions_rejects_empty_dataframe():
    with pytest.raises(ValueError, match="empty"):
        validate_transactions(pd.DataFrame())


def test_validate_transactions_rejects_missing_columns():
    df = _valid_transaction().drop(columns=["amount_chf"])
    with pytest.raises(ValueError, match="missing required columns"):
        validate_transactions(df)


def test_validate_transactions_rejects_missing_user_id():
    df = _valid_transaction(user_id=None)
    with pytest.raises(ValueError, match="missing user_id"):
        validate_transactions(df)


def test_validate_transactions_rejects_unparseable_dates():
    df = _valid_transaction(date="not-a-date")
    with pytest.raises(ValueError, match="not parseable"):
        validate_transactions(df)


def test_validate_transactions_rejects_non_numeric_amounts():
    df = _valid_transaction(amount_chf="a lot")
    with pytest.raises(ValueError, match="must be numeric"):
        validate_transactions(df)


def test_validate_transactions_rejects_negative_amounts():
    df = _valid_transaction(amount_chf=-50.0)
    with pytest.raises(ValueError, match="negative amounts"):
        validate_transactions(df)


def test_validate_transactions_rejects_unsupported_transaction_type():
    df = _valid_transaction(transaction_type="refund")
    with pytest.raises(ValueError, match="unsupported transaction_type"):
        validate_transactions(df)


def test_build_monthly_features_raises_on_invalid_input():
    df = _valid_transaction(amount_chf=-50.0)
    with pytest.raises(ValueError, match="negative amounts"):
        build_monthly_features(df)
