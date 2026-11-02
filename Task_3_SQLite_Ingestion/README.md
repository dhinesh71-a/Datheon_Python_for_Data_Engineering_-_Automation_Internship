# Task 3 – Relational Database Auto-Ingestion & Upsert Engine

Loads Task 2's cleaned CSV into SQLite with an `orders` table, `order_id` primary key, parameterized batch upserts, transaction safety and verification queries.

## Run
1. Copy Task 2's `data/cleaned_orders.csv` into this folder's `data/` directory.
2. Install: `python -m pip install -r requirements.txt`
3. Run: `python load_database.py`

## Outputs
- `data/orders.db`: populated SQLite database.
- `logs/verification_report.txt`: counts, sample records and status totals.
- `logs/ingestion.log`: execution log.

The `ON CONFLICT(order_id) DO UPDATE` upsert makes repeated runs idempotent: existing rows are updated rather than duplicated.
