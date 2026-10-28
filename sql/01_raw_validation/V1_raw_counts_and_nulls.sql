-- V1: Validate the RAW catalog table (crawled CSVs) in Athena.
-- Table: dunkin_sales_db.sales  ->  s3://pooja-dunkin-data-engineering-2026/Raw/sales/
-- Verified result: 400000 rows, 400000 unique IDs, 24 stores, 24 files, 0 NULLs,
--                  2026-01-01 .. 2026-12-31, revenue 2078457.84 (71.92 MB scanned).
SELECT
  COUNT(*)                                                  AS total_rows,
  COUNT(DISTINCT transaction_id)                            AS unique_transactions,
  COUNT(DISTINCT store_id)                                  AS stores,
  COUNT(DISTINCT "$path")                                   AS files_read,      -- hidden column: source S3 file
  SUM(CASE WHEN quantity IS NULL THEN 1 ELSE 0 END)         AS null_quantity,
  SUM(CASE WHEN unit_price_usd IS NULL THEN 1 ELSE 0 END)   AS null_unit_price,
  SUM(CASE WHEN total_sales_usd IS NULL THEN 1 ELSE 0 END)  AS null_total_sales,
  SUM(CASE WHEN order_to_delivery_minutes IS NULL THEN 1 ELSE 0 END) AS null_delivery_minutes,
  MIN(order_date)                                           AS first_date,
  MAX(order_date)                                           AS last_date,
  ROUND(SUM(total_sales_usd), 2)                            AS total_revenue_usd
FROM dunkin_sales_db.sales;
