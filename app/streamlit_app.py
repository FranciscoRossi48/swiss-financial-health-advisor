from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
DATA = ROOT / "data"

from swiss_financial_health.affordability import simulate_loan_affordability


NEON_GREEN = "#12E6A8"
INK = "#111827"
MUTED = "#6B7280"
OFF_WHITE = "#F3FBF7"
LINE = "#E5E7EB"

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


st.set_page_config(page_title="neon Financial Coach", page_icon="CHF", layout="wide")


@st.cache_data
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    transactions = pd.read_csv(DATA / "synthetic_transactions.csv", parse_dates=["date"])
    users = pd.read_csv(DATA / "scored_users.csv")
    monthly = pd.read_csv(DATA / "user_monthly_features.csv", parse_dates=["month"])
    recommendations = pd.read_csv(DATA / "recommendations.csv")
    risk_flags = pd.read_csv(DATA / "risk_flags.csv")
    centroids = pd.read_csv(DATA / "segment_centroids.csv")
    return transactions, users, monthly, recommendations, risk_flags, centroids


def prepare_user_transactions(transactions: pd.DataFrame, user_id: str) -> pd.DataFrame:
    user_tx = transactions.loc[transactions["user_id"] == user_id].copy()
    user_tx["movement"] = user_tx["transaction_type"].map(
        {"income": "Money in", "expense": "Money out", "savings": "Savings"}
    )
    user_tx["signed_amount"] = user_tx["amount_chf"]
    user_tx.loc[user_tx["transaction_type"].isin(["expense", "savings"]), "signed_amount"] *= -1
    user_tx["display_amount"] = user_tx["signed_amount"].map(lambda value: f"CHF {value:,.2f}")
    user_tx["merchant"] = user_tx["category"].map(MERCHANTS).fillna(
        user_tx["category"].str.replace("_", " ").str.title()
    )
    user_tx["category_label"] = user_tx["category"].map(CATEGORY_LABELS).fillna(
        user_tx["category"].str.replace("_", " ").str.title()
    )
    return user_tx.sort_values("date", ascending=False).reset_index(drop=True)


def score_breakdown(record: pd.Series, columns: list[str], labels: list[str]) -> pd.DataFrame:
    return pd.DataFrame({"dimension": labels, "score": [record[col] for col in columns]})


def score_bar(data: pd.DataFrame, title: str):
    fig = px.bar(
        data,
        x="dimension",
        y="score",
        range_y=[0, 100],
        color="score",
        color_continuous_scale=["#DC2626", "#D97706", "#2563EB", NEON_GREEN],
        title=title,
    )
    fig.update_layout(coloraxis_showscale=False, xaxis_title="", yaxis_title="Score")
    return fig


