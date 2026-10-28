-- Register the Glue ETL output (Parquet, partitioned by year/month) as an Athena table.
-- Partition projection: Athena derives the partitions from the rules below, so no crawler,
-- MSCK REPAIR or ALTER TABLE ADD PARTITION is needed after each ETL run.
CREATE EXTERNAL TABLE dunkin_sales_db.sales_processed (
  transaction_id            string,
  order_id                  string,
  store_id                  string,
  store_name                string,
  order_date                date,
  order_timestamp           timestamp,
  delivered_timestamp       timestamp,
  order_channel             string,
  payment_method            string,
  product_category          string,
  item                      string,
  quantity                  int,
  unit_price_usd            decimal(12,2),
  gross_sales_usd           decimal(12,2),
  discount_usd              decimal(12,2),
  subtotal_usd              decimal(12,2),
  nj_sales_tax_usd          decimal(12,2),
  total_sales_usd           decimal(12,2),
  order_to_delivery_minutes int,
  store_number              int,
  order_hour                int,
  day_of_week               string,
  day_of_week_num           int,
  source_file               string,
  run_id                    string,
  processed_at              timestamp
)
PARTITIONED BY (order_year int, order_month int)
STORED AS PARQUET
LOCATION 's3://pooja-dunkin-data-engineering-2026/processed/sales/'
TBLPROPERTIES (
  'projection.enabled'          = 'true',
  'projection.order_year.type'  = 'integer',
  'projection.order_year.range' = '2024,2030',
  'projection.order_month.type' = 'integer',
  'projection.order_month.range'= '1,12'
);
