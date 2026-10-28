from pathlib import Path
import pandas as pd

csv_folder = Path(
    "/Users/home/Desktop/DunkinDonuts/Data_engineer_project/Dunkin_24_Store_CSV"
)

order_ids = [
    "ORD-2026-00017472",
    "ORD-2026-00014631",
    "ORD-2026-00002846",
    "ORD-2026-00016942"
]

print("=" * 70)
print("CHECKING TIMESTAMP RECORDS")
print("=" * 70)

for csv_file in sorted(csv_folder.glob("Store *_Sales_Data.csv")):

    df = pd.read_csv(csv_file)

    matching_rows = df[df["Order_ID"].isin(order_ids)]

    if not matching_rows.empty:

        print("\n" + "=" * 70)
        print(f"FILE: {csv_file.name}")
        print("=" * 70)

        columns_to_show = [
            "Order_ID",
            "Store_ID",
            "Order_Date",
            "Order_Timestamp",
            "Delivered_Timestamp",
            "Order_to_Delivery_Minutes"
        ]

        print(
            matching_rows[columns_to_show].to_string(index=False)
        )

print("\n" + "=" * 70)
print("CHECK COMPLETE")
print("=" * 70)