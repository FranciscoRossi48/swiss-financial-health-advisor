with source as (
    select * from {{ source('swiss_financial_health', 'raw_transactions') }}
)

select
    user_id,
    cast(date as date) as transaction_date,
    category,
    transaction_type,
    cast(amount_chf as float64) as amount_chf,
    profile
from source
