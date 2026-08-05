{{ config(pre_hook="{{ create_segment_model() }}") }}

-- Applies the BQML KMeans model (trained by the pre_hook above, into
-- segment_model) to every user. ML.PREDICT adds CENTROID_ID (the assigned
-- cluster) alongside the input columns.

select
    user_id,
    profile,
    avg_income,
    avg_savings_rate,
    avg_debt_to_income,
    avg_discretionary_ratio,
    income_cv,
    centroid_id as segment
from
    ml.predict(
        model `{{ target.project }}.{{ target.dataset }}.segment_model`,
        (select * from {{ ref("int_user_summary") }})
    )
