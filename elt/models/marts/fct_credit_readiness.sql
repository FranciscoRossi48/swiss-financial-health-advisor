-- SQL equivalent of compute_credit_readiness() in src/swiss_financial_health/credit_readiness.py
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
        {{ scale_lower_is_better('income_cv', 0.08, 0.30) }} as income_reliability_score,
        {{ scale_lower_is_better('avg_debt_to_income', 0.08, 0.30) }} as debt_capacity_score,
        {{ scale_higher_is_better('safe_divide(avg_net_cashflow, avg_income)', 0.05, 0.22) }}
            as cashflow_resilience_score,
        {{ scale_higher_is_better('avg_savings_rate', 0.08, 0.22) }} as savings_discipline_score,
        {{ scale_lower_is_better('avg_discretionary_ratio', 0.16, 0.34) }} as spending_control_score
    from user_summary
),

with_total as (
    select
        *,
        round(
            0.25 * income_reliability_score
            + 0.25 * debt_capacity_score
            + 0.25 * cashflow_resilience_score
            + 0.15 * savings_discipline_score
            + 0.10 * spending_control_score,
            1
        ) as credit_readiness_score
    from component_scores
)

select
    *,
    case
        when credit_readiness_score <= 39 then 'not ready'
        when credit_readiness_score <= 59 then 'needs improvement'
        when credit_readiness_score <= 74 then 'moderate'
        else 'ready'
    end as credit_readiness_band
from with_total
