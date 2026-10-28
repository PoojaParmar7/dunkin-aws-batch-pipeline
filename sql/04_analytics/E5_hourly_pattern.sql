-- E5: Sales by hour of day (0-23). Night hours come only from the six 24-hour stores.
SELECT
  order_hour,
  COUNT(*)                                                AS transactions,
  SUM(total_sales_usd)                                    AS revenue_usd,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)      AS pct_of_all_transactions
FROM dunkin_sales_db.sales_processed
GROUP BY order_hour
ORDER BY order_hour;
