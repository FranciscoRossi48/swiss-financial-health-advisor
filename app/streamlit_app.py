from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
DATA = ROOT / "data"

from swiss_financial_health.affordability import AFFORDABILITY_CEILING, simulate_loan_affordability
from swiss_financial_health.credit_readiness import CREDIT_READINESS_WEIGHTS
from swiss_financial_health.presentation import CATEGORY_LABELS, MERCHANTS
from swiss_financial_health.recommendations import plan_steps
from swiss_financial_health.scoring import SCORE_WEIGHTS


# Pulse tokens, the same as web/src/index.css (the theme itself lives in .streamlit/config.toml).
INK = "#0c1a17"
MINT = "#1fd99a"
MINT_DEEP = "#0e9f6e"
MINT_SOFT = "#dcf7eb"
CANVAS = "#f3f6f4"
MUTED = "#66756f"
LINE = "#e3e9e6"
DANGER, DANGER_SOFT = "#e5484d", "#fdecec"
WARN, WARN_SOFT = "#d98a13", "#fdf3e2"
INFO, INFO_SOFT = "#3a7bd5", "#e7f0fc"

SEGMENT_COLORS = {
    "Stable saver": MINT_DEEP,
    "Variable income": INFO,
    "Balanced user": INK,
    "High discretionary": WARN,
    "Debt pressure": DANGER,
}

BAND_TONES = {
    "strong": "good",
    "healthy": "good",
    "fragile": "warn",
    "critical": "danger",
    "ready": "good",
    "moderate": "info",
    "needs improvement": "warn",
    "not ready": "danger",
    "high": "danger",
    "medium": "warn",
    "low": "info",
}
TONES = {
    "good": (MINT_DEEP, MINT_SOFT),
    "info": (INFO, INFO_SOFT),
    "warn": (WARN, WARN_SOFT),
    "danger": (DANGER, DANGER_SOFT),
}

HEALTH_LABELS = {
    "liquidity_score": "Liquidity",
    "savings_score": "Savings capacity",
    "income_stability_score": "Income stability",
    "debt_score": "Debt exposure",
}
CREDIT_LABELS = {
    "income_reliability_score": "Income reliability",
    "debt_capacity_score": "Debt capacity",
    "cashflow_resilience_score": "Cashflow resilience",
    "savings_discipline_score": "Savings discipline",
    "spending_control_score": "Spending control",
}


st.set_page_config(page_title="Pulse · Analyst view", page_icon="📈", layout="wide")


@st.cache_data
def load_data() -> dict[str, pd.DataFrame]:
    return {
        "transactions": pd.read_csv(DATA / "synthetic_transactions.csv", parse_dates=["date"]),
        "users": pd.read_csv(DATA / "scored_users.csv"),
        "monthly": pd.read_csv(DATA / "user_monthly_features.csv", parse_dates=["month"]),
        "recommendations": pd.read_csv(DATA / "recommendations.csv"),
        "risk_flags": pd.read_csv(DATA / "risk_flags.csv"),
        "centroids": pd.read_csv(DATA / "segment_centroids.csv"),
        "history": pd.read_csv(DATA / "score_history.csv", parse_dates=["month"]),
    }


def chf(value: float, decimals: int = 0) -> str:
    """Swiss formatting, as in the Pulse app: CHF 7’150."""
    sign = "−" if value < 0 else ""
    return f"{sign}CHF {abs(value):,.{decimals}f}".replace(",", "’")


def score_tone(score: float) -> str:
    return "good" if score >= 60 else "info" if score >= 40 else "warn" if score >= 25 else "danger"


def chip(text: str, tone: str) -> str:
    color, background = TONES[tone]
    return f'<span class="chip" style="color:{color};background:{background}">{text}</span>'


def step_html(number: int, step: dict[str, object]) -> str:
    points = f'<div class="step-pts">+{step["points"]}</div>' if step["points"] else ""
    return (
        f'<div class="step"><div class="step-n">{number}</div>'
        f'<div><div class="step-title">{step["title"]}</div><div class="step-body">{step["body"]}</div></div>'
        f"{points}</div>"
    )


