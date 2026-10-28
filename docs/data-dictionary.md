# Data dictionary

**Dataset:** simulated sales transactions for 24 Dunkin' Donuts franchise stores in New Jersey, calendar year 2026.
This is synthetic data made for learning. It is **not** real Dunkin' corporate data.

## Source profile (from the 24 CSV files)

| Fact | Value |
|---|---|
| Files | 24 (one per store), `Store 01_Sales_Data.csv` … `Store 24_Sales_Data.csv` |
| Rows | 400,000 (one row = one transaction, one item line) |
| Size | 71.9 MiB CSV |
| Date range | 2026-01-01 → 2026-12-31 |
| Order channels | Drive-Thru, Walk-In, Mobile App, Delivery |
| Payment methods | Mobile Pay, Debit Card, Credit Card, Cash |
| Product categories | Bakery, Espresso, Beverage, Breakfast, Lunch, Coffee, Tea, Snack (26 distinct items) |

| Store group | Stores | Hours with sales | Transactions per store |
|---|---|---|---|
| 24-hour, high-selling | Store 01–06 | 00:00–23:59 (24 h) | 22,000 |
| Extended, strong sales | Store 07–18 | 04:00–20:59 (17 h) | 16,500 |
| Daytime, moderate sales | Store 19–24 | 06:00–17:59 (12 h) | ≈ 11,667 |

## Columns

Raw = CSV header / Glue crawler type. Processed = type in `sales_processed` (Parquet).

| Column | Raw type | Processed type | Description |
|---|---|---|---|
| `transaction_id` | string | string | **Global unique key** = `store_id` + `-` + `order_id` (e.g. `Store 24-ORD-2026-00000001`) |
| `order_id` | string | string | Store-local order number; repeats across stores |
| `store_id` | string | string | `Store 01` … `Store 24` |
| `store_name` | string | string | Store name |
| `order_date` | string | date | `YYYY-MM-DD` |
| `order_timestamp` | string | timestamp | `YYYY-MM-DD HH:MM:SS`, order placed |
| `delivered_timestamp` | string | timestamp | `YYYY-MM-DD HH:MM:SS`, order handed over |
| `order_channel` | string | string | See profile above |
| `payment_method` | string | string | See profile above |
| `product_category` | string | string | See profile above |
| `item` | string | string | Product name |
| `quantity` | bigint | int | Units in the transaction (> 0) |
| `unit_price_usd` | double | decimal(12,2) | Price per unit |
| `gross_sales_usd` | double | decimal(12,2) | quantity × unit price |
| `discount_usd` | double | decimal(12,2) | Discount amount |
| `subtotal_usd` | double | decimal(12,2) | gross − discount |
| `nj_sales_tax_usd` | double | decimal(12,2) | New Jersey sales tax |
| `total_sales_usd` | double | decimal(12,2) | subtotal + tax (**revenue** in all analytics) |
| `order_to_delivery_minutes` | bigint | int | Minutes from order to handover |

### Columns added by the ETL job

| Column | Type | Description |
|---|---|---|
| `store_number` | int | 24 from `Store 24` (numeric sorting/filtering) |
| `order_hour` | int | 0–23 from `order_timestamp` |
| `day_of_week` | string | Monday … Sunday |
| `day_of_week_num` | int | 1 = Sunday … 7 = Saturday |
| `source_file` | string | S3 file the row came from (lineage) |
| `run_id` | string | ETL run that wrote the row, e.g. `20261016T181511Z` (lineage) |
| `processed_at` | timestamp | When the row was written |
| `order_year`, `order_month` | int | **Partition columns** (S3 folders `order_year=2026/order_month=1/`) |

Money is stored as `decimal(12,2)`, not floating point, so sums are exact to the cent.
