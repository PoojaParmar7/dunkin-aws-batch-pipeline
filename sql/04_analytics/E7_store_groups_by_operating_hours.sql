-- E7: Store comparison by operating pattern. Opening hours are DERIVED from each store's sales
-- (not typed in), so this query independently checks the simulated design:
-- 6 x 24-hour, 12 x about 4 AM-9 PM, 6 x about 6 AM-6 PM.
WITH store_profile AS (
  SELECT
    store_id,
    MIN(order_hour)            AS first_hour,
    MAX(order_hour)            AS last_hour,
    COUNT(DISTINCT order_hour) AS active_hours,
    COUNT(*)                   AS transactions,
    SUM(total_sales_usd)       AS revenue_usd
  FROM dunkin_sales_db.sales_processed
  GROUP BY store_id
)
SELECT
  CASE WHEN active_hours = 24 THEN '1. 24-hour'
       WHEN active_hours >= 15 THEN '2. Extended (about 4 AM-9 PM)'
       ELSE '3. Daytime (about 6 AM-6 PM)' END              AS store_group,
  COUNT(*)                                                   AS stores,
  array_join(array_agg(store_id ORDER BY store_id), ', ')    AS store_list,
  SUM(transactions)                                          AS transactions,
  SUM(revenue_usd)                                           AS revenue_usd,
  ROUND(AVG(revenue_usd), 2)                                 AS avg_revenue_per_store_usd,
  MIN(first_hour)                                            AS earliest_hour,
  MAX(last_hour)                                             AS latest_hour
FROM store_profile
GROUP BY 1
ORDER BY 1;
