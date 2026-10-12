"""Customer-facing labels shared by the Streamlit dashboard and the API.

The synthetic generator only emits categories; these mappings turn them into the kind of
merchant names and copy a banking app would show, without touching the analytical layer.
"""

from __future__ import annotations

CATEGORY_LABELS = {
    "salary": "Salary",
    "freelance": "Freelance",
    "rent": "Rent",
    "insurance": "Insurance",
    "groceries": "Groceries",
    "transport": "Transport",
    "restaurants": "Restaurants",
    "shopping": "Shopping",
    "travel": "Travel",
    "subscriptions": "Subscriptions",
    "debt_payment": "Debt payment",
    "savings_transfer": "Savings transfer",
}

MERCHANTS = {
    "salary": "Employer payroll",
    "freelance": "Client transfer",
    "rent": "Zurich apartment",
    "insurance": "Swiss insurance",
    "groceries": "Migros",
    "transport": "SBB",
    "restaurants": "Local dining",
    "shopping": "Retail purchase",
    "travel": "Travel booking",
    "subscriptions": "Digital subscription",
    "debt_payment": "Loan repayment",
    "savings_transfer": "Savings pocket",
}

SEGMENT_DESCRIPTIONS = {
    "Stable saver": "Steady income and a consistent savings habit. You have room to plan for bigger goals.",
    "Balanced user": "Income and spending are in balance, but there is little left over each month.",
    "High discretionary": (
        "A large share of your money goes to non-essential spending like dining, shopping and travel."
    ),
    "Debt pressure": "Debt repayments take a big bite out of your income, which limits your flexibility.",
    "Variable income": "Your income changes a lot from month to month, so a buffer matters more for you.",
}


def category_label(category: str) -> str:
    return CATEGORY_LABELS.get(category, category.replace("_", " ").title())


def merchant_name(category: str) -> str:
    return MERCHANTS.get(category, category_label(category))
