from pathlib import Path
import logging, sqlite3
import pandas as pd

ROOT=Path(__file__).resolve().parent
DATA=ROOT/"data"; LOGS=ROOT/"logs"
DATA.mkdir(exist_ok=True); LOGS.mkdir(exist_ok=True)
logging.basicConfig(filename=LOGS/"ingestion.log",level=logging.INFO,
                    format="%(asctime)s | %(levelname)s | %(message)s")
COLS=["order_id","customer_name","email","amount","order_date","quantity","status","currency"]
CREATE="""
CREATE TABLE IF NOT EXISTS orders(
 order_id TEXT PRIMARY KEY, customer_name TEXT NOT NULL, email TEXT,
 amount REAL NOT NULL CHECK(amount>=0), order_date TEXT NOT NULL,
 quantity INTEGER NOT NULL CHECK(quantity>0), status TEXT NOT NULL,
 currency TEXT NOT NULL CHECK(currency IN ('INR','USD','EUR','GBP')),
 updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)
"""
UPSERT="""
INSERT INTO orders(order_id,customer_name,email,amount,order_date,quantity,status,currency)
VALUES(?,?,?,?,?,?,?,?)
ON CONFLICT(order_id) DO UPDATE SET
 customer_name=excluded.customer_name,email=excluded.email,amount=excluded.amount,
 order_date=excluded.order_date,quantity=excluded.quantity,status=excluded.status,
 currency=excluded.currency,updated_at=CURRENT_TIMESTAMP
"""

def main():
    source=DATA/"cleaned_orders.csv"
    if not source.exists():
        raise FileNotFoundError("Copy Task 2's cleaned_orders.csv into this task's data folder first.")
    df=pd.read_csv(source)
    if list(df.columns)!=COLS: raise ValueError(f"Schema mismatch. Expected: {COLS}")
    if df.order_id.isna().any() or df.order_id.duplicated().any():
        raise ValueError("order_id must be present and unique")
    db=DATA/"orders.db"
    with sqlite3.connect(db) as conn:
        conn.execute(CREATE)
        records=[(str(r.order_id),str(r.customer_name),None if pd.isna(r.email) else str(r.email),
                  float(r.amount),str(r.order_date),int(r.quantity),str(r.status),str(r.currency))
                 for r in df.itertuples(index=False)]
        conn.executemany(UPSERT,records)
        total=conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        distinct=conn.execute("SELECT COUNT(DISTINCT order_id) FROM orders").fetchone()[0]
        sample=conn.execute("SELECT order_id,customer_name,amount,currency FROM orders ORDER BY order_id LIMIT 5").fetchall()
        statuses=conn.execute("SELECT status,COUNT(*) FROM orders GROUP BY status ORDER BY status").fetchall()
        if total!=distinct: raise RuntimeError("Primary-key verification failed")
    report=["SQLITE INGESTION VERIFICATION REPORT","="*38,
            f"Rows submitted for upsert: {len(records)}",f"Rows in database: {total}",
            f"Distinct primary keys: {distinct}",f"Database: {db.name}","","Sample records:"]
    report += [str(x) for x in sample]
    report += ["","Counts by status:"]+[f"{s}: {n}" for s,n in statuses]
    report += ["","Idempotency: rerun this script; row count should remain unchanged."]
    (LOGS/"verification_report.txt").write_text("\n".join(report)+"\n",encoding="utf-8")
    logging.info("Upserted %s records; database now contains %s",len(records),total)
    print("\n".join(report))
    print("Saved data/orders.db and logs/verification_report.txt")

if __name__=="__main__": main()
