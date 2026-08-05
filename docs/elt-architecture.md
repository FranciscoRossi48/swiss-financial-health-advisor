# Cloud ELT Architecture (GCP + dbt)

The pandas pipeline in [src/swiss_financial_health/](../src/swiss_financial_health/) is the
system of record for the live demo (Streamlit Cloud dashboard, FastAPI service): it has no
external dependencies, costs nothing to run, and cannot go down because a cloud credential
expired. Alongside it, this repository also implements the same pipeline as a cloud ELT
architecture — Cloud Storage → BigQuery → dbt, with segmentation via BigQuery ML — as a second,
independent implementation of the same logic. It lives entirely under [elt/](../elt/) and does
not affect the local pipeline or either deployed service.

## Why a second implementation, not a replacement

The local pandas pipeline is deliberately simple and auditable (see "Regulated AI
Considerations" in the main README) — every threshold is a plain Python `if`/`else` over a
DataFrame column. Moving that logic into SQL/dbt would mean maintaining the same business rules
in two languages, which is a real cost. The ELT version exists to demonstrate a production-shaped
data platform pattern (raw → staging → intermediate → marts, tested and documented with dbt, ML
via BigQuery ML) without displacing the simpler pipeline that everything else in this repo
depends on.

## Layers

```text
Cloud Storage (gs://swiss-fin-health-tfg-raw)
        |
        v
raw_transactions (BigQuery, native table)
        |
        v
stg_transactions (dbt staging, view — typed, tested)
        |
        v
int_monthly_features, int_user_summary (dbt intermediate, views)
        |
        +--> fct_financial_health
        |
        +--> fct_credit_readiness --> fct_risk_flags
        |
        +--> int_user_segments (BigQuery ML KMeans) --> fct_segment_centroids --> fct_user_segments
        |
        v
fct_recommendations
```

Each dbt model has a direct Python counterpart:

| dbt model | Python equivalent |
| --- | --- |
| `stg_transactions` | input to `features.build_monthly_features` |
| `int_monthly_features` | `features.build_monthly_features` |
| `int_user_summary` | `features.build_user_summary` |
| `fct_financial_health` | `scoring.compute_financial_health_score` |
| `fct_credit_readiness` | `credit_readiness.compute_credit_readiness` |
| `fct_risk_flags` | `credit_readiness.build_risk_flags` |
| `fct_recommendations` | `recommendations.generate_recommendations` |
| `segment_model` + `int_user_segments` | `clustering.fit_user_segments` (KMeans step) |
| `fct_segment_centroids` | `clustering.fit_user_segments` (centroid + `label_segment` step) |

## Segmentation: BigQuery ML instead of scikit-learn

`segment_model` is a native `CREATE MODEL ... OPTIONS(model_type='kmeans', ...)` BigQuery ML
model (created by the `create_segment_model()` macro, wired in as a `pre_hook` on
`int_user_segments` since this dbt-bigquery version has no built-in materialization for BQML).
`standardize_features=true` replaces the Python pipeline's `StandardScaler` step, and
`num_clusters=5` matches its `n_clusters` default.

## Validation against the local pipeline

Both implementations were run against the *same* synthetic data (the same
`data/synthetic_transactions.csv`, uploaded as-is to the bucket) and compared row by row:

| Output | Rows compared | Mismatches |
| --- | --- | --- |
| `fct_financial_health` (score + band) | 150 | 0 |
| `fct_credit_readiness` (score + band) | 150 | 6, all ±0.1 points, see below |
| `fct_risk_flags` (flag, severity, explanation) | 236 | 0 |
| `fct_recommendations` (dimension, recommendation, explanation) | 150 | 0 |
| Segment labels and centroid characteristics | 5 segments | Same 5 labels, centroids within rounding of the local `segment_centroids.csv` |

The 6 credit readiness mismatches are a floating-point rounding-boundary artifact, not a logic
error: for those users, the exact weighted sum of the (already-rounded) component scores lands
on a value that rounds to X.X5 — e.g. for one user the true sum is exactly `55.35`. BigQuery's
floating-point evaluation of that sum lands a hair below it (`55.349999999999994`, rounds to
`55.3`); pandas' evaluation, summing the same terms in a different order, lands a hair at or above
it (rounds to `55.4`). Neither is "wrong" — both are correct roundings of their own
floating-point-computed sum, which happens to differ in the 15th significant digit purely from
floating-point non-associativity. None of the 6 cases change a `credit_readiness_band`.
Reproducing this bit-for-bit would require exact/decimal arithmetic on both sides, which is not
worth the complexity for a heuristic 0-100 score.
