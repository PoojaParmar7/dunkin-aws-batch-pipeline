"""
Dunkin' Donuts (simulated franchise data) - batch ETL job
Raw CSV (Raw/sales/)  ->  clean, typed Parquet (processed/sales/), split by month
Each run gets a RUN_ID; its data-quality results go to data-quality/runs/run_id=<RUN_ID>/
Rows that fail a check go to data-quality/rejected/run_id=<RUN_ID>/ (never silently dropped).
The raw files are only read, never changed.

Runs as: AWS Glue 5.0 Spark job, Python 3, 2 x G.1X workers, 15-minute timeout.
"""
import re
import sys
from datetime import datetime, timezone

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql import Window
from pyspark.sql import functions as F

# ---------------------------------------------------------------- 1. Settings
BUCKET = "s3://pooja-dunkin-data-engineering-2026"
RAW_PATH = f"{BUCKET}/Raw/sales/"            # capital R, as in the bucket
PROCESSED_PATH = f"{BUCKET}/processed/sales/"
EXPECTED_FILES = 24
EXPECTED_STORES = 24

EXPECTED_COLUMNS = [
    "transaction_id", "order_id", "store_id", "store_name",
    "order_date", "order_timestamp", "delivered_timestamp",
    "order_channel", "payment_method", "product_category", "item",
    "quantity", "unit_price_usd", "gross_sales_usd", "discount_usd",
    "subtotal_usd", "nj_sales_tax_usd", "total_sales_usd",
    "order_to_delivery_minutes",
]
MONEY_COLUMNS = ["unit_price_usd", "gross_sales_usd", "discount_usd",
                 "subtotal_usd", "nj_sales_tax_usd", "total_sales_usd"]

# ---------------------------------------------------------------- 2. Start the job
args = getResolvedOptions(sys.argv, ["JOB_NAME"])
sc = SparkContext()
glue_context = GlueContext(sc)
spark = glue_context.spark_session
job = Job(glue_context)
job.init(args["JOB_NAME"], args)

# An unreadable date becomes NULL (and is counted as a failed check) instead of crashing the job.
spark.conf.set("spark.sql.legacy.timeParserPolicy", "CORRECTED")

run_started = datetime.now(timezone.utc)
RUN_ID = run_started.strftime("%Y%m%dT%H%M%SZ")          # e.g. 20261016T181500Z
DQ_PATH = f"{BUCKET}/data-quality/runs/run_id={RUN_ID}/"
REJECTED_PATH = f"{BUCKET}/data-quality/rejected/run_id={RUN_ID}/"
print(f"RUN_ID = {RUN_ID}")

# ---------------------------------------------------------------- 3. Read raw CSVs as plain text
raw = (spark.read
       .option("header", True)
       .option("inferSchema", False)      # we set the types ourselves, below
       .csv(RAW_PATH))

# Header names -> lowercase_with_underscores (same style as the Glue catalog table).
def clean_name(name):
    return re.sub(r"[^0-9a-z]+", "_", name.strip().lower()).strip("_")

raw = raw.toDF(*[clean_name(c) for c in raw.columns])
missing_cols = [c for c in EXPECTED_COLUMNS if c not in raw.columns]
if missing_cols:
    raise ValueError(f"Raw files are missing columns: {missing_cols}. Found: {raw.columns}")

raw = raw.select(*EXPECTED_COLUMNS).withColumn("source_file", F.input_file_name())

# Trim spaces; empty text becomes NULL so it is caught by the "missing" checks.
for c in EXPECTED_COLUMNS:
    raw = raw.withColumn(c, F.when(F.trim(F.col(c)) == "", None).otherwise(F.trim(F.col(c))))

# ---------------------------------------------------------------- 4. Set proper data types
typed = (raw
    .withColumn("order_date", F.to_date("order_date", "yyyy-MM-dd"))
    .withColumn("order_timestamp", F.to_timestamp("order_timestamp", "yyyy-MM-dd HH:mm:ss"))
    .withColumn("delivered_timestamp", F.to_timestamp("delivered_timestamp", "yyyy-MM-dd HH:mm:ss"))
    .withColumn("quantity", F.col("quantity").cast("int"))
    .withColumn("order_to_delivery_minutes", F.col("order_to_delivery_minutes").cast("int")))
