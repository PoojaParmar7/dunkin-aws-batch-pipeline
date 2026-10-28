#!/usr/bin/env bash
# Read-only checks used during the project. Run in AWS CloudShell (region us-east-2).
# They list and print; they never change anything.
#   bash cloudshell_checks.sh                     -> overview
#   bash cloudshell_checks.sh <RUN_ID>            -> also print non-PASS lines of that run's DQ report
set -euo pipefail
export AWS_PAGER=""                 # stop the CLI from opening a scrolling viewer
REGION=us-east-2
BUCKET=pooja-dunkin-data-engineering-2026

echo "== Account and region"
aws sts get-caller-identity --query Account --output text
echo "CloudShell region: ${AWS_REGION:-unknown}"

echo "== Crawler target and output database"
aws glue get-crawler --name dunkin-sales-crawler --region "$REGION" \
  --query 'Crawler.{Database:DatabaseName,Prefix:TablePrefix,Targets:Targets.S3Targets,LastCrawl:LastCrawl.Status}'

echo "== Catalog tables"
aws glue get-tables --database-name dunkin_sales_db --region "$REGION" \
  --query 'TableList[].[Name,StorageDescriptor.Location]' --output text

echo "== Raw files (S3 keys are case-sensitive: Raw/ not raw/)"
aws s3 ls "s3://$BUCKET/Raw/sales/" --human-readable --summarize | tail -3

echo "== Processed Parquet files"
aws s3 ls "s3://$BUCKET/processed/sales/" --recursive --human-readable --summarize

echo "== Data-quality runs"
aws s3 ls "s3://$BUCKET/data-quality/runs/"

if [[ $# -ge 1 ]]; then
  RUN="$1"
  P="s3://$BUCKET/data-quality/runs/run_id=$RUN/"
  echo "== Non-PASS lines in run $RUN (header only = everything passed)"
  for f in $(aws s3 ls "$P" | awk '/\.csv$/{print $4}'); do aws s3 cp "$P$f" -; done | grep -v ',PASS$'
fi
