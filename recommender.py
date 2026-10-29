import csv
from pathlib import Path

DATA_PATH = Path("data") / "purchases.csv"
OUTPUT_PATH = Path("output") / "recommendations.csv"

with open("data/purchases.csv", encoding="utf-8") as f:
    text = f.read()


def read_purchases(path):
    valid = []
    rejected = []
    seen = set()

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            row["customer_id"] = row["customer_id"].strip().upper()
            row["product_id"] = row["product_id"].strip().upper()
            try:
                qty = int(row["quantity"])
            except ValueError:
                qty = 0
            
            key = row["purchase_id"]

            if key in seen:
                rejected.append(row)
                continue

            seen.add(key)
            if row["product_id"].strip() == "" or row["purchase_id"].strip() == "" or row["customer_id"].strip() == "" or row["product_name"] == "" or qty <= 0 or row["customer_id"] == "":
                    rejected.append(row)
            else:
                    valid.append(row)


        return valid, rejected


valid, rejected = read_purchases("data/purchases.csv")
print("valid:", len(valid))
print("rejected:", len(rejected))
print(rejected)


