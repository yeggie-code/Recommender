import csv
from pathlib import Path

DATA_PATH = Path("data") / "purchases.csv"
OUTPUT_PATH = Path("output") / "recommendations.csv"
POPULARITY_WEIGHT = 0.5


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

def jaccard(a: set, b: set) -> float:
    """|A intersection B| / |A union B|. Returns 0.0 when both sets are empty."""
    union = a | b
    if not union:
        return 0
    return len(a & b) / len( a | b)

class RecommendationEngine: 
    def __init__(self, purchases: list[dict], min_similarity: float = 0.1) -> None:
            self.min_similarity = min_similarity
            self._history = {}
            self.product_name = {}
            self.product_category = {}
            self.popularity = {}
            customers ={}

            for row in purchases:
                    custid = row["customer_id"]
                    prodid = row["product_id"]
                    
                    if custid not in self._history:
                        self._history[custid] = set()
                    self._history[custid].add(prodid)

                    self.product_name[prodid] = row["product_name"]
                    self.product_category[prodid] = row["category"]

                    if prodid not in customers:
                        customers[prodid] = set()
                    
                    customers[prodid].add(custid)
                    self.popularity = {pid: len(who) for pid, who in customers.items()}


    def history(self, customer_id):
        return self._history[customer_id]


    def similarity(self, c1, c2):
        a = self._history[c1]
        b = self._history[c2]
        return jaccard(a, b)

    
    def similar_customers(self, customer_id: str, k: int = 3) -> list[tuple[str, float]]:
        scored = []
        for other in self._history:
            if other == customer_id:
                continue
            score = self.similarity(customer_id, other)
            if score < self.min_similarity:
                 continue
            scored.append((other, score))
            scored.sort(key=lambda pair: (-pair[1], pair[0]))
        return scored[:k]

    def candidate_products(self, customer_id: str, k: int = 3) -> dict[str, dict]:
        own = self._history[customer_id]
        candidates = {}

        for neighbour, similar in self.similar_customers(customer_id, k):
            new_products = self._history[neighbour] - own

            for pid in new_products:
                if pid not in candidates:
                    candidates[pid] = {"supporters": []}
                candidates[pid]["supporters"].append((neighbour, similar))

        if candidates:
            return candidates

        own = self._history[customer_id]
        ranked = sorted(self.popularity.items(), key=lambda item: (-item[1], item[0]))

        for pid, count in ranked:
            if pid not in own:
                candidates[pid] = {"supporters": [], "fallback": True}
        return candidates

    
    def score(self, evidence: dict) -> float:
        sim_total = sum(sim for _, sim in evidence["supporters"])
        top = max(self.popularity.values())
        return sim_total + POPULARITY_WEIGHT * evidence["popularity"] / top


    def recommend(self, customer_id: str, n: int = 3) -> list[dict]:
        candidates = self.candidate_products(customer_id)
        results = []

        for pid, evidence in candidates.items():
            evidence["popularity"] = self.popularity[pid]
            results.append({
                "product_id": pid,
                "product_name": self.product_name[pid],
                "category": self.product_category[pid],
                "score": round(self.score(evidence), 4),
            })

        results.sort(key=lambda r: (-r["score"], r["product_id"]))
        return results[:n]

    
valid, rejected = read_purchases("data/purchases.csv")
engine = RecommendationEngine(valid)
first_five = list(engine._history)[:5]
print(first_five)
for c1 in first_five:
    row_values = []
    for c2 in first_five:
        row_values.append(round(engine.similarity(c1, c2), 2))
    print(c1, row_values)
print(engine.similarity("C116", "C120"))
print(engine.similar_customers("C116", 3))
print(engine.candidate_products("C116", 3))


strict = RecommendationEngine(valid, min_similarity=0.9)
print(engine.score({"supporters": [("C108", 0.4), ("C120", 0.4)], "popularity": 6}))
for rec in engine.recommend("C116", 3):
    print(rec)
    
