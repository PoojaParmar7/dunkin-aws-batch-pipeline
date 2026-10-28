-- E3: Revenue by store, ranked, with each store's share of total revenue.
SELECT
  RANK() OVER (ORDER BY SUM(total_sales_usd) DESC)                              AS revenue_rank,
  store_id,
  COUNT(*)                                                                       AS transactions,
  SUM(total_sales_usd)                                                           AS revenue_usd,
  ROUND(AVG(total_sales_usd), 2)                                                 AS avg_transaction_usd,
  ROUND(100.0 * SUM(total_sales_usd) / SUM(SUM(total_sales_usd)) OVER (), 2)     AS pct_of_total_revenue
FROM dunkin_sales_db.sales_processed
GROUP BY store_id
ORDER BY revenue_rank;
