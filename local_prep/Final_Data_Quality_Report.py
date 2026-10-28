from pathlib import Path
import pandas as pd


# ==========================================================
# CONFIGURATION
# ==========================================================

CSV_FOLDER = Path(
    "/Users/home/Desktop/DunkinDonuts/Data_engineer_project/Dunkin_24_Store_CSV"
)

REPORT_FOLDER = CSV_FOLDER / "data_quality_reports"

REPORT_FOLDER.mkdir(exist_ok=True)

EXPECTED_FILES = 24
EXPECTED_TRANSACTIONS = 400000

EXPECTED_STORES = {
    f"Store {i:02d}" for i in range(1, 25)
}


# ==========================================================
# INITIALIZE RESULTS
# ==========================================================

files = sorted(CSV_FOLDER.glob("Store *_Sales_Data.csv"))

all_transaction_ids = []
all_order_ids = []

total_rows = 0

total_missing = 0
total_duplicate_order_ids_within_file = 0
total_missing_transaction_ids = 0
total_duplicate_transaction_ids_within_file = 0

total_invalid_quantities = 0
total_invalid_prices = 0
total_invalid_sales = 0
total_invalid_dates = 0
total_invalid_timestamps = 0
total_invalid_store_ids = 0
total_store_consistency = 0

stores_found = set()


# ==========================================================
# PROCESS EACH FILE
# ==========================================================

print("=" * 75)
print("DUNKIN 24-STORE FINAL DATA QUALITY REPORT")
print("=" * 75)

print(f"\nCSV files found: {len(files)}")


for csv_file in files:

    print("\n" + "-" * 75)
    print(f"Processing: {csv_file.name}")
    print("-" * 75)

    df = pd.read_csv(csv_file)

    rows = len(df)

    total_rows += rows

    print(f"Rows: {rows:,}")


    # ------------------------------------------------------
    # STORE INFORMATION
    # ------------------------------------------------------

    expected_store = csv_file.stem.replace("_Sales_Data", "")

    stores_found.update(df["Store_ID"].dropna().unique())


    # ------------------------------------------------------
    # MISSING VALUES
    # ------------------------------------------------------

    missing_values = df.isna().sum().sum()

    total_missing += missing_values

    print(f"Missing values: {missing_values}")


    # ------------------------------------------------------
    # ORDER_ID DUPLICATES WITHIN FILE
    # ------------------------------------------------------

    duplicate_order_ids = df["Order_ID"].duplicated().sum()

    total_duplicate_order_ids_within_file += duplicate_order_ids

    print(f"Duplicate Order_IDs within file: {duplicate_order_ids}")


    # ------------------------------------------------------
    # TRANSACTION_ID
    # ------------------------------------------------------

    missing_transaction_ids = df["Transaction_ID"].isna().sum()

    duplicate_transaction_ids = (
        df["Transaction_ID"].duplicated().sum()
    )

    total_missing_transaction_ids += missing_transaction_ids
    total_duplicate_transaction_ids_within_file += duplicate_transaction_ids

    print(
        f"Missing Transaction_IDs: "
        f"{missing_transaction_ids}"
    )

    print(
        f"Duplicate Transaction_IDs within file: "
        f"{duplicate_transaction_ids}"
    )


    # ------------------------------------------------------
    # COLLECT GLOBAL IDS
    # ------------------------------------------------------

    all_transaction_ids.extend(
        df["Transaction_ID"].dropna().astype(str).tolist()
    )

    all_order_ids.extend(
        df["Order_ID"].dropna().astype(str).tolist()
    )


    # ------------------------------------------------------
    # QUANTITY
    # ------------------------------------------------------

    quantity_numeric = pd.to_numeric(
        df["Quantity"],
        errors="coerce"
    )

    invalid_quantity = (
        quantity_numeric.isna()
        | (quantity_numeric <= 0)
        | (quantity_numeric % 1 != 0)
    ).sum()

    total_invalid_quantities += invalid_quantity

    print(f"Invalid quantities: {invalid_quantity}")


    # ------------------------------------------------------
    # UNIT PRICE
    # ------------------------------------------------------

    price_numeric = pd.to_numeric(
        df["Unit_Price_USD"],
        errors="coerce"
    )

    invalid_price = (
        price_numeric.isna()
        | (price_numeric <= 0)
    ).sum()

    total_invalid_prices += invalid_price

    print(f"Invalid prices: {invalid_price}")


    # ------------------------------------------------------
    # SALES AMOUNTS
    # ------------------------------------------------------

    sales_columns = [
        "Gross_Sales_USD",
        "Discount_USD",
        "Subtotal_USD",
        "NJ_Sales_Tax_USD",
        "Total_Sales_USD"
    ]

    invalid_sales = 0

    for column in sales_columns:

        numeric_values = pd.to_numeric(
            df[column],
            errors="coerce"
        )

        invalid_sales += (
            numeric_values.isna()
            | (numeric_values < 0)
        ).sum()

    total_invalid_sales += invalid_sales

    print(f"Invalid sales amounts: {invalid_sales}")


    # ------------------------------------------------------
    # ORDER DATE
    # ------------------------------------------------------

    order_dates = pd.to_datetime(
        df["Order_Date"],
        errors="coerce"
    )

    invalid_dates = order_dates.isna().sum()

    total_invalid_dates += invalid_dates

    print(f"Invalid dates: {invalid_dates}")


    # ------------------------------------------------------
    # TIMESTAMPS
    # ------------------------------------------------------

    order_timestamps = pd.to_datetime(
        df["Order_Timestamp"],
        errors="coerce"
    )

    delivered_timestamps = pd.to_datetime(
        df["Delivered_Timestamp"],
        errors="coerce"
    )

    invalid_timestamps = (
        order_timestamps.isna().sum()
        + delivered_timestamps.isna().sum()
    )

    total_invalid_timestamps += invalid_timestamps

    print(f"Invalid timestamps: {invalid_timestamps}")


    # ------------------------------------------------------
    # STORE ID FORMAT
    # ------------------------------------------------------

    invalid_store_id = (
        ~df["Store_ID"]
        .astype(str)
        .str.match(r"^Store \d{2}$")
    ).sum()

    total_invalid_store_ids += invalid_store_id

    print(f"Invalid Store_ID: {invalid_store_id}")


    # ------------------------------------------------------
    # STORE CONSISTENCY
    # ------------------------------------------------------

    consistency_issues = (
        df["Store_ID"] != expected_store
    ).sum()

    total_store_consistency += consistency_issues

    print(
        f"Store consistency issues: "
        f"{consistency_issues}"
    )


