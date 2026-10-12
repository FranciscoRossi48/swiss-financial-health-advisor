from __future__ import annotations

import pandas as pd

from swiss_financial_health.validation import validate_transactions


def build_monthly_features(transactions: pd.DataFrame) -> pd.DataFrame:
    validate_transactions(transactions)
    df = transactions.copy()
    df["month"] = pd.to_datetime(df["date"]).dt.to_period("M").dt.to_timestamp()

    pivot = (
        df.pivot_table(
            index=["user_id", "month", "profile"],
            columns="transaction_type",
            values="amount_chf",
            aggfunc="sum",
            fill_value=0,
        )
        .reset_index()
        .rename_axis(None, axis=1)
    )

    for col in ["income", "expense", "savings"]:
        if col not in pivot:
            pivot[col] = 0.0

    debt = (
        df[df["category"] == "debt_payment"]
        .groupby(["user_id", "month"])["amount_chf"]
        .sum()
        .rename("debt_payments")
        .reset_index()
    )
    discretionary = (
        df[df["category"].isin(["restaurants", "shopping", "travel", "subscriptions"])]
        .groupby(["user_id", "month"])["amount_chf"]
        .sum()
        .rename("discretionary_spend")
        .reset_index()
    )

    features = pivot.merge(debt, on=["user_id", "month"], how="left").merge(
        discretionary, on=["user_id", "month"], how="left"
    )
    features[["debt_payments", "discretionary_spend"]] = features[
        ["debt_payments", "discretionary_spend"]
    ].fillna(0)

    # Free cashflow treats savings transfers as reserves the customer keeps, not as spending.
    # Net cashflow is what is left on the current account after those transfers.
    features["free_cashflow"] = features["income"] - features["expense"]
    features["net_cashflow"] = features["free_cashflow"] - features["savings"]
    features["savings_rate"] = safe_ratio(
        features["savings"] + features["net_cashflow"].clip(lower=0), features["income"]
    )
    features["expense_ratio"] = safe_ratio(features["expense"], features["income"])
    features["debt_to_income"] = safe_ratio(features["debt_payments"], features["income"])
    features["discretionary_ratio"] = safe_ratio(features["discretionary_spend"], features["income"])

    income_stats = (
        features.groupby("user_id")["income"].agg(avg_income="mean", income_std="std").reset_index()
    )
    income_stats["income_cv"] = safe_ratio(income_stats["income_std"].fillna(0), income_stats["avg_income"])

    features = features.merge(income_stats[["user_id", "avg_income", "income_cv"]], on="user_id", how="left")
    return features.sort_values(["user_id", "month"]).reset_index(drop=True)


def build_user_summary(monthly_features: pd.DataFrame) -> pd.DataFrame:
    summary = (
        monthly_features.groupby(["user_id", "profile"])
        .agg(
            avg_income=("income", "mean"),
            avg_expense=("expense", "mean"),
            avg_savings_rate=("savings_rate", "mean"),
            avg_debt_to_income=("debt_to_income", "mean"),
            avg_discretionary_ratio=("discretionary_ratio", "mean"),
            avg_net_cashflow=("net_cashflow", "mean"),
            avg_free_cashflow=("free_cashflow", "mean"),
            total_free_cashflow=("free_cashflow", "sum"),
            income_cv=("income_cv", "mean"),
        )
        .reset_index()
    )
    # Reserves built over the observation window (current account + savings pocket, assuming no
    # opening balance), expressed in months of average spending: an emergency-fund style measure.
    summary["reserve_months"] = safe_ratio_signed(summary["total_free_cashflow"], summary["avg_expense"])
    return summary.drop(columns="total_free_cashflow")


def safe_ratio(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return safe_ratio_signed(numerator, denominator).clip(lower=0)


def safe_ratio_signed(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """Like safe_ratio, but keeps negative values (e.g. reserves that were drawn down)."""
    ratio = numerator / denominator.replace(0, pd.NA)
    return ratio.astype("Float64").fillna(0).astype(float)
