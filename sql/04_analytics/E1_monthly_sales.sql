-- E1: Monthly sales with month-over-month growth.
-- LAG() looks at the previous month; January has no previous month, so its growth is NULL.
SELECT
  order_year,
  order_month,
  COUNT(*)                         AS transactions,
  SUM(quantity)                    AS items_sold,
  SUM(total_sales_usd)             AS revenue_usd,
  ROUND(AVG(total_sales_usd), 2)   AS avg_transaction_usd,
  ROUND(100.0 * (SUM(total_sales_usd) - LAG(SUM(total_sales_usd)) OVER (ORDER BY order_year, order_month))
        / LAG(SUM(total_sales_usd)) OVER (ORDER BY order_year, order_month), 2) AS pct_change_vs_prev_month
FROM dunkin_sales_db.sales_processed
GROUP BY order_year, order_month
ORDER BY order_year, order_month;