# ==========================================================
# GLOBAL ID VALIDATION
# ==========================================================

transaction_series = pd.Series(all_transaction_ids)

order_series = pd.Series(all_order_ids)


global_duplicate_transaction_ids = (
    transaction_series.duplicated().sum()
)

global_unique_transaction_ids = (
    transaction_series.nunique()
)

global_duplicate_order_ids = (
    order_series.duplicated().sum()
)

global_unique_order_ids = (
    order_series.nunique()
)


# ==========================================================
# STORE COVERAGE
# ==========================================================

missing_stores = EXPECTED_STORES - stores_found

unexpected_stores = stores_found - EXPECTED_STORES


# ==========================================================
# FINAL PASS / FAIL
# ==========================================================

critical_checks_pass = (
    len(files) == EXPECTED_FILES
    and total_rows == EXPECTED_TRANSACTIONS
    and total_missing == 0
    and total_duplicate_order_ids_within_file == 0
    and total_missing_transaction_ids == 0
    and total_duplicate_transaction_ids_within_file == 0
    and global_duplicate_transaction_ids == 0
    and global_unique_transaction_ids == EXPECTED_TRANSACTIONS
    and total_invalid_quantities == 0
    and total_invalid_prices == 0
    and total_invalid_sales == 0
    and total_invalid_dates == 0
    and total_invalid_timestamps == 0
    and total_invalid_store_ids == 0
    and total_store_consistency == 0
    and len(stores_found) == 24
    and len(missing_stores) == 0
    and len(unexpected_stores) == 0
)


if critical_checks_pass:
    overall_status = "PASS"
else:
    overall_status = "FAIL"


# ==========================================================
# DISPLAY FINAL REPORT
# ==========================================================

print("\n")
print("=" * 75)
print("FINAL DATA QUALITY SUMMARY")
print("=" * 75)

print(f"CSV files found: {len(files)}")
print(f"Expected CSV files: {EXPECTED_FILES}")

print(f"\nTotal transactions: {total_rows:,}")
print(f"Expected transactions: {EXPECTED_TRANSACTIONS:,}")

print(f"\nTotal missing values: {total_missing}")

print(
    "Duplicate Order_IDs within files: "
    f"{total_duplicate_order_ids_within_file}"
)

print(
    "Unique Order_IDs across all stores: "
    f"{global_unique_order_ids:,}"
)

print(
    "Duplicate Order_IDs across all stores: "
    f"{global_duplicate_order_ids:,}"
)

print(
    "\nNOTE: Order_ID is store-level and may repeat "
    "across stores."
)

print(
    "\nMissing Transaction_IDs: "
    f"{total_missing_transaction_ids}"
)

print(
    "Duplicate Transaction_IDs within files: "
    f"{total_duplicate_transaction_ids_within_file}"
)

print(
    "Unique Transaction_IDs globally: "
    f"{global_unique_transaction_ids:,}"
)