for c in MONEY_COLUMNS:
    typed = typed.withColumn(c, F.col(c).cast("decimal(12,2)"))   # exact cents, no float rounding

# ---------------------------------------------------------------- 5. Add columns for analysis
typed = (typed
    .withColumn("store_number", F.regexp_extract("store_id", r"(\d+)", 1).cast("int"))  # "Store 24" -> 24
    .withColumn("order_hour", F.hour("order_timestamp"))
    .withColumn("day_of_week", F.date_format("order_date", "EEEE"))       # Monday, Tuesday, ...
    .withColumn("day_of_week_num", F.dayofweek("order_date"))             # 1 = Sunday ... 7 = Saturday
    .withColumn("order_year", F.year("order_date"))
    .withColumn("order_month", F.month("order_date"))
    .withColumn("run_id", F.lit(RUN_ID))
    .withColumn("processed_at", F.current_timestamp()))

# Number each copy of a transaction_id; copy 2, 3, ... are duplicates.
dup_window = Window.partitionBy("transaction_id").orderBy("source_file", "order_timestamp")
typed = typed.withColumn("dup_rank", F.row_number().over(dup_window))

# ---------------------------------------------------------------- 6. Data-quality rules
# ERROR rules: a row that breaks one is moved to the rejected folder.
error_rules = {f"missing_or_invalid_{c}": F.col(c).isNull() for c in EXPECTED_COLUMNS}
error_rules.update({
    "duplicate_transaction_id":     F.col("dup_rank") > 1,
    "transaction_id_not_store_plus_order":
        F.col("transaction_id") != F.concat_ws("-", "store_id", "order_id"),
    "store_number_unreadable":      F.col("store_number").isNull(),
    "quantity_not_positive":        F.col("quantity") <= 0,
    "negative_unit_price":          F.col("unit_price_usd") < 0,
    "negative_gross_sales":         F.col("gross_sales_usd") < 0,
    "negative_subtotal":            F.col("subtotal_usd") < 0,
    "negative_sales_tax":           F.col("nj_sales_tax_usd") < 0,
    "negative_total_sales":         F.col("total_sales_usd") < 0,
    "negative_delivery_minutes":    F.col("order_to_delivery_minutes") < 0,
    "delivered_before_ordered":     F.col("delivered_timestamp") < F.col("order_timestamp"),
})

# WARNING rules: counted in the report, but the row is kept.
seconds_between = F.unix_timestamp("delivered_timestamp") - F.unix_timestamp("order_timestamp")
warning_rules = {
    "order_date_differs_from_timestamp": F.to_date("order_timestamp") != F.col("order_date"),
    "negative_discount":                 F.col("discount_usd") < 0,
    "gross_not_qty_times_price":
        F.abs(F.col("gross_sales_usd") - F.col("quantity") * F.col("unit_price_usd")) > 0.01,
    "subtotal_not_gross_minus_discount":
        F.abs(F.col("subtotal_usd") - (F.col("gross_sales_usd") - F.col("discount_usd"))) > 0.01,
    "total_not_subtotal_plus_tax":
        F.abs(F.col("total_sales_usd") - (F.col("subtotal_usd") + F.col("nj_sales_tax_usd"))) > 0.01,
    "delivery_minutes_differ_from_timestamps":
        F.abs(F.col("order_to_delivery_minutes") - seconds_between / 60) > 1,
}

def broken_rules(rules):
    """List of the rule names this row breaks (empty list = row is fine)."""
    flags = [F.when(condition, F.lit(name)) for name, condition in rules.items()]
    return F.filter(F.array(*flags), lambda x: x.isNotNull())

checked = (typed
    .withColumn("dq_errors", broken_rules(error_rules))
    .withColumn("dq_warnings", broken_rules(warning_rules))
    .cache())
is_good = F.size("dq_errors") == 0

# ---------------------------------------------------------------- 7. Count everything in one pass
count_if = lambda condition: F.sum(F.when(condition, 1).otherwise(0))
all_rules = ([(n, "error", c) for n, c in error_rules.items()] +
             [(n, "warning", c) for n, c in warning_rules.items()])

