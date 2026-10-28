-- P1: Reconcile the PROCESSED table with the raw data.
-- Verified result (latest: 2026-10-27): one run_id (20261027T222654Z), 400000 rows, 400000 unique IDs, 24 stores,
--                  revenue 2078457.84 (identical to raw), 2026-01-01 .. 2026-12-31.
SELECT
  run_id,
  COUNT(*)                        AS total_rows,
  COUNT(DISTINCT transaction_id)  AS unique_transactions,
  COUNT(DISTINCT store_id)        AS stores,
  SUM(total_sales_usd)            AS total_revenue_usd,
  MIN(order_timestamp)            AS first_order,
  MAX(order_timestamp)            AS last_order
FROM dunkin_sales_db.sales_processed
GROUP BY run_id;
