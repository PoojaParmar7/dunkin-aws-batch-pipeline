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
    "/Users/home/Desktop/DunkinDonuts/Data_engineer_project/Dunkin_24_Store_CSV_Backup_Before_Timestamp_Fix"
)

backup_folder.mkdir(exist_ok=True)

# ---------------------------------------------------------
# RECORDS THAT NEED CORRECTION
# ---------------------------------------------------------

corrections = {
    ("Store 01", "ORD-2026-00017472"): {
        "Delivered_Timestamp": "2026-04-24 00:00:00"
    },

    ("Store 05", "ORD-2026-00014631"): {
        "Delivered_Timestamp": "2026-11-17 00:00:00"
    },

    ("Store 06", "ORD-2026-00002846"): {
        "Order_Timestamp": "2026-02-03 00:00:00"
    },

    ("Store 06", "ORD-2026-00016942"): {
        "Delivered_Timestamp": "2026-12-25 00:00:00"
    }
}

# ---------------------------------------------------------
# PROCESS FILES
# ---------------------------------------------------------

print("=" * 70)
print("TIMESTAMP CORRECTION")
print("=" * 70)

total_changes = 0

for csv_file in sorted(csv_folder.glob("Store *_Sales_Data.csv")):

    df = pd.read_csv(csv_file)

    store_id = csv_file.stem.replace("_Sales_Data", "")

    # Create backup
    backup_file = backup_folder / csv_file.name
    shutil.copy2(csv_file, backup_file)

    file_changes = 0

    for (store, order_id), changes in corrections.items():

        if store != store_id:
            continue

        mask = df["Order_ID"] == order_id

        if mask.any():

            for column, new_value in changes.items():

                old_value = df.loc[mask, column].iloc[0]

                df.loc[mask, column] = new_value

                print(f"\nFILE: {csv_file.name}")
                print(f"ORDER ID: {order_id}")
                print(f"COLUMN: {column}")
                print(f"OLD VALUE: {old_value}")
                print(f"NEW VALUE: {new_value}")

                file_changes += 1
                total_changes += 1

    if file_changes > 0:

        df.to_csv(
            csv_file,
            index=False,
            date_format="%Y-%m-%d %H:%M:%S"
        )

        print(f"Changes saved: {file_changes}")

print("\n" + "=" * 70)
print(f"TOTAL TIMESTAMP VALUES CORRECTED: {total_changes}")
print("=" * 70)

print("\nBackup created at:")
print(backup_folder)

print("\nTimestamp correction completed.")