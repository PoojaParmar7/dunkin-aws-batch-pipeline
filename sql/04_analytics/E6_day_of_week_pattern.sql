-- E6: Sales by day of week. day_of_week_num: 1 = Sunday ... 7 = Saturday.
-- "Average revenue per day" is the fair comparison: 2026 has 53 Thursdays but 52 of every other weekday.
SELECT
  day_of_week_num,
  day_of_week,
  COUNT(*)                                                    AS transactions,
  SUM(total_sales_usd)                                        AS revenue_usd,
  ROUND(SUM(total_sales_usd) / COUNT(DISTINCT order_date), 2) AS avg_revenue_per_day_usd,
  ROUND(AVG(total_sales_usd), 2)                              AS avg_transaction_usd
FROM dunkin_sales_db.sales_processed
GROUP BY day_of_week_num, day_of_week
ORDER BY day_of_week_num;
