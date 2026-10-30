# Customer Recommendation Engine

A small recommender for a retail shop. It looks at what each customer has bought, finds the customers whose baskets overlap most with theirs, and suggests products those similar customers bought that this customer hasn't tried yet.

It uses only the Python standard library, so there is nothing to install.

## Setup and run

You need Python 3.9 or newer.

```
python -m venv recommenderenv
recommenderenv\Scripts\activate
python recommender.py
```

On macOS or Linux, activate with `source recommenderenv/bin/activate` instead.

Put the purchase records in `data/purchases.csv`. Running the script writes `output/recommendations.csv` and prints a sample customer plus a run summary to the console.

## How it works

1. **Read the purchases.** Each row is cleaned and checked. Good rows are kept, bad rows go to a rejected pile.
2. **Build lookups once.** Each customer maps to the set of products they bought. Product names, categories and popularity are stored too. After this, nothing re-reads the raw rows.
3. **Compare customers.** Similarity between two customers is the Jaccard score of their product sets: shared products divided by all different products either of them bought. It runs from 0.0 (nothing in common) to 1.0 (identical baskets).
4. **Pick neighbours.** For a customer, take the 3 most similar other customers.
5. **Collect candidates.** Gather the products the neighbours bought that this customer hasn't, and remember which neighbours back each one.
6. **Rank and keep the top 3.**
7. **Export** everything to CSV.

## Data rules

Rows are cleaned first, then checked. Customer and product IDs are trimmed and upper-cased before anything else happens, so `c116` and ` C116 ` are treated as `C116`.

- **Repeated rows:** a row whose `purchase_id` has already appeared is rejected. I used `purchase_id` as the key because it identifies one purchase. If the same customer buys the same product on two different days, those are two real purchases with different IDs, so both are kept. They still count once in the customer's product set, because we only care whether they bought something, not how often.
- **Blank product:** rejected. There is nothing to recommend without a product ID. A blank `purchase_id`, `customer_id` or `product_name` is rejected too.
- **Zero or negative quantity:** rejected, since nothing was actually bought.
- **Quantity that isn't a number:** treated as 0, so it is rejected instead of crashing the program.

On the sample data this gives 63 rows read, 60 used and 3 rejected.

## Design choices

- **Popularity counts distinct customers, not rows.** If one customer buys the same product ten times it still counts as one. That way a single heavy buyer can't make a product look popular.
- **`min_similarity` defaults to 0.1.** A score of 0.0 means two customers share nothing, so they shouldn't count as neighbours. Without a cutoff, those customers would sit in the neighbour list and add noise. The value can be changed when the engine is created.
- **Ties are always broken the same way.** Neighbours with equal scores are ordered by customer ID, and products with equal scores by product ID. The output is identical on every run.
- **Fallback when there are no candidates.** If a customer has no neighbours above the cutoff, or their neighbours have nothing new to offer, they get the most popular products they haven't bought yet (ties by product ID). I chose this because it is a reasonable guess when we know nothing else, and it means everyone still gets recommendations. These rows have an empty `supporting_customers` column, which is how you can tell them apart.
- **Unknown customers raise an error.** Asking for a customer who isn't in the data raises `KeyError: 'Unknown customer ID: C999'`, instead of quietly returning an empty or made-up result.

## Scoring rule

```
score = (sum of the similarities of the neighbours who bought it)
        + 0.5 × (product popularity ÷ highest popularity in the shop)
```

The idea:

- Each neighbour who bought the product counts as a vote, and more similar neighbours count for more. Two close neighbours agreeing is stronger evidence than one.
- Popularity is a second signal. It separates products with equal neighbour support and ranks the fallback products, which have no neighbours at all.
- The popularity weight is `POPULARITY_WEIGHT = 0.5`, set at the top of `recommender.py`. Raising it makes everyone's lists look more alike, because popular products win for everybody.

### Worked example: customer C116 (Barasa)

C116 bought P03, P09 and P14. Their top neighbours are C108 and C120 (0.40 each) and C109 (0.25). The most popular product in the shop is P03 with 7 buyers.

| Product | Neighbours who bought it | Similarity sum | Popularity bonus | Score |
|---|---|---|---|---|
| P12 Omo 2kg | C108, C120 | 0.40 + 0.40 = 0.80 | 0.5 × 6/7 = 0.429 | **1.229** |
| P13 Jik Bleach 750ml | C108, C120 | 0.80 | 0.5 × 4/7 = 0.286 | **1.086** |
| P08 Ketepa Tea 250g | C109 | 0.25 | 0.5 × 3/7 = 0.214 | **0.464** |

P12 and P13 have exactly the same neighbour support, so popularity decides between them (6 buyers against 4). P08 ranks last because only one, less similar, neighbour bought it.

## Output

`output/recommendations.csv` has one row per customer and rank:

```
customer_id,customer_name,rank,product_id,product_name,category,score,supporting_customers
```

Scores are written to 3 decimal places and `supporting_customers` lists the neighbours behind each suggestion, separated by semicolons. A customer with no possible recommendation still appears once, with blank product columns, so nobody silently disappears from the file.

## Sample run

```
Customer C116 (Barasa) bought: {P03, P09, P14}
Most similar customers:
  C108  jaccard=0.40
  C120  jaccard=0.40
  C109  jaccard=0.25
Recommendations:
  1. Omo 2kg (Household)  score=1.229  because 2 similar customers bought it
  2. Jik Bleach 750ml (Household)  score=1.086  because 2 similar customers bought it
  3. Ketepa Tea 250g (Beverages)  score=0.464  because 1 similar customer bought it

Purchases read: 63 | used: 60 | rejected: 3
Customers: 20 | Products: 15 | Recommendations written: 52
```

Matching rows in the CSV:

```
C116,Barasa,1,P12,Omo 2kg,Household,1.229,C108;C120
C116,Barasa,2,P13,Jik Bleach 750ml,Household,1.086,C108;C120
C116,Barasa,3,P08,Ketepa Tea 250g,Beverages,0.464,C109
```

## Limitations

- The data set is small (20 customers, 15 products), so similarity scores are coarse and a few purchases can change who counts as a neighbour.
- Some customers get fewer than 3 recommendations when their neighbours have few products they haven't already bought.
- Quantity and purchase date are not used in scoring, only whether a customer bought a product.