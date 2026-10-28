from pathlib import Path
import pandas as pd
import shutil

# ---------------------------------------------------------
# FOLDERS
# ---------------------------------------------------------

csv_folder = Path(
    "/Users/home/Desktop/DunkinDonuts/Data_engineer_project/Dunkin_24_Store_CSV"
)

backup_folder = Path(
    "/Users/home/Desktop/DunkinDonuts/Data_engineer_project/Dunkin_24_Store_CSV_Backup_Before_Transaction_ID"
)

backup_folder.mkdir(exist_ok=True)

# ---------------------------------------------------------
# PROCESS ALL 24 STORE FILES
# ---------------------------------------------------------

print("=" * 70)
print("CREATING GLOBAL TRANSACTION_ID")
print("=" * 70)

total_rows = 0
total_duplicates = 0

for csv_file in sorted(csv_folder.glob("Store *_Sales_Data.csv")):

    print(f"\nProcessing: {csv_file.name}")

    # Read CSV
    df = pd.read_csv(csv_file)

    # Backup original file
    backup_file = backup_folder / csv_file.name
    shutil.copy2(csv_file, backup_file)

    # Create globally unique Transaction_ID
    df.insert(
        0,
        "Transaction_ID",
        df["Store_ID"].astype(str)
        + "-"
        + df["Order_ID"].astype(str)
    )

    # Check uniqueness within this file
    duplicate_count = df["Transaction_ID"].duplicated().sum()

    # Save
    df.to_csv(
        csv_file,
        index=False
    )

    rows = len(df)

    total_rows += rows
    total_duplicates += duplicate_count

    print(f"Rows: {rows:,}")
    print(f"Duplicate Transaction_IDs: {duplicate_count}")

# ---------------------------------------------------------
# FINAL SUMMARY
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("TRANSACTION_ID CREATION COMPLETE")
print("=" * 70)

print(f"Total transactions processed: {total_rows:,}")
print(f"Duplicate Transaction_IDs within files: {total_duplicates:,}")

print("\nBackup created at:")
print(backup_folder)

print("\nAll 24 CSV files have been updated.")