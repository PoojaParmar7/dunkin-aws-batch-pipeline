# Screenshots

Console screenshots, cropped so that no AWS account ID or console URL is visible.
When adding new ones, crop out or blur the **12-digit account ID** (top-right menu and browser address bar).

| File | Shows | Status |
|---|---|---|
| `01-s3-bucket-layout.png` | S3 bucket with `Raw/`, `processed/`, `data-quality/`, `athena-results/` | to add |
| `02-crawler-run.png` | Crawler run: Completed, 1 table added | to add |
| `03-catalog-table-schema.png` | Glue Data Catalog → `sales` table schema (19 columns) | to add |
| [`04-athena-raw-profile.png`](04-athena-raw-profile.png) | Raw profile (V3): 0 bad dates/timestamps, revenue 2078457.84, 71.92 MB scanned | ✅ |
| [`05-glue-job-details.png`](05-glue-job-details.png) | Glue job run: Succeeded, 2 DPUs, 0.0736 DPU-hours | ✅ |
| [`06-dq-report-cloudwatch.png`](06-dq-report-cloudwatch.png) | Job output log: check table, `written=400000 rejected=0` | ✅ |
| [`07-processed-parquet-s3.png`](07-processed-parquet-s3.png) | 12 Parquet files (15.4 MiB) + per-run DQ report | ✅ |
| [`08-athena-processed-check.png`](08-athena-processed-check.png) | P1 reconciliation: one run, 400000 rows, 24 stores, 2078457.84 | ✅ |
| `09-e3-revenue-by-store.png` | E3 result | to add |
| [`10-e7-store-groups.png`](10-e7-store-groups.png) | E7: 6 / 12 / 6 store groups, 656.78 KB scanned | ✅ |
| [`11-iam-role-permissions.png`](11-iam-role-permissions.png) | `dunkin-glue-etl-role` with its two policies | ✅ |
| [`12-e8-anomalies.png`](12-e8-anomalies.png) | E8: 33 anomalous store-days | ✅ |
| [`13-eventbridge-failure-rule.png`](13-eventbridge-failure-rule.png) | EventBridge rule pattern for Glue job failures | ✅ |
