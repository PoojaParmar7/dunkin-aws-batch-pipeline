-- E2: Daily sales with a 7-day moving average (smooths weekday/weekend swings). 365 rows.
SELECT
  order_date,
  day_of_week,
  COUNT(*)              AS transactions,
  SUM(total_sales_usd)  AS revenue_usd,
  ROUND(AVG(SUM(total_sales_usd)) OVER (ORDER BY order_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 2)
                        AS revenue_7day_avg
FROM dunkin_sales_db.sales_processed
GROUP BY order_date, day_of_week
ORDER BY order_date;
