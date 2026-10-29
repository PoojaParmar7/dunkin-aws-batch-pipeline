"""
Deploy the whole pipeline in one command (run in AWS CloudShell, from the repo folder).

    python3 scripts/deploy.py you@example.com                  # copies the CSVs from the original bucket
    python3 scripts/deploy.py you@example.com ./my_csv_folder  # uploads the CSVs from a local folder
    python3 scripts/deploy.py you@example.com --schedule on    # also run crawler -> ETL daily (06:00 UTC)

Steps: 1) create or update the CloudFormation stack from infra/pipeline.yaml
       2) upload the Glue ETL script   3) copy the 24 raw CSVs into Raw/sales/
Safe to rerun: CloudFormation only applies what changed, and uploads overwrite the same files.
"""
import argparse
import pathlib
import sys

import boto3
from botocore.exceptions import ClientError, WaiterError

REGION = "us-east-2"
STACK = "dunkin-pipeline-cfn"
DEFAULT_CSV_SOURCE = "s3://pooja-dunkin-data-engineering-2026/Raw/sales/"
REPO = pathlib.Path(__file__).resolve().parent.parent       # works from any folder

cfn = boto3.client("cloudformation", region_name=REGION)
s3 = boto3.client("s3", region_name=REGION)


def stack_status():
    """Current stack status, or None if the stack does not exist yet."""
    try:
        return cfn.describe_stacks(StackName=STACK)["Stacks"][0]["StackStatus"]
    except ClientError as e:
        if "does not exist" in str(e):
            return None
        raise


def print_failures():
    """Show why CloudFormation failed (the first thing to read when a deploy breaks)."""
    for event in cfn.describe_stack_events(StackName=STACK)["StackEvents"][:30]:
        if event["ResourceStatus"].endswith("FAILED"):
            print(f"  {event['LogicalResourceId']}: {event.get('ResourceStatusReason', '')}")


def deploy_stack(email, schedule):
    template = (REPO / "infra" / "pipeline.yaml").read_text()
    settings = dict(
        StackName=STACK,
        TemplateBody=template,
        Capabilities=["CAPABILITY_NAMED_IAM"],              # the template creates a named IAM role
        Parameters=[
            {"ParameterKey": "AlertEmail", "ParameterValue": email},
            {"ParameterKey": "ScheduleEnabled", "ParameterValue": "true" if schedule == "on" else "false"},
        ],
    )
    status = stack_status()
    if status == "ROLLBACK_COMPLETE":
        sys.exit("The first deploy failed and left an empty stack. Run python3 scripts/teardown.py, then deploy again.")

    try:
        if status is None:
            print(f"Creating stack {STACK} (about 1-2 minutes)...")
            cfn.create_stack(**settings)
            waiter = cfn.get_waiter("stack_create_complete")
        else:
            print(f"Updating stack {STACK}...")
            cfn.update_stack(**settings)
            waiter = cfn.get_waiter("stack_update_complete")
        waiter.wait(StackName=STACK, WaiterConfig={"Delay": 10, "MaxAttempts": 90})
    except ClientError as e:
        if "No updates are to be performed" not in str(e):
            raise
        print("Stack already up to date.")
    except WaiterError:
        print("Stack deploy failed:")
        print_failures()
        sys.exit(1)


def stack_outputs():
    outputs = cfn.describe_stacks(StackName=STACK)["Stacks"][0]["Outputs"]
    return {o["OutputKey"]: o["OutputValue"] for o in outputs}


def copy_csvs(source, bucket):
    if source.startswith("s3://"):
        src_bucket, _, prefix = source[len("s3://"):].partition("/")
        pages = s3.get_paginator("list_objects_v2").paginate(Bucket=src_bucket, Prefix=prefix)
        for page in pages:
            for obj in page.get("Contents", []):
                if obj["Key"].endswith(".csv"):
                    name = obj["Key"].rsplit("/", 1)[-1]
                    s3.copy({"Bucket": src_bucket, "Key": obj["Key"]}, bucket, f"Raw/sales/{name}")
                    print(f"  copied {name}")
    else:
        for path in sorted(pathlib.Path(source).glob("*.csv")):
            s3.upload_file(str(path), bucket, f"Raw/sales/{path.name}")
            print(f"  uploaded {path.name}")

    count = sum(obj["Key"].endswith(".csv")
                for page in s3.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix="Raw/sales/")
                for obj in page.get("Contents", []))
    print(f"CSV files now in Raw/sales/: {count} (expected 24)")


def main():
    parser = argparse.ArgumentParser(description="Deploy the Dunkin' pipeline stack.")
    parser.add_argument("email", help="email address for failure alerts")
    parser.add_argument("csv_source", nargs="?", default=DEFAULT_CSV_SOURCE,
                        help="s3://bucket/prefix/ or a local folder with the 24 CSVs")
    parser.add_argument("--schedule", choices=["on", "off"], default="off",
                        help="run crawler -> ETL daily at 06:00 UTC (default: off)")
    args = parser.parse_args()

    print(f"== 1/3 CloudFormation stack {STACK}")
    deploy_stack(args.email, args.schedule)
    bucket = stack_outputs()["BucketName"]

    print(f"== 2/3 Upload ETL script to s3://{bucket}/scripts/")
    s3.upload_file(str(REPO / "glue_jobs" / "dunkin_sales_etl.py"), bucket, "scripts/dunkin_sales_etl.py")

    print(f"== 3/3 Load raw CSVs from {args.csv_source}")
    copy_csvs(args.csv_source, bucket)

    print(f"\nDeployed. Confirm the SNS subscription email sent to {args.email}, then run: python3 scripts/run.py")


if __name__ == "__main__":
    main()