def prepare_user_transactions(transactions: pd.DataFrame, user_id: str) -> pd.DataFrame:
    user_tx = transactions.loc[transactions["user_id"] == user_id].copy()
    user_tx["movement"] = user_tx["transaction_type"].map(
        {"income": "Money in", "expense": "Money out", "savings": "Savings"}
    )
    user_tx["signed_amount"] = user_tx["amount_chf"]
    user_tx.loc[user_tx["transaction_type"].isin(["expense", "savings"]), "signed_amount"] *= -1
    user_tx["merchant"] = (
        user_tx["category"].map(MERCHANTS).fillna(user_tx["category"].str.replace("_", " ").str.title())
    )
    user_tx["category_label"] = (
        user_tx["category"].map(CATEGORY_LABELS).fillna(user_tx["category"].str.replace("_", " ").str.title())
    )
    return user_tx.sort_values("date", ascending=False).reset_index(drop=True)


def style_figure(fig: go.Figure, height: int = 340) -> go.Figure:
    """Pulse look for every chart: Manrope, transparent background, light grid, no clutter."""
    fig.update_layout(
        height=height,
        margin={"l": 8, "r": 8, "t": 36, "b": 8},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Manrope, sans-serif", "color": INK, "size": 12},
        title={"font": {"size": 15, "color": INK}, "x": 0, "xanchor": "left"},
        legend={
            "orientation": "h",
            "y": 1.02,
            "yanchor": "bottom",
            "x": 1,
            "xanchor": "right",
            "title": None,
        },
        hoverlabel={"font_family": "Manrope, sans-serif"},
    )
    fig.update_xaxes(
        showgrid=False,
        linecolor=LINE,
        tickfont={"color": MUTED},
        title_font={"color": MUTED},
        automargin=True,
    )
    fig.update_yaxes(
        gridcolor=LINE,
        zeroline=False,
        tickfont={"color": MUTED},
        title_font={"color": MUTED},
        automargin=True,
    )
    return fig


def show_chart(fig: go.Figure) -> None:
    # theme=None keeps the Pulse colours instead of Streamlit's chart theme
    st.plotly_chart(fig, theme=None, width="stretch", config={"displayModeBar": False})


def breakdown_chart(record: pd.Series, labels: dict[str, str], weights: dict[str, float], title: str):
    data = pd.DataFrame(
        {
            "dimension": [f"{labels[col]} · {weights[col]:.0%}" for col in labels],
            "score": [record[col] for col in labels],
        }
    )
    # bar fills match the app's progress bars: mint for good, otherwise the tone colour
    data["color"] = [
        MINT if score_tone(score) == "good" else TONES[score_tone(score)][0] for score in data["score"]
    ]
    fig = go.Figure(
        go.Bar(
            x=data["score"],
            y=data["dimension"],
            orientation="h",
            marker={"color": data["color"], "cornerradius": 6},
            text=data["score"].round(0).astype(int),
            textposition="outside",
            cliponaxis=False,
            hovertemplate="%{y}: %{x:.1f} / 100<extra></extra>",
        )
    )
    fig.update_layout(title=title, bargap=0.35)
    fig.update_xaxes(range=[0, 108], showgrid=True, gridcolor=LINE, title=None)
    fig.update_yaxes(autorange="reversed", showgrid=False, title=None, tickfont={"color": INK, "size": 13})
    return style_figure(fig, height=60 + 52 * len(labels))


