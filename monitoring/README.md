# Monitoring: failure alerts

```
Glue job dunkin-sales-etl ends FAILED / TIMEOUT / STOPPED
        │  (Glue publishes a "Glue Job State Change" event automatically)
        ▼
EventBridge rule  dunkin-glue-job-failed   (default event bus, pattern below)
        │
        ▼
SNS topic  dunkin-pipeline-alerts  ──►  email subscription (confirmed)
```

- Event pattern: [`eventbridge-glue-job-failed.json`](eventbridge-glue-job-failed.json)
- **Data-quality failures are covered too:** if a critical check fails (e.g. a store file is missing), the job raises an error *before* writing `processed/`, ends as `FAILED`, and the alert fires.
- **Tested:** a run was started and stopped manually. The `STOPPED` email arrived within seconds. Two identical emails arrived for the same `jobRunId`, because AWS event delivery is *at least once*, so alert consumers should tolerate duplicates.
- **Cost:** ≈ $0. AWS service events on the default bus are free; SNS email is free for the first 1,000 per month.

## Setup (console)
1. **SNS** → Topics → Create topic → Standard → `dunkin-pipeline-alerts` → Create subscription → Email → confirm via the email link.
2. **EventBridge** → Rules → Create rule (Advanced builder) → `dunkin-glue-job-failed`, default bus, *Rule with an event pattern* → *AWS events* → *Custom pattern (JSON editor)* → paste the pattern → Target: *SNS topic* `dunkin-pipeline-alerts` → Create rule.
