"""
Run the pipeline once (crawler -> ETL via the Glue workflow), then check the result in Athena.

    python3 scripts/run.py

Cost: about $0.10 per run (crawler ~ $0.07 + ETL ~ $0.03).
The check reuses sql/03_processed_validation/P1_processed_reconciliation.sql.
"""
import pathlib
import sys
import time
from decimal import Decimal

import boto3

REGION = "us-east-2"
STACK = "dunkin-pipeline-cfn"
REPO = pathlib.Path(__file__).resolve().parent.parent
EXPECTED = {"total_rows": "400000", "unique_transactions": "400000", "stores": "24",
            "total_revenue_usd": "2078457.84"}

cfn = boto3.client("cloudformation", region_name=REGION)
glue = boto3.client("glue", region_name=REGION)
athena = boto3.client("athena", region_name=REGION)


def stack_outputs():
    outputs = cfn.describe_stacks(StackName=STACK)["Stacks"][0]["Outputs"]
    return {o["OutputKey"]: o["OutputValue"] for o in outputs}


def run_workflow(workflow):
    run_id = glue.start_workflow_run(Name=workflow)["RunId"]
    print(f"Workflow run {run_id} started (usually 4-6 minutes: crawler, then ETL)")
    while True:
        run = glue.get_workflow_run(Name=workflow, RunId=run_id)["Run"]
        print(f"{time.strftime('%H:%M:%S')}  workflow {run['Status']}")
        if run["Status"] not in ("RUNNING", "STOPPING"):
            return run
        time.sleep(30)


def check_etl(job, workflow_started):
    """The ETL run must be newer than this workflow run; otherwise the crawler failed and ETL never started."""
    runs = glue.get_job_runs(JobName=job)["JobRuns"]
    if not runs or runs[0]["StartedOn"] < workflow_started:
        sys.exit("ETL did not run: the crawler probably failed. Check Glue -> Crawlers, and the alert email.")
    latest = runs[0]
    print(f"ETL run {latest['Id']}: {latest['JobRunState']} in {latest.get('ExecutionTime', 0)} s")
    if latest["JobRunState"] != "SUCCEEDED":
        sys.exit(f"ETL failed: {latest.get('ErrorMessage', '')}. Check Glue -> ETL jobs -> {job} -> Runs.")


def athena_query(sql, workgroup):
    query_id = athena.start_query_execution(QueryString=sql, WorkGroup=workgroup)["QueryExecutionId"]
    while True:
        status = athena.get_query_execution(QueryExecutionId=query_id)["QueryExecution"]["Status"]
        if status["State"] not in ("QUEUED", "RUNNING"):
            break
        time.sleep(2)
    if status["State"] != "SUCCEEDED":
        sys.exit(f"Athena query {status['State']}: {status.get('StateChangeReason', '')}")
    rows = athena.get_query_results(QueryExecutionId=query_id)["ResultSet"]["Rows"]
    header = [col.get("VarCharValue") for col in rows[0]["Data"]]
    return [dict(zip(header, [col.get("VarCharValue") for col in row["Data"]])) for row in rows[1:]]


def main():
    out = stack_outputs()

    print(f"== Run workflow {out['WorkflowName']}")
    run = run_workflow(out["WorkflowName"])
    stats = run["Statistics"]
    print(f"Steps: {stats.get('SucceededActions', 0)} succeeded, {stats.get('FailedActions', 0)} failed, "
          f"{stats.get('StoppedActions', 0)} stopped, {stats.get('TimeoutActions', 0)} timed out")
    check_etl(out["JobName"], run["StartedOn"])

    print(f"== Reconcile {out['DatabaseName']}.sales_processed in Athena (P1)")
    sql_file = REPO / "sql" / "03_processed_validation" / "P1_processed_reconciliation.sql"
    sql = "\n".join(line for line in sql_file.read_text().splitlines() if not line.startswith("--"))
    sql = sql.replace("dunkin_sales_db.", f"{out['DatabaseName']}.").rstrip().rstrip(";")
    results = athena_query(sql, out["AthenaWorkGroup"])

    all_ok = len(results) == 1          # one run_id: the full refresh replaced older output
    for row in results:
        for name, value in row.items():
            check = ""
            if name in EXPECTED:
                ok = Decimal(value) == Decimal(EXPECTED[name])
                all_ok = all_ok and ok
                check = "PASS" if ok else f"FAIL (expected {EXPECTED[name]})"
            print(f"  {name:20} {str(value):28} {check}")
    print("\nPipeline run verified." if all_ok else "\nReconciliation did NOT match. See above.")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
