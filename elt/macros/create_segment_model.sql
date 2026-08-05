{#
  dbt-bigquery has no native "model" materialization for BigQuery ML in this
  version, so the CREATE MODEL DDL is issued explicitly here and wired in as a
  pre_hook on int_user_segments (see that model's config) — this keeps model
  training part of the normal `dbt run` DAG instead of a separate manual step.

  standardize_features replaces the Python pipeline's StandardScaler
  (see clustering.py); num_clusters=5 matches its n_clusters default.
#}
{% macro create_segment_model() %}
    {% set sql %}
        create or replace model `{{ target.project }}.{{ target.dataset }}.segment_model`
        options (
            model_type = 'kmeans',
            num_clusters = 5,
            standardize_features = true
        ) as
        select
            avg_income,
            avg_savings_rate,
            avg_debt_to_income,
            avg_discretionary_ratio,
            income_cv
        from {{ ref('int_user_summary') }}
    {% endset %}
    {% do run_query(sql) %}
{% endmacro %}
