from pathlib import Path
import pandas as pd


# ============================================================
# 1. CONFIGURATION
# ============================================================

# Folder containing the 24 CSV files
input_folder = Path(
    "/Users/home/Desktop/DunkinDonuts/Data_engineer_project/Dunkin_24_Store_CSV"
)

# Folder where validation reports will be saved
report_folder = input_folder / "data_quality_reports"
report_folder.mkdir(exist_ok=True)


# Expected number of stores and transactions
EXPECTED_STORES = 24
EXPECTED_TRANSACTIONS = 400_000


# Expected columns in every CSV file
EXPECTED_COLUMNS = [
    "Order_ID",
    "Store_ID",
    "Store_Name",
    "Order_Date",
    "Order_Timestamp",
    "Delivered_Timestamp",
    "Order_Channel",
    "Payment_Method",
    "Product_Category",
    "Item",
    "Quantity",
    "Unit_Price_USD",
    "Gross_Sales_USD",
    "Discount_USD",
    "Subtotal_USD",
    "NJ_Sales_Tax_USD",
    "Total_Sales_USD",
    "Order_to_Delivery_Minutes"
]


# ============================================================
# 2. FIND CSV FILES
# ============================================================

csv_files = sorted(
    input_folder.glob("Store *_Sales_Data.csv")
)

print("=" * 70)
print("DUNKIN 24-STORE DATA QUALITY VALIDATION")
print("=" * 70)

print(f"\nCSV files found: {len(csv_files)}")

if len(csv_files) != EXPECTED_STORES:
    print(
        f"WARNING: Expected {EXPECTED_STORES} CSV files "
        f"but found {len(csv_files)}."
    )


# ============================================================
# 3. STORAGE FOR REPORT RESULTS
# ============================================================

report_results = []

all_order_ids = []
all_store_ids = []

total_rows = 0
total_missing_values = 0
total_duplicate_order_ids = 0
total_invalid_quantities = 0
total_invalid_prices = 0
total_invalid_sales = 0
total_invalid_dates = 0
total_invalid_timestamps = 0
total_invalid_store_ids = 0
total_invalid_store_names = 0


# ============================================================
# 4. PROCESS EACH CSV FILE
# ============================================================