stats = checked.agg(
    F.count(F.lit(1)).alias("rows_read"),
    F.countDistinct("source_file").alias("files_read"),
    F.countDistinct("store_id").alias("stores"),
    F.countDistinct("transaction_id").alias("unique_transaction_ids"),
    count_if(is_good).alias("rows_written"),
    count_if(~is_good).alias("rows_rejected"),
    F.sum("total_sales_usd").alias("revenue_all_rows"),
    F.sum(F.when(is_good, F.col("total_sales_usd"))).alias("revenue_written"),
    F.min("order_date").alias("first_date"),
    F.max("order_date").alias("last_date"),
    *[count_if(c).alias(n) for n, _, c in all_rules],
).collect()[0]

# ---------------------------------------------------------------- 8. Build the data-quality report
report = []
def add(check, check_type, value, expected="", passed=None):
    if passed is None:
        status = "INFO"
    elif passed:
        status = "PASS"
    else:
        status = "WARN" if check_type == "warning" else "FAIL"
    report.append((RUN_ID, run_started.isoformat(), check, check_type, str(value), str(expected), status))

add("rows_read", "critical", stats.rows_read, "> 0", stats.rows_read > 0)
add("files_read", "critical", stats.files_read, EXPECTED_FILES, stats.files_read == EXPECTED_FILES)
add("stores", "critical", stats.stores, EXPECTED_STORES, stats.stores == EXPECTED_STORES)
add("row_count_reconciles", "critical",
    f"{stats.rows_written} written + {stats.rows_rejected} rejected", stats.rows_read,
    stats.rows_written + stats.rows_rejected == stats.rows_read)
add("unique_transaction_ids", "error", stats.unique_transaction_ids, stats.rows_read,
    stats.unique_transaction_ids == stats.rows_read)
add("rows_rejected", "error", stats.rows_rejected, 0, stats.rows_rejected == 0)
for name, check_type, _ in all_rules:
    add(name, check_type, stats[name], 0, stats[name] == 0)
add("rows_written", "metric", stats.rows_written)
add("revenue_all_rows_usd", "metric", stats.revenue_all_rows)
add("revenue_written_usd", "metric", stats.revenue_written)
add("first_order_date", "metric", stats.first_date)
add("last_order_date", "metric", stats.last_date)

report_df = spark.createDataFrame(
    report, ["run_id", "run_started_utc", "check_name", "check_type", "value", "expected", "status"])
report_df.coalesce(1).write.mode("overwrite").option("header", True).csv(DQ_PATH)
report_df.select("check_name", "value", "expected", "status").show(100, truncate=False)

# Stop BEFORE touching processed/ if the batch itself looks wrong (e.g. a store file is missing).
critical_failures = [r[2] for r in report if r[3] == "critical" and r[6] == "FAIL"]
if critical_failures:
    raise RuntimeError(f"Critical checks failed: {critical_failures}. "
                       f"processed/ was NOT changed. See {DQ_PATH}")

# ---------------------------------------------------------------- 9. Write clean data as Parquet
OUTPUT_COLUMNS = EXPECTED_COLUMNS + [
    "store_number", "order_hour", "day_of_week", "day_of_week_num",
    "source_file", "run_id", "processed_at", "order_year", "order_month"]

(checked.filter(is_good)
    .select(*OUTPUT_COLUMNS)
    .repartition("order_year", "order_month")        # one file per month
    .write.mode("overwrite")                          # full refresh: replaces the previous run's output
    .partitionBy("order_year", "order_month")         # folders: order_year=2026/order_month=1/ ...
    .parquet(PROCESSED_PATH))

# ---------------------------------------------------------------- 10. Save rejected rows (if any)
if stats.rows_rejected > 0:
    (checked.filter(~is_good)
        .withColumn("dq_errors", F.array_join("dq_errors", ";"))
        .withColumn("dq_warnings", F.array_join("dq_warnings", ";"))
        .drop("dup_rank")
        .coalesce(1).write.mode("overwrite").option("header", True).csv(REJECTED_PATH))

print(f"Done. RUN_ID={RUN_ID} written={stats.rows_written} rejected={stats.rows_rejected}")
job.commit()
