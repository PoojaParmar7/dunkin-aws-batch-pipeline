from pathlib import Path
import pandas as pd

input_folder = Path(
    "/Users/home/Desktop/DunkinDonuts/Data_engineer_project/Dunkin_24_Store_CSV"
)

print("=" * 70)
print("TIMESTAMP ERROR INVESTIGATION")
print("=" * 70)

print(f"\nCSV folder:")
print(input_folder)

print(f"\nFolder exists: {input_folder.exists()}")

csv_files = sorted(
    input_folder.glob("Store *_Sales_Data.csv")
)

print(f"CSV files found: {len(csv_files)}")


total_errors = 0

for csv_file in csv_files:

    df = pd.read_csv(csv_file)

    for column in [
        "Order_Timestamp",
        "Delivered_Timestamp"
    ]:

        if column not in df.columns:
            continue

        parsed = pd.to_datetime(
            df[column],
            errors="coerce"
        )

        invalid_mask = parsed.isna()

        invalid_rows = df[invalid_mask]

        if len(invalid_rows) > 0:

            total_errors += len(invalid_rows)

            print("\n" + "=" * 70)
            print(f"FILE: {csv_file.name}")
            print(f"COLUMN: {column}")
            print(f"INVALID ROWS: {len(invalid_rows)}")
            print("=" * 70)

            print(
                invalid_rows[
                    [
                        "Order_ID",
                        "Store_ID",
                        "Order_Date",
                        "Order_Timestamp",
                        "Delivered_Timestamp"
                    ]
                ].to_string(index=False)
            )


print("\n" + "=" * 70)
print(f"TOTAL INVALID TIMESTAMP VALUES: {total_errors}")
print("=" * 70)