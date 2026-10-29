"""
Delete everything the stack created, including ALL data in its bucket (cannot be undone).
The original console-built resources (pooja-dunkin-data-engineering-2026 etc.) are not touched.

    python3 scripts/teardown.py
"""
import sys

import boto3
from botocore.exceptions import ClientError

REGION = "us-east-2"
STACK = "dunkin-pipeline-cfn"

cfn = boto3.client("cloudformation", region_name=REGION)


def main():
    try:
        stack = cfn.describe_stacks(StackName=STACK)["Stacks"][0]
    except ClientError as e:
        if "does not exist" in str(e):
            sys.exit(f"Stack {STACK} does not exist. Nothing to delete.")
        raise
    outputs = {o["OutputKey"]: o["OutputValue"] for o in stack.get("Outputs", [])}
    bucket = outputs.get("BucketName")

    answer = input(f"Delete stack {STACK} and all files in s3://{bucket} ? Type yes: ")
    if answer.strip() != "yes":
        sys.exit("Cancelled.")

    if bucket:
        print(f"== Empty s3://{bucket} (CloudFormation can only delete an empty bucket)")
        boto3.resource("s3", region_name=REGION).Bucket(bucket).objects.all().delete()

    print(f"== Delete stack {STACK} (about 1-2 minutes)")
    cfn.delete_stack(StackName=STACK)
    cfn.get_waiter("stack_delete_complete").wait(StackName=STACK, WaiterConfig={"Delay": 10, "MaxAttempts": 90})
    print("Deleted. (Glue log groups under /aws-glue/ are shared and kept; delete them in CloudWatch if wanted.)")


if __name__ == "__main__":
    main()
