from __future__ import annotations
import csv, json, logging, sqlite3, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
TASK1 = REPO / "Task_1_Web_Scraper"
DATA, LOGS, REPORTS = ROOT / "data", ROOT / "logs", ROOT / "reports"
for folder in (DATA, LOGS, REPORTS):
    folder.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("datheon_etl")
logger.setLevel(logging.INFO)
if not logger.handlers:
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    for handler in (logging.FileHandler(LOGS / "pipeline.log", encoding="utf-8"),
                    logging.StreamHandler()):
        handler.setFormatter(fmt)
        logger.addHandler(handler)

def run_scraper():
    script = TASK1 / "scraper.py"
    if not script.exists():
        raise FileNotFoundError(f"Missing scraper: {script}")
    start = time.perf_counter()
    result = subprocess.run([sys.executable, str(script)], cwd=TASK1,
                            capture_output=True, text=True)
    if result.stdout.strip():
        logger.info("Scraper output:\\n%s", result.stdout.strip())
    if result.stderr.strip():
        (logger.error if result.returncode else logger.warning)(
            "Scraper messages:\\n%s", result.stderr.strip())
    if result.returncode:
        raise RuntimeError(f"Scraper failed with exit code {result.returncode}")
    return round(time.perf_counter() - start, 2)

def transform():
    source = TASK1 / "data" / "books.csv"
    target = DATA / "cleaned_books.csv"
    if not source.exists():
        raise FileNotFoundError(f"Scraper output not found: {source}")
    required = {"title", "price", "price_currency", "availability", "rating",
                "category", "product_url", "listing_page", "page_number"}
    seen, input_count, output_count = set(), 0, 0
    fields = ["title", "price", "currency", "availability", "rating",
              "category", "product_url", "listing_page", "page_number"]
    with source.open(newline="", encoding="utf-8-sig") as src:
        reader = csv.DictReader(src)
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Scraper CSV missing columns: {sorted(missing)}")
        with target.open("w", newline="", encoding="utf-8") as dst:
            writer = csv.DictWriter(dst, fieldnames=fields)
            writer.writeheader()
            for row in reader:
                input_count += 1
                title, url = (row.get("title") or "").strip(), (row.get("product_url") or "").strip()
                try:
                    price, page = float(row["price"]), int(row["page_number"])
                except (ValueError, TypeError, KeyError):
                    continue
                if not title or not url or price < 0 or url in seen:
                    continue
                seen.add(url)
                writer.writerow({
                    "title": title, "price": f"{price:.2f}",
                    "currency": (row.get("price_currency") or "GBP").strip().upper(),
                    "availability": " ".join((row.get("availability") or "").split()),
                    "rating": (row.get("rating") or "Unknown").strip(),
                    "category": (row.get("category") or "Books").strip(),
                    "product_url": url,
                    "listing_page": (row.get("listing_page") or "").strip(),
                    "page_number": page
                })
                output_count += 1
    if output_count == 0:
        raise ValueError("Transformation produced zero valid records")
    summary = {"input_rows": input_count, "clean_rows": output_count,
               "removed_rows": input_count-output_count,
               "output": "data/cleaned_books.csv"}
    (REPORTS / "transformation_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    logger.info("Transformation retained %s of %s rows", output_count, input_count)
    return summary

def load():
    source, db = DATA / "cleaned_books.csv", DATA / "books.db"
    create = """CREATE TABLE IF NOT EXISTS books(
      product_url TEXT PRIMARY KEY, title TEXT NOT NULL,
      price REAL NOT NULL CHECK(price >= 0), currency TEXT NOT NULL,
      availability TEXT, rating TEXT, category TEXT, listing_page TEXT,
      page_number INTEGER, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"""
    upsert = """INSERT INTO books(product_url,title,price,currency,availability,rating,category,listing_page,page_number)
      VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(product_url) DO UPDATE SET
      title=excluded.title,price=excluded.price,currency=excluded.currency,
      availability=excluded.availability,rating=excluded.rating,category=excluded.category,
      listing_page=excluded.listing_page,page_number=excluded.page_number,
      updated_at=CURRENT_TIMESTAMP"""
    with source.open(newline="", encoding="utf-8") as src:
        rows = [(r["product_url"], r["title"], float(r["price"]), r["currency"],
                 r["availability"], r["rating"], r["category"], r["listing_page"],
                 int(r["page_number"])) for r in csv.DictReader(src)]
    with sqlite3.connect(db) as conn:
        conn.execute(create)
        conn.executemany(upsert, rows)
        total = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
        distinct = conn.execute("SELECT COUNT(DISTINCT product_url) FROM books").fetchone()[0]
        if total != distinct:
            raise RuntimeError("Database primary-key verification failed")
    logger.info("Upserted %s books; database contains %s", len(rows), total)
    return total

def run_pipeline():
    started = datetime.now(timezone.utc).isoformat()
    clock = time.perf_counter()
    result = {"status": "SUCCESS", "started_at_utc": started}
    logger.info("========== PIPELINE START ==========")
    try:
        result["extraction_seconds"] = run_scraper()
        result["transformation"] = transform()
        result["database_rows"] = load()
    except Exception as exc:
        result["status"] = "FAILED"
        result["error"] = f"{type(exc).__name__}: {exc}"
        logger.exception("Pipeline failed")
    result["duration_seconds"] = round(time.perf_counter()-clock, 2)
    result["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    report = REPORTS / "latest_run_summary.json"
    report.write_text(json.dumps(result, indent=2), encoding="utf-8")
    try:
        from email_alert import send_alert
        sent = send_alert(result, report)
        logger.info("Email alert sent: %s", sent)
    except Exception:
        logger.exception("Email alert could not be sent")
    logger.info("Pipeline status: %s", result["status"])
    if result["status"] != "SUCCESS":
        raise RuntimeError(result.get("error", "Pipeline failed"))
    return result

if __name__ == "__main__":
    try:
        print(json.dumps(run_pipeline(), indent=2))
    except Exception as exc:
        print(f"PIPELINE FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
