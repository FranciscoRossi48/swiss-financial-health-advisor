-- SQL equivalent of the centroid computation + label_segment() in
-- src/swiss_financial_health/clustering.py. Priority order matches Python's
-- if/elif chain exactly (debt pressure checked first, balanced user is the fallback).

with segments as (
    select * from {{ ref("int_user_segments") }}
),

financial_health as (
    select user_id, financial_health_score from {{ ref("fct_financial_health") }}
),

centroids as (
    select
        s.segment,
        avg(s.avg_income) as avg_income,
        avg(s.avg_savings_rate) as avg_savings_rate,
        avg(s.avg_debt_to_income) as avg_debt_to_income,
        avg(s.avg_discretionary_ratio) as avg_discretionary_ratio,
        avg(s.income_cv) as income_cv,
        avg(f.financial_health_score) as financial_health_score
    from segments as s
    inner join financial_health as f on s.user_id = f.user_id
    group by s.segment
)

select
    *,
    case
        when avg_debt_to_income >= 0.18 then 'Debt pressure'
        when income_cv >= 0.25 then 'Variable income'
        when avg_savings_rate >= 0.20 then 'Stable saver'
        when avg_discretionary_ratio >= 0.25 then 'High discretionary'
        else 'Balanced user'
    end as segment_label
from centroids
