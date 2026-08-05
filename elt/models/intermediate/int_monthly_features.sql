-- SQL equivalent of build_monthly_features() in src/swiss_financial_health/features.py

with transactions as (
    select * from {{ ref('stg_transactions') }}
),

monthly as (
    select
        user_id,
        profile,
        date_trunc(transaction_date, month) as month,
        sum(case when transaction_type = 'income' then amount_chf else 0 end) as income,
        sum(case when transaction_type = 'expense' then amount_chf else 0 end) as expense,
        sum(case when transaction_type = 'savings' then amount_chf else 0 end) as savings,
        sum(case when category = 'debt_payment' then amount_chf else 0 end) as debt_payments,
        sum(
            case
                when category in ('restaurants', 'shopping', 'travel', 'subscriptions') then amount_chf
                else 0
            end
        ) as discretionary_spend
    from transactions
    group by user_id, profile, month
),

with_income_stats as (
    select
        *,
        avg(income) over (partition by user_id) as avg_income,
        stddev_samp(income) over (partition by user_id) as income_std
    from monthly
)

select
    user_id,
    profile,
    month,
    income,
    expense,
    savings,
    debt_payments,
    discretionary_spend,
    income - expense - savings as net_cashflow,
    greatest(coalesce(safe_divide(savings + greatest(income - expense - savings, 0), income), 0), 0)
        as savings_rate,
    greatest(coalesce(safe_divide(expense, income), 0), 0) as expense_ratio,
    greatest(coalesce(safe_divide(debt_payments, income), 0), 0) as debt_to_income,
    greatest(coalesce(safe_divide(discretionary_spend, income), 0), 0) as discretionary_ratio,
    avg_income,
    greatest(coalesce(safe_divide(coalesce(income_std, 0), avg_income), 0), 0) as income_cv
from with_income_stats
