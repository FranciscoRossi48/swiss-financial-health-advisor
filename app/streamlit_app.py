from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
DATA = ROOT / "data"


st.set_page_config(page_title="Swiss Financial Health Advisor", page_icon="CHF", layout="wide")


@st.cache_data
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    users = pd.read_csv(DATA / "scored_users.csv")
    monthly = pd.read_csv(DATA / "user_monthly_features.csv", parse_dates=["month"])
    recommendations = pd.read_csv(DATA / "recommendations.csv")
    risk_flags = pd.read_csv(DATA / "risk_flags.csv")
    centroids = pd.read_csv(DATA / "segment_centroids.csv")
    return users, monthly, recommendations, risk_flags, centroids


def score_breakdown(record: pd.Series, columns: list[str], labels: list[str]) -> pd.DataFrame:
    return pd.DataFrame({"dimension": labels, "score": [record[col] for col in columns]})


def score_bar(data: pd.DataFrame, title: str):
    fig = px.bar(
        data,
        x="dimension",
        y="score",
        range_y=[0, 100],
        color="score",
        color_continuous_scale=["#b42318", "#d99a2b", "#4f7fca", "#16803c"],
        title=title,
    )
    fig.update_layout(coloraxis_showscale=False, xaxis_title="", yaxis_title="Score")
    return fig


users, monthly, recommendations, risk_flags, centroids = load_data()

st.title("Swiss Financial Health Advisor")
st.caption(
    "Synthetic prescriptive analytics prototype for financial health and credit readiness in a Swiss neobank context."
)

selected_user = st.selectbox("User", users["user_id"].tolist(), label_visibility="collapsed")
user = users.loc[users["user_id"] == selected_user].iloc[0]
rec = recommendations.loc[recommendations["user_id"] == selected_user].iloc[0]
user_flags = risk_flags.loc[risk_flags["user_id"] == selected_user].copy()
user_monthly = monthly.loc[monthly["user_id"] == selected_user].copy()

metric_cols = st.columns(4)
metric_cols[0].metric("Financial Health", f"{user['financial_health_score']:.1f}/100", user["health_band"].title())
metric_cols[1].metric(
    "Credit Readiness",
    f"{user['credit_readiness_score']:.1f}/100",
    user["credit_readiness_band"].title(),
)
metric_cols[2].metric("Segment", user["segment_label"])
metric_cols[3].metric("Priority", rec["priority_dimension"].title())

overview_tab, health_tab, credit_tab, recommendations_tab, segments_tab = st.tabs(
    ["Overview", "Financial Health", "Credit Readiness", "Recommendations", "Segment Insights"]
)

with overview_tab:
    left, right = st.columns([0.42, 0.58])
    with left:
        st.subheader("User Snapshot")
        st.dataframe(
            pd.DataFrame(
                [
                    ["Average income", f"CHF {user['avg_income']:,.0f}"],
                    ["Average expense", f"CHF {user['avg_expense']:,.0f}"],
                    ["Average net cashflow", f"CHF {user['avg_net_cashflow']:,.0f}"],
                    ["Savings rate", f"{user['avg_savings_rate']:.1%}"],
                    ["Debt-to-income", f"{user['avg_debt_to_income']:.1%}"],
                    ["Income volatility", f"{user['income_cv']:.2f}"],
                ],
                columns=["Metric", "Value"],
            ),
            use_container_width=True,
            hide_index=True,
        )

        st.subheader("Primary Recommendation")
        st.write(rec["recommendation"])
        st.caption(rec["explanation"])

    with right:
        trend = px.line(
            user_monthly,
            x="month",
            y=["income", "expense", "savings"],
            title="Monthly Financial Flows",
            labels={"value": "CHF", "variable": "Flow"},
        )
        st.plotly_chart(trend, use_container_width=True)

with health_tab:
    health_scores = score_breakdown(
        user,
        ["liquidity_score", "income_stability_score", "savings_score", "debt_score"],
        ["Liquidity", "Income stability", "Savings", "Debt"],
    )
    st.plotly_chart(score_bar(health_scores, "Financial Health Score Breakdown"), use_container_width=True)

    population = px.histogram(
        users,
        x="financial_health_score",
        color="health_band",
        nbins=25,
        title="Population Distribution by Financial Health",
    )
    st.plotly_chart(population, use_container_width=True)

with credit_tab:
    credit_scores = score_breakdown(
        user,
        [
            "income_reliability_score",
            "debt_capacity_score",
            "cashflow_resilience_score",
            "savings_discipline_score",
            "spending_control_score",
        ],
        ["Income reliability", "Debt capacity", "Cashflow resilience", "Savings discipline", "Spending control"],
    )
    st.plotly_chart(score_bar(credit_scores, "Credit Readiness Score Breakdown"), use_container_width=True)

    flag_counts = (
        risk_flags.groupby(["severity", "flag"])
        .size()
        .reset_index(name="users")
        .sort_values(["severity", "users"], ascending=[True, False])
    )
    flag_chart = px.bar(
        flag_counts,
        x="flag",
        y="users",
        color="severity",
        title="Risk Flags Across Synthetic Users",
    )
    flag_chart.update_layout(xaxis_title="", yaxis_title="Users")
    st.plotly_chart(flag_chart, use_container_width=True)

with recommendations_tab:
    st.subheader("Prescriptive Action")
    st.write(rec["recommendation"])
    st.caption(rec["explanation"])

    st.subheader("Credit Readiness Risk Flags")
    st.dataframe(
        user_flags[["severity", "flag", "explanation"]],
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "Credit readiness is an educational decision-support signal. It is not an approval, rejection, pricing, or eligibility decision."
    )

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
            title="User Segments by Savings and Debt",
            labels={
                "avg_savings_rate": "Average savings rate",
                "avg_debt_to_income": "Debt-to-income",
                "segment_label": "Segment",
            },
        )
        st.plotly_chart(scatter, use_container_width=True)

    with col2:
        st.subheader("Segment Centroids")
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
    "Educational prototype with synthetic data. Outputs are explainable analytics signals, not regulated financial advice."
)
