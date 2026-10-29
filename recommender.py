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


class RecommendationEngine: 
    def __init__(self, purchases):
            self.history = {}
            self.product_name = {}
            self.product_category = {}
            self.popularity = {}
            customers ={}

            for row in purchases:
                    custid = row["customer_id"]
                    prodid = row["product_id"]
                    
                    if custid not in self.history:
                        self.history[custid] = set()
                    self.history[custid].add(prodid)

                    self.product_name[prodid] = row["product_name"]
                    self.product_category[prodid] = row["category"]

                    if prodid not in customers:
                        customers[prodid] = set()
                    
                    customers[prodid].add(custid)
                    self.popularity = {pid: len(who) for pid, who in customers.items()}

    def similarity(self, c1, c2):
        a = self.history[c1]
        b = self.history[c2]
        return jaccard(a, b)

   
def jaccard(a: set, b: set) -> float:
    """|A intersection B| / |A union B|. Returns 0.0 when both sets are empty."""
    union = a | b
    if not union:
        return 0
    return len(a & b) / len( a | b)

valid, rejected = read_purchases("data/purchases.csv")
engine = RecommendationEngine(valid)
first_five = list(engine.history)[:5]
print(first_five)
for c1 in first_five:
    row_values = []
    for c2 in first_five:
        row_values.append(round(engine.similarity(c1, c2), 2))
    print(c1, row_values)
print(engine.similarity("C116", "C120"))