def inject_styles() -> None:
    st.markdown(
        f"""
        <style>
        :root {{
            --neon-green: {NEON_GREEN};
            --ink: {INK};
            --muted: {MUTED};
            --off-white: {OFF_WHITE};
            --line: {LINE};
        }}
        .stApp {{
            background: linear-gradient(180deg, #ffffff 0%, var(--off-white) 100%);
            color: var(--ink);
        }}
        h1, h2, h3 {{
            letter-spacing: 0;
        }}
        div[data-testid="stMetric"] {{
            background: rgba(255, 255, 255, 0.86);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 14px 16px;
        }}
        div[data-testid="stMetricLabel"] {{
            color: var(--muted);
        }}
        .neon-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 18px;
            padding: 18px 20px;
            border: 1px solid var(--line);
            border-radius: 8px;
            background: #ffffff;
            margin-bottom: 18px;
        }}
        .neon-logo {{
            font-size: 34px;
            line-height: 1;
            font-weight: 800;
            letter-spacing: 0;
            color: var(--ink);
        }}
        .neon-logo span {{
            color: var(--neon-green);
        }}
        .neon-subtitle {{
            margin-top: 6px;
            color: var(--muted);
            font-size: 14px;
        }}
        .pill {{
            display: inline-flex;
            align-items: center;
            min-height: 30px;
            padding: 5px 10px;
            border-radius: 8px;
            background: #DDFBEF;
            color: #065F46;
            font-weight: 700;
            font-size: 13px;
        }}
        .notice {{
            padding: 10px 12px;
            border: 1px solid var(--line);
            border-radius: 8px;
            background: rgba(255,255,255,.72);
            color: var(--muted);
            font-size: 13px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


inject_styles()
transactions, users, monthly, recommendations, risk_flags, centroids = load_data()

st.markdown(
    """
    <div class="neon-header">
      <div>
        <div class="neon-logo">neon<span>.</span> coach</div>
        <div class="neon-subtitle">
          A banking-app prototype for transactions, financial health and prescriptive guidance.
        </div>
      </div>
      <div class="pill">Prototype inspired by neon Switzerland AG</div>
    </div>
    """,
    unsafe_allow_html=True,
)

selected_user = st.selectbox("Customer profile", users["user_id"].tolist())
user = users.loc[users["user_id"] == selected_user].iloc[0]
rec = recommendations.loc[recommendations["user_id"] == selected_user].iloc[0]
user_flags = risk_flags.loc[risk_flags["user_id"] == selected_user].copy()
user_monthly = monthly.loc[monthly["user_id"] == selected_user].copy()
user_tx = prepare_user_transactions(transactions, selected_user)

current_balance = user_tx["signed_amount"].sum()
monthly_income = user_monthly["income"].iloc[-1]
monthly_outflow = user_monthly[["expense", "savings"]].iloc[-1].sum()

metric_cols = st.columns(4)
metric_cols[0].metric("Current balance", f"CHF {current_balance:,.0f}")
metric_cols[1].metric("Monthly income", f"CHF {monthly_income:,.0f}")
metric_cols[2].metric("Monthly outflow", f"CHF {monthly_outflow:,.0f}")
metric_cols[3].metric("Segment", user["segment_label"])

home_tab, transactions_tab, health_tab, coach_tab, simulator_tab, segments_tab = st.tabs(
    ["Home", "Transactions", "Financial Health", "Coach", "Loan Simulator", "Segments"]
)

with home_tab:
    left, right = st.columns([0.38, 0.62])
    with left:
        st.subheader("Your financial snapshot")
        score_cols = st.columns(2)
        score_cols[0].metric(
            "Health index",
            f"{user['financial_health_score']:.1f}/100",
            user["health_band"].title(),
        )
        score_cols[1].metric(
            "Credit readiness",
            f"{user['credit_readiness_score']:.1f}/100",
            user["credit_readiness_band"].title(),
        )
        st.dataframe(
            pd.DataFrame(
                [
                    ["Average income", f"CHF {user['avg_income']:,.0f}"],
                    ["Average expenses", f"CHF {user['avg_expense']:,.0f}"],
                    ["Net cashflow", f"CHF {user['avg_net_cashflow']:,.0f}"],
                    ["Savings rate", f"{user['avg_savings_rate']:.1%}"],
                    ["Debt-to-income", f"{user['avg_debt_to_income']:.1%}"],
                ],
                columns=["Metric", "Value"],
            ),
            use_container_width=True,
            hide_index=True,
        )
        st.markdown(f"**Recommended next step**  \n{rec['recommendation']}")
        st.caption(rec["explanation"])

    with right:
        trend = px.line(
            user_monthly,
            x="month",
            y=["income", "expense", "savings"],
            title="Monthly flows",
            labels={"value": "CHF", "variable": "Flow"},
            color_discrete_map={"income": NEON_GREEN, "expense": "#111827", "savings": "#2563EB"},
        )
        trend.update_layout(legend_title_text="")
        st.plotly_chart(trend, use_container_width=True)

with transactions_tab:
    st.subheader("Movements")
    filter_cols = st.columns([0.35, 0.35, 0.30])
    movement_filter = filter_cols[0].multiselect(
        "Movement type",
        ["Money in", "Money out", "Savings"],
        default=["Money in", "Money out", "Savings"],
    )
    category_filter = filter_cols[1].multiselect(
        "Category",
        sorted(user_tx["category_label"].unique()),
        default=sorted(user_tx["category_label"].unique()),
    )
    rows_to_show = filter_cols[2].slider("Rows", 10, 80, 25, step=5)

    filtered_tx = user_tx[
        user_tx["movement"].isin(movement_filter) & user_tx["category_label"].isin(category_filter)
    ].head(rows_to_show)

    st.dataframe(
        filtered_tx[["date", "merchant", "category_label", "movement", "display_amount"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "date": "Date",
            "merchant": "Merchant",
            "category_label": "Category",
            "movement": "Type",
            "display_amount": "Amount",
        },
    )

    spend = (
        user_tx[user_tx["transaction_type"].isin(["expense", "savings"])]
        .groupby("category_label", as_index=False)["amount_chf"]
        .sum()
        .sort_values("amount_chf", ascending=False)
    )
    spend_fig = px.bar(
        spend,
        x="category_label",
        y="amount_chf",
        title="Spending and savings transfers by category",
        labels={"category_label": "", "amount_chf": "CHF"},
        color_discrete_sequence=[NEON_GREEN],
    )
    st.plotly_chart(spend_fig, use_container_width=True)

with health_tab:
    st.subheader("Health index")
    health_scores = score_breakdown(
        user,
        ["liquidity_score", "income_stability_score", "savings_score", "debt_score"],
        ["Liquidity", "Income stability", "Savings", "Debt"],
    )
    st.plotly_chart(score_bar(health_scores, "Health index breakdown"), use_container_width=True)

    st.subheader("Credit readiness")
    credit_scores = score_breakdown(
        user,
        [
            "income_reliability_score",
            "debt_capacity_score",
            "cashflow_resilience_score",
            "savings_discipline_score",
            "spending_control_score",
        ],
        [
            "Income reliability",
            "Debt capacity",
            "Cashflow resilience",
            "Savings discipline",
            "Spending control",
        ],
    )
    st.plotly_chart(score_bar(credit_scores, "Credit readiness breakdown"), use_container_width=True)

with coach_tab:
    st.subheader("Personalized guidance")
    st.markdown(f"**Priority area:** {rec['priority_dimension'].title()}")
    st.write(rec["recommendation"])
    st.caption(rec["explanation"])

    st.subheader("Risk flags")
    st.dataframe(
        user_flags[["severity", "flag", "explanation"]],
        use_container_width=True,
        hide_index=True,
    )
    st.markdown(
        """
        <div class="notice">
        These insights are educational decision-support signals. They are not credit approval, credit pricing,
        investment advice, or regulated financial advice.
        </div>
        """,
        unsafe_allow_html=True,
    )

with simulator_tab:
    st.subheader("Loan affordability simulator")
    input_cols = st.columns(3)
    loan_amount = input_cols[0].number_input(
        "Loan amount (CHF)", min_value=500.0, max_value=200_000.0, value=10_000.0, step=500.0
    )
    annual_rate_pct = input_cols[1].slider("Annual interest rate (%)", 0.0, 15.0, 5.0, step=0.1)
    term_years = input_cols[2].slider("Term (years)", 1, 10, 3)

    result = simulate_loan_affordability(
        avg_income=user["avg_income"],
        avg_net_cashflow=user["avg_net_cashflow"],
        avg_debt_to_income=user["avg_debt_to_income"],
        loan_amount=loan_amount,
        annual_rate=annual_rate_pct / 100,
        term_years=term_years,
    )

    result_cols = st.columns(3)
    result_cols[0].metric("Monthly payment", f"CHF {result.monthly_payment:,.0f}")
    result_cols[1].metric("Resulting debt-to-income", f"{result.resulting_debt_to_income:.1%}")
    result_cols[2].metric("Projected free cashflow", f"CHF {result.projected_free_cashflow:,.0f}")

    if result.verdict == "affordable":
        st.success(f"**{result.verdict.title()}** — {result.explanation}")
    elif result.verdict == "marginal":
        st.warning(f"**{result.verdict.title()}** — {result.explanation}")
    else:
        st.error(f"**{result.verdict.title()}** — {result.explanation}")

with segments_tab:
    col1, col2 = st.columns(2)
    with col1:
        scatter = px.scatter(
            users,
            x="avg_savings_rate",
            y="avg_debt_to_income",
            color="segment_label",
            size="credit_readiness_score",
            hover_data=["user_id", "health_band", "credit_readiness_band"],
            title="Customer segments",
            labels={
                "avg_savings_rate": "Average savings rate",
                "avg_debt_to_income": "Debt-to-income",
                "segment_label": "Segment",
            },
        )
        st.plotly_chart(scatter, use_container_width=True)

    with col2:
        st.subheader("Segment centroids")
        st.dataframe(
            centroids[
                [
                    "segment_label",
                    "avg_income",
                    "avg_savings_rate",
                    "avg_debt_to_income",
                    "avg_discretionary_ratio",
                    "income_cv",
                    "financial_health_score",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

st.caption(
    "Educational prototype with synthetic data. Visual style is inspired by neon Switzerland AG, "
    "but this project is independent and not affiliated with neon."
)
