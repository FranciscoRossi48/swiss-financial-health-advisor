-- SQL equivalent of build_user_summary() in src/swiss_financial_health/features.py

select
    user_id,
    profile,
    avg(income) as avg_income,
    avg(expense) as avg_expense,
    avg(savings_rate) as avg_savings_rate,
    avg(debt_to_income) as avg_debt_to_income,
    avg(discretionary_ratio) as avg_discretionary_ratio,
    avg(net_cashflow) as avg_net_cashflow,
    avg(income_cv) as income_cv
from {{ ref('int_monthly_features') }}
group by user_id, profile
