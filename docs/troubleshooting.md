# Troubleshooting log

Real problems hit while building the pipeline, and how they were diagnosed.

## 1. Glue crawler "Completed" but created no tables

**Symptom:** `dunkin-sales-crawler` finished with status *Completed*, *Tables added: –*, and the log said
`Finished writing to Catalog`, but `dunkin_sales_db` had no tables.

**Diagnosis (read-only CLI checks in CloudShell, in this order):**
1. Account and region: `aws sts get-caller-identity`; bucket region with `aws s3api get-bucket-location` → both `us-east-2`. Ruled out.
2. Crawler settings: `aws glue get-crawler` → database correct, no exclusions, no table prefix. Target path `s3://…/raw/sales/`.
3. Listing that exact path: `aws s3 ls s3://…/raw/sales/` returned **nothing**.
4. Full bucket listing (`aws s3api list-objects-v2`) showed the files under **`Raw/sales/`** (capital R).

**Root cause:** S3 keys are **case-sensitive**. The crawler pointed at `raw/sales/`, an empty location, so it had nothing to classify and "successfully" created nothing.

**Fix:** set the crawler target to `s3://pooja-dunkin-data-engineering-2026/Raw/sales/` and rerun. Result: one table `sales` (all 24 files grouped, because they share a schema), CSV, header skipped, 19 columns.

**Lesson:** a crawler that succeeds with zero tables usually means it found no files. Check the exact path, including letter case, before suspecting IAM.

## 2. AWS CLI output opened a scrolling viewer in CloudShell

Long CLI output opened in `less`, and further pasted commands were swallowed. Fix: `export AWS_PAGER=""` at the start of each CloudShell session.

## 3. Athena "Run" not available

Athena needs a **query result location** before running anything. Set in Athena → Settings → Manage:
`s3://pooja-dunkin-data-engineering-2026/athena-results/` (kept separate from raw/processed/data-quality).

## 4. Glue job run three times

Clicking **Run** more than once created three runs. Each wrote its own quality report, and the processed output was replaced each time (no duplicates). This confirmed the job is idempotent.
