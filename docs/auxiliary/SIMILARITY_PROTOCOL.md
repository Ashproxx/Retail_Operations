# Product ranking agreement protocol

Freeze this comparison before measuring. Use only transactions through March 31, 2026, aggregated by SKU, with at least fourteen observed dates. Use the same four descriptive feature definitions as the existing clustering experiment: log1p observed units, log1p realized unit price, observed dates and observed stores. Standardize on these training products. Compare Euclidean distance against cosine distance on the same standardized vectors; neither method is a relevance oracle. Exclude a product with a zero centered vector from both candidate pools because cosine direction is undefined.

For each query product, exclude itself, rank every other eligible product, break distance ties by SKU, and report full-ranking Spearman and top-five intersection divided by five, averaged across queries. These are **method agreement**, not human agreement or accuracy. No hyperparameter tuning, primary-test read or production similarity replacement is performed.

Emit the union of both top-five lists as a review queue with empty reviewer/relevance fields. The agent must not fill these as human-reviewed. The pool is biased by both methods and cannot estimate recall against all relevant products. An independent judged query/candidate set and business criteria are still needed for ranking acceptance. Stock availability and customer substitution cannot be inferred from observed sales.

Run `python -m scripts.evaluate_similarity` after committing. The local read-only evaluator records its exact commit and aggregate-source digest and refuses to overwrite evidence. Only SKU identifiers, ranks and aggregate statistics are saved; no customer or employee data enters this experiment.
