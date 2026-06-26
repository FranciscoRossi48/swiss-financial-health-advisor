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
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    users = pd.read_csv(DATA / "scored_users.csv")
    monthly = pd.read_csv(DATA / "user_monthly_features.csv", parse_dates=["month"])
    recommendations = pd.read_csv(DATA / "recommendations.csv")
    centroids = pd.read_csv(DATA / "segment_centroids.csv")
    return users, monthly, recommendations, centroids


def score_color(score: float) -> str:
    if score >= 80:
        return "#16803c"
    if score >= 60:
        return "#4f7fca"
    if score >= 40:
        return "#b7791f"
    return "#b42318"


users, monthly, recommendations, centroids = load_data()

st.title("Swiss Financial Health Advisor")
st.caption("Synthetic prescriptive analytics prototype for personal finance in a Swiss neobank context.")

left, right = st.columns([0.30, 0.70])

with left:
    selected_user = st.selectbox("User", users["user_id"].tolist())
    user = users.loc[users["user_id"] == selected_user].iloc[0]
    rec = recommendations.loc[recommendations["user_id"] == selected_user].iloc[0]

    st.metric("Financial Health Score", f"{user['financial_health_score']:.1f}/100", user["health_band"].title())
    st.metric("Segment", user["segment_label"])
    st.metric("Priority", rec["priority_dimension"].title())

    st.subheader("Recommendation")
    st.write(rec["recommendation"])
    st.caption(rec["explanation"])

with right:
    score_cols = ["liquidity_score", "income_stability_score", "savings_score", "debt_score"]
    scores = pd.DataFrame(
        {
            "dimension": ["Liquidity", "Income stability", "Savings", "Debt"],
            "score": [user[col] for col in score_cols],
        }
    )
    fig = px.bar(
        scores,
        x="dimension",
        y="score",
        range_y=[0, 100],
        color="score",
        color_continuous_scale=["#b42318", "#d99a2b", "#4f7fca", "#16803c"],
        title="Score Breakdown",
    )
    fig.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

    user_monthly = monthly[monthly["user_id"] == selected_user].copy()
    trend = px.line(
        user_monthly,
        x="month",
        y=["income", "expense", "savings"],
        title="Monthly Financial Flows",
        labels={"value": "CHF", "variable": "Flow"},
    )
    st.plotly_chart(trend, use_container_width=True)

st.divider()

col1, col2 = st.columns(2)
with col1:
    scatter = px.scatter(
        users,
        x="avg_savings_rate",
        y="avg_debt_to_income",
        color="segment_label",
        size="financial_health_score",
        hover_data=["user_id", "health_band"],
        title="User Segments",
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
