from __future__ import annotations

import pandas as pd

REQUIRED_TRANSACTION_COLUMNS = {"user_id", "date", "category", "transaction_type", "amount_chf"}
VALID_TRANSACTION_TYPES = {"income", "expense", "savings"}


def validate_transactions(transactions: pd.DataFrame) -> None:
    """Validate the shape and values of raw transactions before they enter the pipeline.

    This is the pipeline's system boundary: transactions are the only input that could
    plausibly come from an external source (a CSV upload or an Open Banking feed) rather
    than from code within this repository. Every downstream module assumes these
    invariants hold, so they are checked once here instead of defensively everywhere.
    """
    if transactions.empty:
        raise ValueError("Transactions dataframe is empty.")

    missing_columns = REQUIRED_TRANSACTION_COLUMNS - set(transactions.columns)
    if missing_columns:
        raise ValueError(f"Transactions dataframe is missing required columns: {sorted(missing_columns)}")

    if transactions["user_id"].isna().any():
        raise ValueError("Transactions dataframe contains rows with a missing user_id.")

    try:
        pd.to_datetime(transactions["date"])
    except (ValueError, TypeError) as exc:
        raise ValueError("Transactions dataframe has a 'date' column that is not parseable.") from exc

    if not pd.api.types.is_numeric_dtype(transactions["amount_chf"]):
        raise ValueError("Transactions dataframe's 'amount_chf' column must be numeric.")

    if (transactions["amount_chf"] < 0).any():
        raise ValueError("Transactions dataframe contains negative amounts; amounts must be non-negative.")

    invalid_types = set(transactions["transaction_type"].unique()) - VALID_TRANSACTION_TYPES
    if invalid_types:
        raise ValueError(
            f"Transactions dataframe contains unsupported transaction_type values: {sorted(invalid_types)}. "
            f"Expected one of {sorted(VALID_TRANSACTION_TYPES)}."
        )