def inject_styles() -> None:
    st.markdown(
        f"""
        <style>
        .block-container {{ padding-top: 2.5rem; max-width: 1240px; }}
        div[data-testid="stMetric"] {{
            background: #fff;
            border: 1px solid {LINE};
            border-radius: 20px;
            padding: 16px 18px;
            box-shadow: 0 1px 2px rgba(12, 26, 23, 0.04);
        }}
        div[data-testid="stMetricLabel"] p {{ color: {MUTED}; font-weight: 600; }}
        div[role="tab"] p {{ font-weight: 700; }}
        .pulse-header {{
            display: flex; align-items: center; justify-content: space-between; gap: 18px;
            padding: 20px 24px; margin-bottom: 20px; border-radius: 24px;
            background: {INK}; color: #fff; position: relative; overflow: hidden;
        }}
        .pulse-header::before {{
            content: ""; position: absolute; right: -60px; top: -90px; width: 260px; height: 260px;
            border-radius: 999px; background: rgba(31, 217, 154, 0.25); filter: blur(60px);
        }}
        .pulse-brand {{ display: flex; align-items: center; gap: 14px; position: relative; }}
        .pulse-logo {{ font-size: 30px; line-height: 1; font-weight: 800; letter-spacing: -0.02em; }}
        .pulse-logo span {{ color: {MINT}; }}
        .pulse-subtitle {{ margin-top: 6px; color: rgba(255,255,255,0.65); font-size: 14px; }}
        .pulse-pill {{
            position: relative; padding: 6px 12px; border-radius: 999px; font-size: 13px; font-weight: 700;
            background: rgba(255,255,255,0.08); color: {MINT};
        }}
        .chip {{
            display: inline-block; padding: 3px 10px; border-radius: 999px; font-size: 12px; font-weight: 700;
            margin-right: 6px;
        }}
        .eyebrow {{
            font-size: 12px; font-weight: 700; letter-spacing: 0.03em; text-transform: uppercase;
            color: {MUTED};
        }}
        .focus-card {{
            background: {INK}; color: #fff; border-radius: 24px; padding: 22px 24px; margin-bottom: 12px;
        }}
        .focus-card .eyebrow {{ color: {MINT}; }}
        .focus-card h3 {{ color: #fff; margin: 10px 0 6px; font-size: 20px; line-height: 1.35; }}
        .focus-card p {{ color: rgba(255,255,255,0.7); margin: 0; font-size: 14px; }}
        .step {{
            display: flex; gap: 12px; align-items: flex-start; padding: 12px 14px; margin-bottom: 8px;
            background: #fff; border: 1px solid {LINE}; border-radius: 16px;
        }}
        .step-n {{
            flex-shrink: 0; width: 24px; height: 24px; border-radius: 8px; background: {INK}; color: {MINT};
            font-size: 12px; font-weight: 800; display: flex; align-items: center; justify-content: center;
        }}
        .step-title {{ font-weight: 700; font-size: 14px; }}
        .step-body {{ color: {MUTED}; font-size: 13px; margin-top: 2px; }}
        .step-pts {{
            margin-left: auto; flex-shrink: 0; padding: 2px 8px; border-radius: 999px; font-size: 12px;
            font-weight: 800; background: {MINT_SOFT}; color: {MINT_DEEP};
        }}
        .flag {{ display: flex; gap: 10px; padding: 12px 14px; margin-bottom: 8px; border-radius: 16px; }}
        .flag-title {{ font-weight: 700; font-size: 14px; }}
        .flag-body {{ color: {MUTED}; font-size: 13px; margin-top: 2px; }}
        .notice {{ color: {MUTED}; font-size: 12px; margin-top: 12px; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


inject_styles()
data = load_data()
users = data["users"]

st.markdown(
    f"""
    <div class="pulse-header">
      <div class="pulse-brand">
        <svg width="44" height="44" viewBox="0 0 32 32" aria-hidden="true">
          <rect width="32" height="32" rx="9" fill="#ffffff" fill-opacity="0.08"/>
          <path d="M5 17h5l3-7 5 13 3-6h6" fill="none" stroke="{MINT}" stroke-width="2.6"
                stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <div>
          <div class="pulse-logo">pulse<span>.</span> analyst view</div>
          <div class="pulse-subtitle">
            Transactions, financial health, segments and guidance for each synthetic customer.
          </div>
        </div>
      </div>
      <div class="pulse-pill">Fictional brand · synthetic data</div>
    </div>
    """,
    unsafe_allow_html=True,
)

labels_by_user = {
    row.user_id: f"{row.user_id} · {row.segment_label} · health {row.financial_health_score:.0f}"
    for row in users.itertuples()
}
selected_user = st.selectbox("Customer", list(labels_by_user), format_func=labels_by_user.get)

user = users.loc[users["user_id"] == selected_user].iloc[0]
rec = data["recommendations"].loc[data["recommendations"]["user_id"] == selected_user].iloc[0]
user_flags = data["risk_flags"].loc[data["risk_flags"]["user_id"] == selected_user]
user_monthly = data["monthly"].loc[data["monthly"]["user_id"] == selected_user]
user_history = data["history"].loc[data["history"]["user_id"] == selected_user]
user_tx = prepare_user_transactions(data["transactions"], selected_user)

latest = user_monthly.iloc[-1]
metric_cols = st.columns(4)
metric_cols[0].metric("Current balance", chf(user_tx["signed_amount"].sum()))
metric_cols[1].metric(f"Income · {latest['month']:%b %Y}", chf(latest["income"]))
metric_cols[2].metric(f"Spent + saved · {latest['month']:%b %Y}", chf(latest["expense"] + latest["savings"]))
metric_cols[3].metric("Segment", user["segment_label"])

overview_tab, transactions_tab, health_tab, coach_tab, simulator_tab, segments_tab = st.tabs(
    ["Overview", "Transactions", "Financial health", "Coach", "Loan simulator", "Segments"]
)

with overview_tab:
    left, right = st.columns([0.4, 0.6], gap="large")
    with left:
        score_cols = st.columns(2)
        score_cols[0].metric("Health index · of 100", f"{user['financial_health_score']:.0f}")
        score_cols[0].markdown(
            chip(user["health_band"].title(), BAND_TONES[user["health_band"]]), unsafe_allow_html=True
        )
        score_cols[1].metric("Credit readiness · of 100", f"{user['credit_readiness_score']:.0f}")
        score_cols[1].markdown(
            chip(user["credit_readiness_band"].title(), BAND_TONES[user["credit_readiness_band"]]),
            unsafe_allow_html=True,
        )
        st.dataframe(
            pd.DataFrame(
                [
                    ["Average income", chf(user["avg_income"])],
                    ["Average spending", chf(user["avg_expense"])],
                    ["Free cashflow", chf(user["avg_free_cashflow"])],
                    ["Reserves", f"{user['reserve_months']:.1f} months of spending"],
                    ["Savings rate", f"{user['avg_savings_rate']:.1%}"],
                    ["Debt-to-income", f"{user['avg_debt_to_income']:.1%}"],
                ],
                columns=["Metric", "Value"],
            ),
            width="stretch",
            hide_index=True,
        )

    with right:
        flows = user_monthly.melt(
            id_vars="month", value_vars=["income", "expense", "savings"], var_name="flow", value_name="CHF"
        )
        flows["flow"] = flows["flow"].map({"income": "Income", "expense": "Spending", "savings": "Savings"})
        trend = px.line(
            flows,
            x="month",
            y="CHF",
            color="flow",
            title="Monthly flows",
            color_discrete_map={"Income": MINT_DEEP, "Spending": INK, "Savings": INFO},
        )
        trend.update_traces(line={"width": 2.5})
        trend.update_xaxes(title=None, dtick="M2", tickformat="%b")
        trend.update_yaxes(title=None, tickformat=",.0f")
        show_chart(style_figure(trend))

with transactions_tab:
    filter_cols = st.columns(2)
    movement_filter = filter_cols[0].multiselect(
        "Movement type", ["Money in", "Money out", "Savings"], default=["Money in", "Money out", "Savings"]
    )
    categories = sorted(user_tx["category_label"].unique())
    category_filter = filter_cols[1].multiselect("Category", categories, default=categories)
    filtered_tx = user_tx[
        user_tx["movement"].isin(movement_filter) & user_tx["category_label"].isin(category_filter)
    ]

    table_col, chart_col = st.columns([0.55, 0.45], gap="large")
    with table_col:
        st.dataframe(
            filtered_tx[["date", "merchant", "category_label", "movement", "signed_amount"]],
            width="stretch",
            height=420,
            hide_index=True,
            column_config={
                "date": st.column_config.DateColumn("Date", format="D MMM YYYY"),
                "merchant": "Merchant",
                "category_label": "Category",
                "movement": "Type",
                "signed_amount": st.column_config.NumberColumn("Amount (CHF)", format="%.2f"),
            },
        )
    with chart_col:
        spend = (
            filtered_tx[filtered_tx["transaction_type"].isin(["expense", "savings"])]
            .groupby("category_label", as_index=False)["amount_chf"]
            .sum()
            .sort_values("amount_chf")
        )
        spend_fig = px.bar(
            spend,
            x="amount_chf",
            y="category_label",
            orientation="h",
            title="Spending and savings by category (12 months)",
            color_discrete_sequence=[MINT],
        )
        spend_fig.update_traces(marker_cornerradius=6, hovertemplate="%{y}: CHF %{x:,.0f}<extra></extra>")
        spend_fig.update_xaxes(title=None, tickformat=",.0f", showgrid=True, gridcolor=LINE)
        spend_fig.update_yaxes(title=None, tickfont={"color": INK})
        show_chart(style_figure(spend_fig, height=420))

with health_tab:
    left, right = st.columns(2, gap="large")
    with left:
        show_chart(breakdown_chart(user, HEALTH_LABELS, SCORE_WEIGHTS, "Financial health index by part"))
        history_fig = px.area(
            user_history, x="month", y="financial_health_score", title="Score over the year"
        )
        history_fig.update_traces(line={"color": MINT, "width": 2.5}, fillcolor=MINT_SOFT)
        history_fig.add_hline(
            y=60,
            line_dash="dot",
            line_color=MUTED,
            annotation_text="Healthy from 60",
            annotation_font_color=MUTED,
        )
        history_fig.update_xaxes(title=None, dtick="M2", tickformat="%b")
        history_fig.update_yaxes(title=None, range=[0, 100])
        show_chart(style_figure(history_fig, height=260))
    with right:
        show_chart(breakdown_chart(user, CREDIT_LABELS, CREDIT_READINESS_WEIGHTS, "Credit readiness by part"))
        st.caption(
            "Bars show each part's score out of 100; the percentage is its weight in the composite. "
            "Colours follow the app: green from 60, blue from 40, amber from 25, red below."
        )

with coach_tab:
    left, right = st.columns([0.55, 0.45], gap="large")
    with left:
        st.markdown(
            f"""
            <div class="focus-card">
              <div class="eyebrow">Focus area · {rec["priority_dimension"].title()}</div>
              <h3>{rec["recommendation"]}</h3>
              <p>{rec["explanation"]}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="eyebrow" style="margin:16px 0 8px">Action plan</div>', unsafe_allow_html=True
        )
        steps = plan_steps(rec["priority_dimension"], user.to_dict())
        steps_html = "".join(step_html(n, step) for n, step in enumerate(steps, start=1))
        st.markdown(steps_html, unsafe_allow_html=True)
    with right:
        st.markdown('<div class="eyebrow" style="margin-bottom:8px">Risk flags</div>', unsafe_allow_html=True)
        flags_html = ""
        for flag in user_flags.itertuples():
            color, background = TONES["good"] if flag.severity == "low" else TONES[BAND_TONES[flag.severity]]
            flags_html += f"""<div class="flag" style="background:{background}">
              <div style="color:{color};font-weight:800">●</div>
              <div><div class="flag-title">{flag.flag}
              <span style="color:{color};font-size:12px;margin-left:6px">{flag.severity.title()}</span></div>
              <div class="flag-body">{flag.explanation}</div></div></div>"""
        st.markdown(flags_html, unsafe_allow_html=True)
        st.markdown(
            '<div class="notice">These insights are educational decision-support signals. '
            "They are not credit approval, credit pricing, investment advice, "
            "or regulated financial advice.</div>",
            unsafe_allow_html=True,
        )

