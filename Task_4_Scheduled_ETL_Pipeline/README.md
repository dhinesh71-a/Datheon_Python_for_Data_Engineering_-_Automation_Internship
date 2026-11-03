# Task 4: Scheduled End-to-End ETL Pipeline with Alerting

## Workflow
1. **Extract:** run the existing Task 1 scraper to create `books.csv` and `books.json`.
2. **Transform:** validate the scraped CSV, normalize fields, remove duplicate product URLs, and write `data/cleaned_books.csv`.
3. **Load:** upsert transformed books into SQLite (`data/books.db`) using `product_url` as the primary key.
4. **Report and alert:** save a JSON run summary and logs; optionally email the summary report.
5. **Schedule:** run daily using the Python `schedule` package.

## Important schema note
Task 2 and Task 3 currently process synthetic retail orders (`order_id`, `customer_name`, etc.), while Task 1 extracts books (`title`, `price`, `product_url`, etc.). These schemas are incompatible. To create a genuine end-to-end ETL pipeline without corrupting or misusing the existing projects, Task 4 transforms and loads the Task 1 book data using its own compatible steps. Tasks 2 and 3 remain independently runnable projects.

## Install (PowerShell)
From the repository root:
```powershell
cd Task_4_Scheduled_ETL_Pipeline
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Run once
```powershell
python pipeline.py
```
The scraper visits all available pages. On success, check `data/cleaned_books.csv`, `data/books.db`, `reports/latest_run_summary.json`, and `logs/pipeline.log`.

## Run on a daily schedule
```powershell
$env:PIPELINE_RUN_TIME = "09:00"
python scheduler.py
```
Keep the terminal and computer running. Press Ctrl+C to stop. For automatic execution after reboot/sign-in, configure Windows Task Scheduler to start the scheduler or trigger `pipeline.py` at the desired time.

## Optional email alert
Configure these environment variables in the same PowerShell session before running:
```powershell
$env:SMTP_HOST = "smtp.gmail.com"
$env:SMTP_PORT = "587"
$env:SMTP_USERNAME = "your_email@gmail.com"
$env:SMTP_PASSWORD = "your_app_password"
$env:ALERT_FROM = "your_email@gmail.com"
$env:ALERT_TO = "recipient@example.com"
python pipeline.py
```
For Gmail, use an App Password, not your normal password. Never commit real credentials. `.env.example` contains placeholders only. If SMTP is not configured, the pipeline still saves reports and logs; the email is simply skipped.

## Idempotency
SQLite uses `product_url` as a primary key with `ON CONFLICT DO UPDATE`, so repeated runs update existing records instead of creating duplicates.