print(
    "Duplicate Transaction_IDs globally: "
    f"{global_duplicate_transaction_ids}"
)

print(f"\nInvalid quantities: {total_invalid_quantities}")
print(f"Invalid prices: {total_invalid_prices}")
print(f"Invalid sales amounts: {total_invalid_sales}")
print(f"Invalid dates: {total_invalid_dates}")
print(f"Invalid timestamps: {total_invalid_timestamps}")
print(f"Invalid Store_ID values: {total_invalid_store_ids}")
print(f"Store consistency issues: {total_store_consistency}")

print("\nExpected stores: 24")
print(f"Stores found: {len(stores_found)}")
print(f"Missing stores: {missing_stores if missing_stores else 'None'}")
print(
    f"Unexpected stores: "
    f"{unexpected_stores if unexpected_stores else 'None'}"
)

print("\n" + "=" * 75)
print(f"OVERALL DATA QUALITY STATUS: {overall_status}")
print("=" * 75)


# ==========================================================
# SAVE SUMMARY TXT
# ==========================================================

summary_file = (
    REPORT_FOLDER /
    "Dunkin_Final_Data_Quality_Summary.txt"
)

with open(summary_file, "w") as f:

    f.write("DUNKIN 24-STORE FINAL DATA QUALITY REPORT\n")
    f.write("=" * 60 + "\n\n")

    f.write(f"CSV files: {len(files)} / {EXPECTED_FILES}\n")

    f.write(
        f"Transactions: "
        f"{total_rows:,} / {EXPECTED_TRANSACTIONS:,}\n"
    )

    f.write(
        f"Missing values: {total_missing}\n"
    )

    f.write(
        f"Duplicate Order_IDs within files: "
        f"{total_duplicate_order_ids_within_file}\n"
    )

    f.write(
        f"Duplicate Order_IDs across stores: "
        f"{global_duplicate_order_ids:,}\n"
    )

    f.write(
        f"Missing Transaction_IDs: "
        f"{total_missing_transaction_ids}\n"
    )

    f.write(
        f"Duplicate Transaction_IDs globally: "
        f"{global_duplicate_transaction_ids}\n"
    )

    f.write(
        f"Unique Transaction_IDs globally: "
        f"{global_unique_transaction_ids:,}\n"
    )

    f.write(
        f"Invalid quantities: "
        f"{total_invalid_quantities}\n"
    )

    f.write(
        f"Invalid prices: "
        f"{total_invalid_prices}\n"
    )

    f.write(
        f"Invalid sales amounts: "
        f"{total_invalid_sales}\n"
    )

    f.write(
        f"Invalid dates: "
        f"{total_invalid_dates}\n"
    )

    f.write(
        f"Invalid timestamps: "
        f"{total_invalid_timestamps}\n"
    )

    f.write(
        f"Invalid Store_ID values: "
        f"{total_invalid_store_ids}\n"
    )

    f.write(
        f"Store consistency issues: "
        f"{total_store_consistency}\n"
    )

    f.write(
        f"Stores found: {len(stores_found)} / 24\n"
    )

    f.write(
        f"\nOVERALL STATUS: {overall_status}\n"
    )


# ==========================================================
# SAVE CSV REPORT
# ==========================================================

report_data = {
    "Metric": [
        "CSV Files",
        "Total Transactions",
        "Missing Values",
        "Duplicate Order_IDs Within Files",
        "Duplicate Order_IDs Across Stores",
        "Missing Transaction_IDs",
        "Duplicate Transaction_IDs Globally",
        "Unique Transaction_IDs Globally",
        "Invalid Quantities",
        "Invalid Prices",
        "Invalid Sales Amounts",
        "Invalid Dates",
        "Invalid Timestamps",
        "Invalid Store_ID",
        "Store Consistency Issues",
        "Stores Found",
        "Expected Stores",
        "Overall Status"
    ],

    "Value": [
        len(files),
        total_rows,
        total_missing,
        total_duplicate_order_ids_within_file,
        global_duplicate_order_ids,
        total_missing_transaction_ids,
        global_duplicate_transaction_ids,
        global_unique_transaction_ids,
        total_invalid_quantities,
        total_invalid_prices,
        total_invalid_sales,
        total_invalid_dates,
        total_invalid_timestamps,
        total_invalid_store_ids,
        total_store_consistency,
        len(stores_found),
        24,
        overall_status
    ]
}

report_df = pd.DataFrame(report_data)

csv_report_file = (
    REPORT_FOLDER /
    "Dunkin_Final_Data_Quality_Report.csv"
)

report_df.to_csv(
    csv_report_file,
    index=False
)


# ==========================================================
# COMPLETED
# ==========================================================

print("\nReports created:")

print(summary_file)

print(csv_report_file)

print("\nFinal data-quality validation completed.")