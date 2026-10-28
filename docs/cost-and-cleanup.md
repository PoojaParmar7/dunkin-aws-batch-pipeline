# Cost and cleanup

Region: us-east-2 (Ohio). Prices as listed in the AWS console at build time.

## Measured / estimated cost

| Service | Usage | Cost |
|---|---|---|
| Glue ETL job | 1 run = 0.0736 DPU-hours (2 × G.1X, 2 min 12 s) × $0.44 | **≈ $0.03 per run** |
| Glue crawler | ~10-minute minimum per run | ≈ $0.07 per run |
| Athena | $5 per TB scanned; raw table query = 71.92 MB | ≈ $0.0004 per raw query; less on Parquet |
| S3 storage | ≈ 90 MB (CSV + Parquet + reports) | < $0.01 per month |
| CloudWatch Logs | Small job/crawler logs | Cents or less |
| EventBridge + SNS email | Failure alerts (AWS service events; < 1,000 emails/month) | $0 |

**Nothing runs on a schedule, so there is no ongoing compute cost.** Glue jobs and crawlers cost money only while running.

## Cost guards in place

- Glue job: 2 workers (minimum), **15-minute timeout**, 0 retries.
- Crawler: on-demand only (no schedule).
- Bucket: Block Public Access on.

## Recommended housekeeping (optional, still free tier-friendly)

1. **Athena results expire automatically:** S3 → bucket → *Management* → *Create lifecycle rule* → prefix `athena-results/` → *Expire current versions of objects* after **7 days**.
2. **Log retention:** CloudWatch → *Log groups* → `/aws-glue/jobs/output`, `/aws-glue/jobs/error`, `/aws-glue/crawlers` → *Actions* → *Edit retention setting* → **14 days**.

## Full teardown (only when the project is finished)

Delete in this order (console):
1. Glue → ETL jobs → `dunkin-sales-etl` → Actions → Delete.
2. Glue → Crawlers → `dunkin-sales-crawler` → Delete.
3. Glue → Databases → `dunkin_sales_db` → Delete (removes the `sales` and `sales_processed` table definitions, not the S3 data).
4. S3 → `pooja-dunkin-data-engineering-2026` → *Empty*, then *Delete*.
5. S3 → `aws-glue-assets-<account-id>-us-east-2` (job scripts, Spark logs) → Empty → Delete.
6. EventBridge → Rules → `dunkin-glue-job-failed` → Delete; SNS → Topics → `dunkin-pipeline-alerts` → Delete.
7. IAM → Roles → `dunkin-glue-etl-role` → Delete (and the crawler's role if no longer used).
8. CloudWatch → Log groups → delete the `/aws-glue/...` groups.
