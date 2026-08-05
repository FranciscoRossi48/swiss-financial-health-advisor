-- SQL equivalent of generate_recommendations() in src/swiss_financial_health/recommendations.py
-- Tie-break order matches Python's min() over [liquidity, income_stability, savings, debt] exactly:
-- the CASE WHEN below checks dimensions in that same order, so ties resolve to the same winner.

with financial_health as (
    select * from {{ ref('fct_financial_health') }}
),

weakest as (
    select
        *,
        least(liquidity_score, income_stability_score, savings_score, debt_score) as min_score
    from financial_health
),

labeled as (
    select
        user_id,
        avg_net_cashflow,
        income_cv,
        avg_savings_rate,
        avg_debt_to_income,
        case
            when liquidity_score = min_score then 'liquidity_score'
            when income_stability_score = min_score then 'income_stability_score'
            when savings_score = min_score then 'savings_score'
            else 'debt_score'
        end as priority_dimension_key
    from weakest
)

select
    user_id,
    case priority_dimension_key
        when 'liquidity_score' then 'liquidity'
        when 'income_stability_score' then 'income stability'
        when 'savings_score' then 'savings capacity'
        else 'debt exposure'
    end as priority_dimension,
    case priority_dimension_key
        when 'liquidity_score' then 'Build a short-term cash buffer before increasing discretionary spending.'
        when 'income_stability_score'
            then 'Use a conservative monthly baseline and route irregular income toward savings.'
        when 'savings_score'
            then 'Automate a savings transfer near payday and target a first milestone of 10% of income.'
        else 'Prioritize high-interest debt payments and avoid adding new recurring credit obligations.'
    end as recommendation,
    case priority_dimension_key
        when 'liquidity_score'
            then format(
                'Average monthly net cashflow is CHF %.0f, limiting resilience to unexpected expenses.',
                avg_net_cashflow
            )
        when 'income_stability_score'
            then format('Income coefficient of variation is %.2f, indicating relatively uneven inflows.', income_cv)
        when 'savings_score'
            then format(
                'Average savings rate is %.1f%%, below a sustainable long-term target.', avg_savings_rate * 100
            )
        else format('Debt payments represent %.1f%% of monthly income.', avg_debt_to_income * 100)
    end as explanation
from labeled
