## Console (one customer)
Customer <customer_id> (<name>) bought: {<product_id>, ...}
Most similar customers:
  <customer_id>  jaccard=<0.00>
  <customer_id>  jaccard=<0.00>
  <customer_id>  jaccard=<0.00>
Recommendations:
  1. <product_name> (<category>)  score=<0.000>  because <n> similar customers bought it
  2. ...
  3. ...

## output/recommendations.csv
customer_id,customer_name,rank,product_id,product_name,category,score,supporting_customers
<C-id>,<text>,<1..n>,<P-id>,<text>,<text>,<float, 3 dp>,<C-id;C-id;...>
...
# One row per (customer, rank). Customers with no possible recommendation still appear
# once with blank product columns, so nobody silently disappears from the file.

## Run summary
Purchases read: <n> | used: <n> | rejected: <n>
Customers: <n> | Products: <n> | Recommendations written: <n>
