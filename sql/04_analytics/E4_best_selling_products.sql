-- E4: Top 10 products by units sold.
SELECT
  product_category,
  item,
  SUM(quantity)                    AS units_sold,
  COUNT(*)                         AS transactions,
  SUM(total_sales_usd)             AS revenue_usd,
  ROUND(AVG(unit_price_usd), 2)    AS avg_unit_price_usd
FROM dunkin_sales_db.sales_processed
GROUP BY product_category, item
ORDER BY units_sold DESC
LIMIT 10;
