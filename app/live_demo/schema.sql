CREATE TABLE IF NOT EXISTS demo_schema(version INTEGER PRIMARY KEY);
INSERT OR IGNORE INTO demo_schema VALUES(1);
CREATE TABLE IF NOT EXISTS demo_state(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS demo_runs(
 id TEXT PRIMARY KEY, source TEXT NOT NULL, checksum TEXT NOT NULL, started_at TEXT NOT NULL,
 ended_at TEXT, status TEXT NOT NULL, accepted INTEGER NOT NULL DEFAULT 0,
 skipped INTEGER NOT NULL DEFAULT 0, rejected INTEGER NOT NULL DEFAULT 0, error TEXT);
CREATE TABLE IF NOT EXISTS demo_events(
 id TEXT PRIMARY KEY, source TEXT NOT NULL, source_record_id TEXT NOT NULL, digest TEXT NOT NULL,
 run_id TEXT NOT NULL REFERENCES demo_runs(id), store_id TEXT NOT NULL REFERENCES stores(id),
 sku_id TEXT NOT NULL REFERENCES retail_products(sku_id), kind TEXT NOT NULL,
 order_id TEXT, quantity INTEGER NOT NULL, unit_paise INTEGER NOT NULL CHECK(unit_paise>=0),
 discount_bps INTEGER NOT NULL CHECK(discount_bps BETWEEN 0 AND 10000), net_paise INTEGER NOT NULL,
 stock_delta INTEGER, occurred_at TEXT NOT NULL, business_date TEXT NOT NULL, received_at TEXT NOT NULL,
 synthetic INTEGER CHECK(synthetic IN(0,1) OR synthetic IS NULL),
 original_id TEXT REFERENCES demo_events(id), reason TEXT, actor TEXT NOT NULL, factors TEXT NOT NULL,
 UNIQUE(source,source_record_id));
CREATE UNIQUE INDEX IF NOT EXISTS demo_once_reversal ON demo_events(original_id) WHERE kind='reversal';
CREATE INDEX IF NOT EXISTS demo_scope_date ON demo_events(store_id,business_date,id);
CREATE INDEX IF NOT EXISTS demo_stock_time ON demo_events(store_id,sku_id,occurred_at);
CREATE INDEX IF NOT EXISTS demo_arrival ON demo_events(received_at);
CREATE TRIGGER IF NOT EXISTS demo_no_update BEFORE UPDATE ON demo_events BEGIN SELECT RAISE(ABORT,'Append-only ledger'); END;
CREATE TRIGGER IF NOT EXISTS demo_no_delete BEFORE DELETE ON demo_events BEGIN SELECT RAISE(ABORT,'Append-only ledger'); END;
CREATE TABLE IF NOT EXISTS demo_checkpoints(slot TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES demo_runs(id), committed_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS demo_orders(
 id TEXT PRIMARY KEY, store_id TEXT NOT NULL REFERENCES stores(id),sku_id TEXT NOT NULL REFERENCES retail_products(sku_id),
 ordered_at TEXT NOT NULL, due_at TEXT NOT NULL, quantity INTEGER NOT NULL CHECK(quantity>0), delivered_at TEXT);
CREATE TABLE IF NOT EXISTS demo_shifts(
 id TEXT PRIMARY KEY, employee_id TEXT NOT NULL REFERENCES employees(employee_id),store_id TEXT NOT NULL REFERENCES stores(id),
 business_date TEXT NOT NULL, start_at TEXT NOT NULL,end_at TEXT NOT NULL,source TEXT NOT NULL DEFAULT 'simulated',
 CHECK(end_at>start_at), UNIQUE(employee_id,business_date));
CREATE TABLE IF NOT EXISTS demo_attendance(
 id TEXT PRIMARY KEY, shift_id TEXT NOT NULL REFERENCES demo_shifts(id), status TEXT NOT NULL,
 occurred_at TEXT NOT NULL, received_at TEXT NOT NULL, UNIQUE(shift_id,status));
