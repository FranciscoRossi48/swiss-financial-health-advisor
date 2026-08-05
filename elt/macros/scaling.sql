{#
  SQL equivalents of scale_higher_is_better / scale_lower_is_better in
  src/swiss_financial_health/scoring.py. Both clip the scaled value to [0, 1],
  convert to a 0-100 score, and treat NULL (division by zero, missing data) as
  the worst case (0) — mirroring pandas' .clip(0, 1).fillna(0) there.
#}

{% macro scale_higher_is_better(expression, good, excellent) %}
    round(
        coalesce(
            greatest(least(safe_divide(({{ expression }}) - ({{ good }}), ({{ excellent }}) - ({{ good }})), 1), 0),
            0
        ) * 100,
        1
    )
{% endmacro %}

{% macro scale_lower_is_better(expression, good, poor) %}
    round(
        coalesce(
            greatest(least(1 - safe_divide(({{ expression }}) - ({{ good }}), ({{ poor }}) - ({{ good }})), 1), 0),
            0
        ) * 100,
        1
    )
{% endmacro %}
