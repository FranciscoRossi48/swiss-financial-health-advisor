-- Singular dbt test: fails if it returns any rows.
-- Mirrors the non-negative amount check in swiss_financial_health.validation.validate_transactions.
select *
from {{ ref('stg_transactions') }}
where amount_chf < 0
