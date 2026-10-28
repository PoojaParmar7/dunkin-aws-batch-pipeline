-- V3: Profile the RAW table: can every date/timestamp be parsed, and which category values exist?
-- Verified result: bad_order_date = 0, bad_order_ts = 0, bad_delivered_ts = 0.
SELECT
  SUM(CASE WHEN order_to_delivery_minutes IS NULL THEN 1 ELSE 0 END)                     AS null_delivery_minutes,
  MIN(order_date)                                                                        AS first_date,
  MAX(order_date)                                                                        AS last_date,
  ROUND(SUM(total_sales_usd), 2)                                                         AS total_revenue_usd,
  SUM(CASE WHEN try(date_parse(order_date, '%Y-%m-%d')) IS NULL THEN 1 ELSE 0 END)        AS bad_order_date,
  SUM(CASE WHEN try(date_parse(order_timestamp, '%Y-%m-%d %H:%i:%s')) IS NULL THEN 1 ELSE 0 END)     AS bad_order_ts,
  SUM(CASE WHEN try(date_parse(delivered_timestamp, '%Y-%m-%d %H:%i:%s')) IS NULL THEN 1 ELSE 0 END) AS bad_delivered_ts,
  array_join(array_agg(DISTINCT order_channel), ' | ')                                    AS channels,
  array_join(array_agg(DISTINCT payment_method), ' | ')                                   AS payment_methods,
  array_join(array_agg(DISTINCT product_category), ' | ')                                 AS categories,
  COUNT(DISTINCT item)                                                                   AS distinct_items
FROM dunkin_sales_db.sales;
