import csv
from pathlib import Path

DATA_PATH = Path("data") / "purchases.csv"
OUTPUT_PATH = Path("output") / "recommendations.csv"
POPULARITY_WEIGHT = 0.5

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
            self.customer_name = {}
            customers ={}

            for row in purchases:
                    custid = row["customer_id"]
                    prodid = row["product_id"]
                    self.customer_name[custid] = row["customer_name"]
                    
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
        if customer_id not in self._history:
            raise KeyError(f"Unknown customer ID: {customer_id}")
        return self._history[customer_id]


    def similarity(self, c1, c2):
        a = self.history(c1)
        b = self.history(c2)
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
        own = self.history(customer_id)
        candidates = {}

        for neighbour, similar in self.similar_customers(customer_id, k):
            new_products = self._history[neighbour] - own

            for pid in new_products:
                if pid not in candidates:
                    candidates[pid] = {"supporters": []}
                candidates[pid]["supporters"].append((neighbour, similar))

        if candidates:
            return candidates

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
                "supporting_customers": ";".join(c for c, _ in evidence["supporters"]),
                "score": round(self.score(evidence), 4),

            })

        results.sort(key=lambda r: (-r["score"], r["product_id"]))
        return results[:n]


    def recommend_all(self, n: int = 3) -> list[dict]:
        rows = []
        for customer_id in sorted(self._history):
            name = self.customer_name[customer_id]
            recs = self.recommend(customer_id, n)

            if not recs:
                rows.append({"customer_id": customer_id, "customer_name": name,
                             "rank": "", "product_id": "", "product_name": "",
                             "category": "", "score": "", "supporting_customers": ""})
                continue

            for rank, rec in enumerate(recs, start=1):
                rows.append({"customer_id": customer_id, "customer_name": name,
                             "rank": rank, **rec})
        return rows


    def export_csv(self, rows: list[dict], path: Path = OUTPUT_PATH) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = ["customer_id", "customer_name", "rank", "product_id",
                      "product_name", "category", "score", "supporting_customers"]

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in rows:
                out = dict(r)
                if out["score"] != "":
                    out["score"] = f"{out['score']:.3f}"
                writer.writerow(out)


def show_customer(engine, customer_id, n=3):
    name = engine.customer_name[customer_id]
    bought = sorted(engine.history(customer_id))

    print(f"Customer {customer_id} ({name}) bought: " + "{" + ", ".join(bought) + "}")

    print("Most similar customers:")
    for other, sim in engine.similar_customers(customer_id, 3):
        print(f"  {other}  jaccard={sim:.2f}")

    print("Recommendations:")
    for i, rec in enumerate(engine.recommend(customer_id, n), start=1):
        supporters = rec["supporting_customers"]
        count = len(supporters.split(";")) if supporters else 0
        if count:
            reason = f"{count} similar customers bought it"
        else:
            reason = "it is popular with all customers"
        print(f"  {i}. {rec['product_name']} ({rec['category']})  score={rec['score']:.3f}  because {reason}")

def main():
    valid, rejected = read_purchases(DATA_PATH)
    engine = RecommendationEngine(valid)
    rows = engine.recommend_all(3)
    engine.export_csv(rows)

    written = sum(1 for r in rows if r["product_id"] != "")

    print(f"Purchases read: {len(valid) + len(rejected)} | used: {len(valid)} | rejected: {len(rejected)}")
    print(f"Customers: {len(engine._history)} | Products: {len(engine.product_name)} | Recommendations written: {written}")
    show_customer(engine, "C116")
    print()

if __name__ == "__main__":
    main()       