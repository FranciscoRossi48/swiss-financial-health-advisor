-- SQL equivalent of compute_financial_health_score() in src/swiss_financial_health/scoring.py
-- Threshold rationale: docs/scoring-methodology.md in the repo root.

with user_summary as (
    select * from {{ ref('int_user_summary') }}
),

component_scores as (
    select
        user_id,
        profile,
        avg_income,
        avg_expense,
        avg_net_cashflow,
        avg_savings_rate,
        avg_debt_to_income,
        avg_discretionary_ratio,
        income_cv,
        {{ scale_higher_is_better('safe_divide(greatest(avg_net_cashflow, 0), avg_expense)', 0.25, 0.75) }}
            as liquidity_score,
        {{ scale_lower_is_better('income_cv', 0.10, 0.35) }} as income_stability_score,
        {{ scale_higher_is_better('avg_savings_rate', 0.10, 0.25) }} as savings_score,
        {{ scale_lower_is_better('avg_debt_to_income', 0.05, 0.25) }} as debt_score
    from user_summary
),

with_total as (
    select
        *,
        round(
            0.30 * liquidity_score
            + 0.20 * income_stability_score
            + 0.30 * savings_score
            + 0.20 * debt_score,
            1
        ) as financial_health_score
    from component_scores
)

select
    *,
    case
        when financial_health_score <= 39 then 'critical'
        when financial_health_score <= 59 then 'fragile'
        when financial_health_score <= 79 then 'healthy'
        else 'strong'
    end as health_band
from with_total
