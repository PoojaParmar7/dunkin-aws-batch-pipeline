-- E8: Unusual sales days per store (z-score). A day is flagged when its revenue is 3 or more
-- standard deviations from that store's own daily average. Zero rows is a valid result
-- (no extreme days); lower the threshold to 2.5 to see the closest cases.
WITH daily AS (
  SELECT store_id, order_date, CAST(SUM(total_sales_usd) AS double) AS revenue
  FROM dunkin_sales_db.sales_processed
  GROUP BY store_id, order_date
),
store_stats AS (
  SELECT store_id, AVG(revenue) AS avg_rev, STDDEV(revenue) AS sd_rev
  FROM daily
  GROUP BY store_id
)
SELECT
  d.store_id,
  d.order_date,
  ROUND(d.revenue, 2)                                      AS revenue_usd,
  ROUND(s.avg_rev, 2)                                      AS store_avg_daily_usd,
  ROUND((d.revenue - s.avg_rev) / NULLIF(s.sd_rev, 0), 2)  AS z_score,
  CASE WHEN d.revenue > s.avg_rev THEN 'Unusually high' ELSE 'Unusually low' END AS anomaly
FROM daily d
JOIN store_stats s ON d.store_id = s.store_id
WHERE ABS((d.revenue - s.avg_rev) / NULLIF(s.sd_rev, 0)) >= 3
ORDER BY ABS((d.revenue - s.avg_rev) / NULLIF(s.sd_rev, 0)) DESC;
