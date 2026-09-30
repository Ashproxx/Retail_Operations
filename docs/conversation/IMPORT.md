# Import actual observations without changing the original file

No real dataset was supplied during development. Validate your source-column meaning before creating a mapping; these example headings are illustrative.

Create `mapping.json` locally:

```json
{
  "date": "Business Date",
  "store_id": "Store Code",
  "store_location": "Store Name",
  "sku_id": "Product Code",
  "category": "Category",
  "style_name": "Product Name",
  "gender": "Gender",
  "color": "Color",
  "size": "Size",
  "unit_price_inr": "Observed Price INR",
  "units_sold": "Units Sold",
  "closing_stock": "Closing Stock",
  "reorder_point": "Reorder Point"
}
```

Map only headings actually present in your CSV/XLSX. Required canonical fields: date, store_id, store_location, sku_id, unit_price_inr, units_sold, closing_stock, reorder_point. Optional fields include category, style_code, style_name, gender, color, size, supplier, opening_stock, vendor_lead_time_days, stockout_risk_flag. Do not substitute zero for unavailable facts. This importer requires the required fields; collect them or build a separately reviewed source adapter if absent.

```powershell
.\.venv\Scripts\python.exe -m app.conversation.ingest --file "C:\data\apparel.xlsx" --mapping "C:\data\mapping.json"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
```

Do not use `--fixture` for real data. It is an explicit marker for synthetic validation files.

- One observation per store/product/date; duplicate batches and existing identities fail atomically. Existing source data is not overwritten.
- Raw original source columns are retained alongside validated canonical values and taxonomy fields.
- Up to 20 MB, 10,000 observations, 100 columns; active XLSX sheet only. Formulas, duplicate headers, missing mappings and malformed values are rejected.
- Unmapped apparel categories are reported and remain unknown. Extend `app/conversation/config/apparel_taxonomy.json` after reviewing the source vocabulary.
- Prices must be INR for the current implementation. Revenue is units × observed price, not audited net revenue. Currency conversion, taxes, discounts and refunds are not inferred.
- Store grants must include the actual source store IDs. End users select human names; the server resolves IDs internally and rechecks authorization.
- The canonical importer feeds `/assistant`. Existing operational agents still use their own validated records and policy documents. Import those with the original integration loader; canonical sales observations do not invent vendor costs, orders or return policies.

Keep original data and configuration outside git. After importing, compare row counts, sample products, source totals, prices, stock and missing-day coverage before relying on recommendations. Backtests in the demo establish implementation behavior on synthetic history, not accuracy on your business.
