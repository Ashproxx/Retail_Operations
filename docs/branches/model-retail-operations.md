# Retail Operations transaction workspace

Owns app/enterprise/retail.py and shared turn contract. Uses SQL aggregates over imported transactions, dynamically scoped store/category/style/variant/channel/payment/customer/fulfillment options, source net revenue, distinct orders, no-data/latest-date clarification and separate retail memory. Delivery excludes pickups and counts orders once. Competitor weekly estimates disclose their grain and deduplicate our own metrics across competitor rows. Forecast reuses chronological candidate evaluation, never fills absent days as zero. Current inventory explicitly unavailable.

Charts return compatible structured specifications with interpretations. Legacy retail workspace remains intact. API mounting and new UI belong to integration/UI branches. Small regression covers query, date fallback, chart equality, competition and no-stock boundary; actual database smoke queries completed. Raw workbooks remain local.
