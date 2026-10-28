from pathlib import Path
import pandas as pd

# ---------------------------------------------------------
# FOLDER
# ---------------------------------------------------------

csv_folder = Path(
    "/Users/home/Desktop/DunkinDonuts/Data_engineer_project/Dunkin_24_Store_CSV"
)

# ---------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------

print("=" * 70)
print("GLOBAL TRANSACTION_ID VALIDATION")
print("=" * 70)

all_transaction_ids = []
total_rows = 0
files_processed = 0

for csv_file in sorted(csv_folder.glob("Store *_Sales_Data.csv")):

    print(f"\nProcessing: {csv_file.name}")

    df = pd.read_csv(csv_file)

    files_processed += 1
    total_rows += len(df)

    # Check Transaction_ID column exists
    if "Transaction_ID" not in df.columns:
        print("ERROR: Transaction_ID column is missing!")
        continue

    # Collect IDs for global validation
    all_transaction_ids.extend(
        df["Transaction_ID"].astype(str).tolist()
    )

    # Check missing IDs
    missing_ids = df["Transaction_ID"].isna().sum()

    # Check duplicate IDs within file
    duplicate_ids = df["Transaction_ID"].duplicated().sum()

    print(f"Rows: {len(df):,}")
    print(f"Missing Transaction_IDs: {missing_ids}")
    print(f"Duplicate Transaction_IDs in file: {duplicate_ids}")

# ---------------------------------------------------------
# GLOBAL CHECK
# ---------------------------------------------------------

transaction_series = pd.Series(all_transaction_ids)

global_duplicate_count = transaction_series.duplicated().sum()

unique_transaction_ids = transaction_series.nunique()

# ---------------------------------------------------------
# FINAL REPORT
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("GLOBAL TRANSACTION_ID RESULTS")
print("=" * 70)

print(f"CSV files processed: {files_processed}")
print(f"Total transactions: {total_rows:,}")
print(f"Unique Transaction_IDs: {unique_transaction_ids:,}")
print(f"Global duplicate Transaction_IDs: {global_duplicate_count:,}")

print("\n" + "=" * 70)

if (
    total_rows == 400000
    and unique_transaction_ids == 400000
    and global_duplicate_count == 0
):
    print("STATUS: PASS")
    print("All 400,000 transactions have unique Transaction_IDs.")
else:
    print("STATUS: FAIL")
    print("Transaction_ID validation requires further investigation.")

print("=" * 70)