with simulator_tab:
    input_cols = st.columns(3, gap="large")
    loan_amount = input_cols[0].slider("Loan amount (CHF)", 1_000, 60_000, 10_000, step=500, format="%d")
    annual_rate_pct = input_cols[1].slider(
        "Annual interest rate (%)", 0.0, 15.0, 5.0, step=0.1, format="%.1f"
    )
    term_years = input_cols[2].slider("Term (years)", 1, 10, 3)

    result = simulate_loan_affordability(
        avg_income=user["avg_income"],
        avg_free_cashflow=user["avg_free_cashflow"],
        avg_debt_to_income=user["avg_debt_to_income"],
        loan_amount=loan_amount,
        annual_rate=annual_rate_pct / 100,
        term_years=term_years,
    )

    result_cols = st.columns(3)
    result_cols[0].metric("Monthly payment", chf(result.monthly_payment))
    result_cols[1].metric(
        f"Debt payments vs income · guideline {AFFORDABILITY_CEILING:.0%}",
        f"{result.resulting_debt_to_income:.1%}",
    )
    result_cols[2].metric("Free cashflow after payment", chf(result.projected_free_cashflow))

    tone = {"affordable": "good", "marginal": "warn", "not recommended": "danger"}[result.verdict]
    color, background = TONES[tone]
    st.markdown(
        f"""<div class="flag" style="background:{background};margin-top:12px">
          <div><div class="flag-title" style="color:{color}">{result.verdict.title()}</div>
          <div class="flag-body" style="color:{INK}">{result.explanation}</div></div></div>""",
        unsafe_allow_html=True,
    )