for csv_file in csv_files:

    print("\n" + "-" * 70)
    print(f"Processing: {csv_file.name}")
    print("-" * 70)

    # --------------------------------------------------------
    # Read CSV
    # --------------------------------------------------------

    try:
        df = pd.read_csv(csv_file)

    except Exception as e:

        print(f"ERROR reading file: {e}")

        report_results.append({
            "File": csv_file.name,
            "Rows": 0,
            "Columns": 0,
            "Missing_Values": "READ ERROR",
            "Duplicate_Order_IDs": "READ ERROR",
            "Invalid_Quantity": "READ ERROR",
            "Invalid_Price": "READ ERROR",
            "Invalid_Sales": "READ ERROR",
            "Invalid_Dates": "READ ERROR",
            "Invalid_Timestamps": "READ ERROR",
            "Invalid_Store_ID": "READ ERROR",
            "Invalid_Store_Name": "READ ERROR",
            "Status": "FAIL"
        })

        continue


    # --------------------------------------------------------
    # Row count
    # --------------------------------------------------------

    row_count = len(df)

    total_rows += row_count

    print(f"Rows: {row_count:,}")


    # --------------------------------------------------------
    # Column check
    # --------------------------------------------------------

    actual_columns = list(df.columns)

    missing_columns = [
        column
        for column in EXPECTED_COLUMNS
        if column not in actual_columns
    ]

    extra_columns = [
        column
        for column in actual_columns
        if column not in EXPECTED_COLUMNS
    ]

    if missing_columns:
        print(f"Missing columns: {missing_columns}")

    if extra_columns:
        print(f"Extra columns: {extra_columns}")

    column_check = (
        "PASS"
        if not missing_columns
        else "FAIL"
    )


    # --------------------------------------------------------
    # Missing values
    # --------------------------------------------------------

    missing_values = int(
        df.isna().sum().sum()
    )

    total_missing_values += missing_values

    print(f"Missing values: {missing_values:,}")


    # --------------------------------------------------------
    # Duplicate Order_ID
    # --------------------------------------------------------

    if "Order_ID" in df.columns:

        duplicate_order_ids = int(
            df["Order_ID"].duplicated().sum()
        )

        total_duplicate_order_ids += duplicate_order_ids

        all_order_ids.extend(
            df["Order_ID"].dropna().astype(str).tolist()
        )

    else:

        duplicate_order_ids = -1

    print(
        f"Duplicate Order_IDs: "
        f"{duplicate_order_ids:,}"
    )


    # --------------------------------------------------------
    # Quantity validation
    # --------------------------------------------------------

    if "Quantity" in df.columns:

        quantity = pd.to_numeric(
            df["Quantity"],
            errors="coerce"
        )

        invalid_quantity = int(
            (
                quantity.isna()
                | (quantity <= 0)
                | (quantity % 1 != 0)
            ).sum()
        )

    else:

        invalid_quantity = -1

    total_invalid_quantities += max(
        invalid_quantity,
        0
    )

    print(
        f"Invalid quantities: "
        f"{invalid_quantity:,}"
    )


    # --------------------------------------------------------
    # Unit price validation
    # --------------------------------------------------------

    if "Unit_Price_USD" in df.columns:

        unit_price = pd.to_numeric(
            df["Unit_Price_USD"],
            errors="coerce"
        )

        invalid_price = int(
            (
                unit_price.isna()
                | (unit_price <= 0)
            ).sum()
        )

    else:

        invalid_price = -1

    total_invalid_prices += max(
        invalid_price,
        0
    )

    print(
        f"Invalid prices: "
        f"{invalid_price:,}"
    )


    # --------------------------------------------------------
    # Sales amount validation
    # --------------------------------------------------------

    sales_columns = [
        "Gross_Sales_USD",
        "Discount_USD",
        "Subtotal_USD",
        "NJ_Sales_Tax_USD",
        "Total_Sales_USD"
    ]

    invalid_sales = 0

    for column in sales_columns:

        if column in df.columns:

            values = pd.to_numeric(
                df[column],
                errors="coerce"
            )

            invalid_sales += int(
                (
                    values.isna()
                    | (values < 0)
                ).sum()
            )

    total_invalid_sales += invalid_sales

    print(
        f"Invalid sales amounts: "
        f"{invalid_sales:,}"
    )


    # --------------------------------------------------------
    # Date validation
    # --------------------------------------------------------

    invalid_dates = 0

    if "Order_Date" in df.columns:

        parsed_dates = pd.to_datetime(
            df["Order_Date"],
            errors="coerce"
        )

        invalid_dates = int(
            parsed_dates.isna().sum()
        )

    total_invalid_dates += invalid_dates

    print(
        f"Invalid dates: "
        f"{invalid_dates:,}"
    )


    # --------------------------------------------------------
    # Timestamp validation
    # --------------------------------------------------------

    invalid_timestamps = 0

    for column in [
        "Order_Timestamp",
        "Delivered_Timestamp"
    ]:

        if column in df.columns:

            parsed_timestamp = pd.to_datetime(
                df[column],
                errors="coerce"
            )

            invalid_timestamps += int(
                parsed_timestamp.isna().sum()
            )

    total_invalid_timestamps += invalid_timestamps

    print(
        f"Invalid timestamps: "
        f"{invalid_timestamps:,}"
    )


    # --------------------------------------------------------
    # Store ID validation
    # --------------------------------------------------------

    invalid_store_id = 0

    if "Store_ID" in df.columns:

        store_ids = (
            df["Store_ID"]
            .dropna()
            .astype(str)
        )

        all_store_ids.extend(
            store_ids.tolist()
        )

        invalid_store_id = int(
            (~store_ids.str.match(r"^Store \d{2}$"))
            .sum()
        )

    total_invalid_store_ids += invalid_store_id

    print(
        f"Invalid Store_ID: "
        f"{invalid_store_id:,}"
    )


    # --------------------------------------------------------
    # Store name consistency
    # --------------------------------------------------------

    invalid_store_name = 0

    if (
        "Store_ID" in df.columns
        and "Store_Name" in df.columns
    ):

        file_store_ids = (
            df["Store_ID"]
            .dropna()
            .astype(str)
            .unique()
        )

        file_store_names = (
            df["Store_Name"]
            .dropna()
            .astype(str)
            .unique()
        )

        # Each store file should contain one Store_ID
        # and one Store_Name.
        if len(file_store_ids) != 1:
            invalid_store_name += 1

        if len(file_store_names) != 1:
            invalid_store_name += 1

    total_invalid_store_names += invalid_store_name

    print(
        f"Store consistency issues: "
        f"{invalid_store_name:,}"
    )


    # --------------------------------------------------------
    # File status
    # --------------------------------------------------------

    file_status = "PASS"

    if missing_columns:
        file_status = "FAIL"

    if missing_values > 0:
        file_status = "FAIL"

    if duplicate_order_ids > 0:
        file_status = "FAIL"

    if invalid_quantity > 0:
        file_status = "FAIL"

    if invalid_price > 0:
        file_status = "FAIL"

    if invalid_sales > 0:
        file_status = "FAIL"

    if invalid_dates > 0:
        file_status = "FAIL"

    if invalid_timestamps > 0:
        file_status = "FAIL"

    if invalid_store_id > 0:
        file_status = "FAIL"

    if invalid_store_name > 0:
        file_status = "FAIL"


    # --------------------------------------------------------
    # Add result to report
    # --------------------------------------------------------

    report_results.append({

        "File": csv_file.name,

        "Rows": row_count,

        "Columns": len(actual_columns),

        "Missing_Columns": ", ".join(missing_columns),

        "Extra_Columns": ", ".join(extra_columns),

        "Missing_Values": missing_values,

        "Duplicate_Order_IDs": duplicate_order_ids,

        "Invalid_Quantity": invalid_quantity,

        "Invalid_Price": invalid_price,

        "Invalid_Sales": invalid_sales,

        "Invalid_Dates": invalid_dates,

        "Invalid_Timestamps": invalid_timestamps,

        "Invalid_Store_ID": invalid_store_id,

        "Store_Consistency_Issues":
            invalid_store_name,

        "Status": file_status
    })


