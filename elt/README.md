# Cloud ELT Pipeline (GCP + dbt)

A BigQuery + dbt implementation of the same pipeline as
[src/swiss_financial_health/](../src/swiss_financial_health/), following a raw → staging →
intermediate → marts pattern with BigQuery ML for segmentation. See
[docs/elt-architecture.md](../docs/elt-architecture.md) for the full architecture and validation
results against the local pandas pipeline.

This is a separate, optional piece of the project. The public dashboard and API do **not**
depend on it or on GCP being reachable.

## Resources used

| Resource | Value |
| --- | --- |
| GCP project | `swiss-fin-health-tfg` |
| Bucket | `gs://swiss-fin-health-tfg-raw` (`us-central1`, free tier eligible) |
| BigQuery dataset | `swiss_financial_health` (`us-central1`) |
| Budget alert | $1, at 50/90/100% |

## One-time setup

Authenticate the `gcloud` CLI (used by `dbt-bigquery`'s `oauth` method — no key file):

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project swiss-fin-health-tfg
```

Create a Python environment for dbt, separate from the main project's `.venv` (dbt pins
dependency versions that can conflict with the Streamlit/FastAPI stack):

```bash
cd elt
python3 -m venv .venv
source .venv/bin/activate
pip install "dbt-bigquery<2"
```

Add the profile in `profiles.yml.example` to `~/.dbt/profiles.yml` (append it — don't overwrite
any existing profiles you already have there).

## Loading raw data

The raw layer is loaded from the same CSV the local pipeline generates:

```bash
python ../scripts/build_demo_data.py   # regenerates data/synthetic_transactions.csv, if needed
gcloud storage cp ../data/synthetic_transactions.csv \
  gs://swiss-fin-health-tfg-raw/transactions/synthetic_transactions.csv

bq load \
  --source_format=CSV --skip_leading_rows=1 --replace \
  swiss_financial_health.raw_transactions \
  gs://swiss-fin-health-tfg-raw/transactions/synthetic_transactions.csv \
  user_id:STRING,date:DATE,category:STRING,transaction_type:STRING,amount_chf:FLOAT64,profile:STRING
```

## Running the pipeline

```bash
source .venv/bin/activate
dbt debug   # verify the connection
dbt build   # runs every model + test, staging through marts, in dependency order
```

`dbt build` trains the BigQuery ML KMeans model as part of the `int_user_segments` step (see the
`create_segment_model()` macro), so a single command reproduces the whole pipeline from raw data
to segmented, scored users.

## Useful commands

```bash
dbt run --select stg_transactions          # run a single model
dbt test                                    # run only the data tests
dbt docs generate && dbt docs serve         # browse the model docs and lineage graph
```
