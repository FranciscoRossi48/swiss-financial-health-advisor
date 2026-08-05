-- SQL equivalent of build_risk_flags() / risk_flags_for_user() in
-- src/swiss_financial_health/credit_readiness.py

with credit as (
    select * from {{ ref('fct_credit_readiness') }}
),

debt_flags as (
    select
        user_id,
        case when avg_debt_to_income >= 0.25 then 'High debt burden' else 'Elevated debt burden' end as flag,
        case when avg_debt_to_income >= 0.25 then 'high' else 'medium' end as severity,
        case
            when avg_debt_to_income >= 0.25
                then format('Debt payments represent %.1f%% of average monthly income.', avg_debt_to_income * 100)
            else format(
                'Debt payments are above a conservative affordability threshold at %.1f%%.',
                avg_debt_to_income * 100
            )
        end as explanation
    from credit
    where avg_debt_to_income >= 0.18
),

income_flags as (
    select
        user_id,
        case when income_cv >= 0.30 then 'Highly variable income' else 'Variable income' end as flag,
        case when income_cv >= 0.30 then 'high' else 'medium' end as severity,
        case
            when income_cv >= 0.30
                then format('Income coefficient of variation is %.2f, reducing repayment predictability.', income_cv)
            else format('Income volatility is material with a coefficient of variation of %.2f.', income_cv)
        end as explanation
    from credit
    where income_cv >= 0.22
),

cashflow_flags as (
    select
        user_id,
        case
            when safe_divide(avg_net_cashflow, avg_income) < 0 then 'Negative free cashflow'
            else 'Thin cashflow buffer'
        end as flag,
        case when safe_divide(avg_net_cashflow, avg_income) < 0 then 'high' else 'medium' end as severity,
        case
            when safe_divide(avg_net_cashflow, avg_income) < 0
                then 'Average monthly expenses and savings transfers exceed income.'
            else format(
                'Free cashflow is only %.1f%% of average income.',
                coalesce(safe_divide(avg_net_cashflow, avg_income), 0) * 100
            )
        end as explanation
    from credit
    where coalesce(safe_divide(avg_net_cashflow, avg_income), 0) < 0.05
),

savings_flags as (
    select
        user_id,
        'Low savings discipline' as flag,
        'medium' as severity,
        format('Average savings rate is %.1f%%.', avg_savings_rate * 100) as explanation
    from credit
    where avg_savings_rate < 0.05
),

discretionary_flags as (
    select
        user_id,
        'High discretionary spend' as flag,
        'medium' as severity,
        format('Discretionary spending represents %.1f%% of income.', avg_discretionary_ratio * 100) as explanation
    from credit
    where avg_discretionary_ratio >= 0.32
),

all_flags as (
    select * from debt_flags
    union all
    select * from income_flags
    union all
    select * from cashflow_flags
    union all
    select * from savings_flags
    union all
    select * from discretionary_flags
),

no_flag_users as (
    select
        credit.user_id,
        'No major risk flags' as flag,
        'low' as severity,
        'The synthetic profile does not show a dominant credit readiness weakness.' as explanation
    from credit
    left join (select distinct user_id from all_flags) as flagged
        on credit.user_id = flagged.user_id
    where flagged.user_id is null
)

select * from all_flags
union all
select * from no_flag_users
