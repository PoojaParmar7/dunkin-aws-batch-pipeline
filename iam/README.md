# IAM: least-privilege role for the Glue ETL job

Role **`dunkin-glue-etl-role`** (trusted entity: AWS Glue) has two policies:

| Policy | Type | What it allows |
|---|---|---|
| `AWSGlueServiceRole` | AWS managed | CloudWatch logs, Glue Data Catalog, the job's own script in the `aws-glue-assets-*` bucket. **No access to the data bucket.** |
| [`dunkin-s3-pipeline-access`](dunkin-s3-pipeline-access.json) | Inline | See below |

| Statement | Allows | Why |
|---|---|---|
| `ListOnlyPipelineFolders` | List only `Raw/sales`, `processed`, `data-quality` | Spark lists a folder before reading/writing it |
| `ReadRawOnly` | **Read** `Raw/sales/*`: no write, no delete | Raw data is immutable; the job physically cannot change it |
| `WriteProcessedAndDataQuality` | Read/write/delete in `processed/*` and `data-quality/*` | Delete is needed so a rerun can replace its previous output (idempotent full refresh) |

The bucket keeps **Block Public Access** on. Nothing in this project is public.