with segments_tab:
    scatter = px.scatter(
        users,
        x="avg_savings_rate",
        y="avg_debt_to_income",
        color="segment_label",
        size="credit_readiness_score",
        size_max=16,
        hover_data={"user_id": True, "health_band": True, "credit_readiness_band": True},
        title="Customers by savings rate and debt load",
        color_discrete_map=SEGMENT_COLORS,
        labels={"segment_label": "Segment"},
    )
    scatter.update_traces(marker={"opacity": 0.8, "line": {"width": 1, "color": "#fff"}})
    scatter.update_xaxes(title="Savings rate", tickformat=".0%")
    scatter.update_yaxes(title="Debt-to-income", tickformat=".0%")
    style_figure(scatter, height=460)
    # five segment names do not fit beside the title, so the legend goes under the chart
    scatter.update_layout(legend={"y": -0.16, "yanchor": "top", "x": 0, "xanchor": "left"}, margin={"b": 40})
    show_chart(scatter)
    st.markdown(
        '<div class="eyebrow" style="margin:6px 0 8px">Segment centroids</div>', unsafe_allow_html=True
    )
    centroids = data["centroids"].sort_values("financial_health_score", ascending=False).copy()
    for col in ["avg_savings_rate", "avg_debt_to_income", "avg_discretionary_ratio", "income_cv"]:
        centroids[col] = centroids[col] * 100
    st.dataframe(
        centroids[
            [
                "segment_label",
                "financial_health_score",
                "avg_income",
                "avg_savings_rate",
                "avg_debt_to_income",
                "avg_discretionary_ratio",
                "income_cv",
            ]
        ],
        width="stretch",
        hide_index=True,
        column_config={
            "segment_label": "Segment",
            "financial_health_score": st.column_config.NumberColumn("Health", format="%.0f"),
            "avg_income": st.column_config.NumberColumn("Income (CHF)", format="%.0f"),
            "avg_savings_rate": st.column_config.NumberColumn("Savings", format="%.1f%%"),
            "avg_debt_to_income": st.column_config.NumberColumn("Debt / income", format="%.1f%%"),
            "avg_discretionary_ratio": st.column_config.NumberColumn("Discretionary", format="%.1f%%"),
            "income_cv": st.column_config.NumberColumn("Income variation", format="%.1f%%"),
        },
    )
    st.caption("K-Means over five behavioural features; silhouette score 0.63 on the demo population.")

st.caption(
    "Educational prototype with synthetic data. Pulse is a fictional brand created for this project "
    "and is not affiliated with any bank or fintech."
)
