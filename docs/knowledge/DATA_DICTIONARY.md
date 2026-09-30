# Analytical data dictionary

Existing SQL: domain_records (validated JSON by agent/store), stores (ID/name), session_state (principal/session hash + TTL), request_receipts, signed_rag_manifest.

The analytical observation view will preserve raw imported values and expose date, store_id, store_location, sku_id, style_code, style_name, category, gender, color, size, unit_price_inr, opening_stock, units_sold, closing_stock, reorder_point, vendor_lead_time_days and stockout_risk_flag when provided.

Normalization adds department, apparel_family, normalized_category, normalized_location, date dimensions and calendar context. Unknown attributes remain null; no guessed suppliers, product names, prices, dates or external competitors. Human-friendly option labels may describe recorded attributes without claiming they are original product names.

Revenue = observed units * observed price; not inferred net revenue. Sell-through is a labelled proxy. Missing dates are not zero sales. Stockout-constrained sales are not unconstrained demand. Legacy observations remain read-only and compatible.

Derived import dimensions: `date_dimension` (ISO business date), weekday (Monday=0), month, quarter, year, configured `season_key`, and `price_band` (under INR 1,000; INR 1,000–1,999.99; INR 2,000+). These are descriptive bins, not economic market positioning. Unknown source attributes remain null. Product 360 includes scoped observed prices, daily units, inventory snapshots, performance and unit ranks; ranking scope and tie handling are exposed.
