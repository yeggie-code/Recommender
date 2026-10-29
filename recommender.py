import csv
from pathlib import Path

DATA_PATH = Path("data") / "purchases.csv"
OUTPUT_PATH = Path("output") / "recommendations.csv"

with open("data/purchases.csv", encoding="utf-8") as f:
    text = f.read()


def read_purchases(path):
    valid = []
    rejected = []

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["product_id"].strip() == "" or row["purchase_id"].strip() == "" or row["customer_id"].strip() == "" or row["product_name"] == "":
                rejected.append(row)
            else:
                valid.append(row)
        

    return valid, rejected

valid, rejected = read_purchases("data/purchases.csv")
print("valid:", len(valid))
print("rejected:", len(rejected))