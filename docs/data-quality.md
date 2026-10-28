# Data quality

Quality is checked twice: once **locally** before upload (pandas), and again on **every AWS batch run** (PySpark, inside the Glue job).

## 1. Local validation before upload (pandas), in [`local_prep/`](../local_prep)

| Step | Script | Result |
|---|---|---|
| Find unreadable timestamps | `inspect_timestamp_errors.py`, `check_timestamp_values.py` | 4 bad values found (Store 01, 05, 06) |
| Fix them (with backup) | `fix_timestamp_errors.py` | 4 values corrected |
| Create a global key | `create_transaction_id.py` | `Transaction_ID = Store_ID-Order_ID` (Order_ID alone repeats across stores: 378,000 repeats) |
| Validate the key | `validate_transaction_id.py` | 400,000 unique, 0 duplicates |
| Final report | `Final_Data_Quality_Report.py` | **PASS**: see [`Dunkin_Final_Data_Quality_Summary.txt`](Dunkin_Final_Data_Quality_Summary.txt) |

## 2. Independent check in Athena (raw table)

[`sql/01_raw_validation/`](../sql/01_raw_validation): 400,000 rows, 400,000 unique IDs, 24 stores, 24 files, 0 NULLs, every date and timestamp parseable, revenue **$2,078,457.84**.

## 3. Checks inside every Glue ETL run

Each run gets a `RUN_ID` (UTC time, e.g. `20261016T181511Z`) and writes:

```
data-quality/runs/run_id=<RUN_ID>/part-*.csv       one line per check (always written)
data-quality/rejected/run_id=<RUN_ID>/part-*.csv   rows that failed an error rule (only if any)
```

Report columns: `run_id, run_started_utc, check_name, check_type, value, expected, status`.

| Type | What happens on failure | Checks |
|---|---|---|
| **critical** | Job **stops before touching `processed/`** and the run fails | rows read > 0 · 24 files · 24 stores · rows written + rows rejected = rows read |
| **error** | Row moved to `rejected/`, kept out of `processed/` | missing or unparseable value in any of the 19 columns · duplicate `transaction_id` · `transaction_id` ≠ `store_id-order_id` (store consistency) · quantity ≤ 0 · negative price, gross, subtotal, tax or total · negative delivery minutes · delivered before ordered |
| **warning** | Row kept; count reported as `WARN` | order date ≠ date of order timestamp · negative discount · gross ≠ qty × price · subtotal ≠ gross − discount · total ≠ subtotal + tax (±$0.01) · delivery minutes ≠ timestamp difference (±1 min) |
| **metric** | Reported as `INFO` | rows written · revenue (all rows / written rows) · first/last order date |

## Results

| Run ID | Rows read | Written | Rejected | Errors | Warnings | Revenue in = out |
|---|---|---|---|---|---|---|
| `20261016T180652Z` | 400,000 | 400,000 | 0 | 0 | 0 | ✅ |
| `20261016T181208Z` | 400,000 | 400,000 | 0 | 0 | 0 | ✅ $2,078,457.84 |
| `20261016T181511Z` | 400,000 | 400,000 | 0 | 0 | 0 | ✅ $2,078,457.84 |

| `20261027T222654Z` (current data, after a deliberately stopped alert-test run) | 400,000 | 400,000 | 0 | — | — | ✅ $2,078,457.84 (verified in Athena, P1) |

Repeated runs produced identical output with no duplicates, and a run stopped mid-way was fully recovered by one normal rerun: the job is **idempotent** (it replaces `processed/sales/` on each run).