# ============================================================
# 5. GLOBAL ORDER_ID DUPLICATE CHECK
# ============================================================

print("\n" + "=" * 70)
print("GLOBAL ORDER_ID VALIDATION")
print("=" * 70)

order_id_series = pd.Series(all_order_ids)

global_duplicate_order_ids = int(
    order_id_series.duplicated().sum()
)

print(
    f"Duplicate Order_IDs across all 24 stores: "
    f"{global_duplicate_order_ids:,}"
)


# ============================================================
# 6. STORE COVERAGE
# ============================================================

print("\n" + "=" * 70)
print("STORE COVERAGE")
print("=" * 70)

expected_store_ids = {
    f"Store {i:02d}"
    for i in range(1, 25)
}

actual_store_ids = set(all_store_ids)

missing_stores = sorted(
    expected_store_ids - actual_store_ids
)

unexpected_stores = sorted(
    actual_store_ids - expected_store_ids
)

print(
    f"Expected stores: "
    f"{len(expected_store_ids)}"
)

print(
    f"Stores found: "
    f"{len(actual_store_ids)}"
)

print(
    f"Missing stores: "
    f"{missing_stores if missing_stores else 'None'}"
)

print(
    f"Unexpected stores: "
    f"{unexpected_stores if unexpected_stores else 'None'}"
)


# ============================================================
# 7. OVERALL DATA QUALITY STATUS
# ============================================================

overall_status = "PASS"

if len(csv_files) != EXPECTED_STORES:
    overall_status = "FAIL"

if total_rows != EXPECTED_TRANSACTIONS:
    overall_status = "FAIL"

if total_missing_values > 0:
    overall_status = "FAIL"

if total_duplicate_order_ids > 0:
    overall_status = "FAIL"

if global_duplicate_order_ids > 0:
    overall_status = "FAIL"

if total_invalid_quantities > 0:
    overall_status = "FAIL"

if total_invalid_prices > 0:
    overall_status = "FAIL"

if total_invalid_sales > 0:
    overall_status = "FAIL"

if total_invalid_dates > 0:
    overall_status = "FAIL"

if total_invalid_timestamps > 0:
    overall_status = "FAIL"

if total_invalid_store_ids > 0:
    overall_status = "FAIL"

if total_invalid_store_names > 0:
    overall_status = "FAIL"

if missing_stores:
    overall_status = "FAIL"

if unexpected_stores:
    overall_status = "FAIL"


# ============================================================
# 8. SAVE DETAILED REPORT
# ============================================================

report_df = pd.DataFrame(
    report_results
)

detailed_report = (
    report_folder
    / "Dunkin_24_Store_Data_Quality_Report.csv"
)

report_df.to_csv(
    detailed_report,
    index=False
)


# ============================================================
# 9. CREATE SUMMARY REPORT
# ============================================================

summary_lines = [

    "DUNKIN 24-STORE DATA QUALITY REPORT",
    "=" * 60,

    "",
    f"CSV files found: {len(csv_files)}",
    f"Expected CSV files: {EXPECTED_STORES}",

    "",
    f"Total transactions: {total_rows:,}",
    f"Expected transactions: {EXPECTED_TRANSACTIONS:,}",

    "",
    f"Total missing values: {total_missing_values:,}",

    f"Duplicate Order_IDs within files: "
    f"{total_duplicate_order_ids:,}",

    f"Duplicate Order_IDs across all stores: "
    f"{global_duplicate_order_ids:,}",

    "",
    f"Invalid quantities: "
    f"{total_invalid_quantities:,}",

    f"Invalid prices: "
    f"{total_invalid_prices:,}",

    f"Invalid sales amounts: "
    f"{total_invalid_sales:,}",

    f"Invalid dates: "
    f"{total_invalid_dates:,}",

    f"Invalid timestamps: "
    f"{total_invalid_timestamps:,}",

    f"Invalid Store_ID values: "
    f"{total_invalid_store_ids:,}",

    f"Store consistency issues: "
    f"{total_invalid_store_names:,}",

    "",
    f"Expected stores: {EXPECTED_STORES}",
    f"Stores found: {len(actual_store_ids)}",

    f"Missing stores: "
    f"{missing_stores if missing_stores else 'None'}",

    f"Unexpected stores: "
    f"{unexpected_stores if unexpected_stores else 'None'}",

    "",
    "=" * 60,

    f"OVERALL DATA QUALITY STATUS: "
    f"{overall_status}",

    "=" * 60
]


summary_report = (
    report_folder
    / "Dunkin_Data_Quality_Summary.txt"
)

with open(
    summary_report,
    "w",
    encoding="utf-8"
) as file:

    file.write(
        "\n".join(summary_lines)
    )


# ============================================================
# 10. DISPLAY FINAL SUMMARY
# ============================================================

print("\n" + "\n".join(summary_lines))

print("\nReports created:")
print(detailed_report)
print(summary_report)

print("\nData quality validation completed.")
