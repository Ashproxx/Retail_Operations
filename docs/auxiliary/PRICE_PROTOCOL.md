# Descriptive price association protocol

This supplement is fixed before its first measurement. It reads only imported synthetic sales through March 31, 2026. It never reads the opened final-test period, tunes existing models, changes prices or exports transactions.

Aggregate observed units and net INR revenue by SKU/day across stores. Keep products with at least 28 observed dates. Reject invalid/nonpositive aggregates and duplicate keys. Missing dates stay absent: zero sales and stock availability cannot be inferred. Fit one OLS specification: log observed units on log realized unit price, SKU and weekday fixed effects, and a linear day trend. Each observed product/day has equal weight. Fail closed for a rank-deficient design or fewer than twelve observed week clusters.

Report the price coefficient and 95% t interval using week-cluster robust covariance with the statsmodels small-sample correction and cluster-count-minus-one degrees of freedom. Week groups are Monday-Sunday calendar blocks. This interval is conditional on the specification, not guaranteed coverage: dependence between weeks, limited clusters, endogeneity and selection remain. No p-value-based model selection or recommendation is permitted.

Realized unit price divides revenue by units, so mathematical coupling and quantity weighting can distort the result. Promotions, stock, changing store coverage and customer mix are not controlled. The coefficient is a descriptive correlation, **not causal elasticity**. There is no train/test accuracy claim. A controlled experiment or defensible external identification strategy and independent operational evidence would be needed before causal advice.

Run `python -m scripts.evaluate_price_association` after committing the implementation. The result records the exact code commit, versions and an aggregate-source digest and refuses overwrite. Existing M17/M18 final-test results remain unchanged.
