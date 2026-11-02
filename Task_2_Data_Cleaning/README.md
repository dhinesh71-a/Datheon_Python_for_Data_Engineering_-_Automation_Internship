# Task 2 – Automated Data Cleaning & Schema Transformation

Cleans a deliberately messy synthetic retail-orders CSV using Pandas.

## Run
```powershell
python -m pip install -r requirements.txt
python clean_data.py
```

## Files
- `data/raw_orders_dirty.csv`: sample source with nulls, inconsistent casing, mixed currency/date formats, invalid values and a duplicate.
- `data/cleaned_orders.csv`: normalized, validated output.
- `data/cleaning_summary.json`: row counts, schema checks and column types.
- `logs/quality_report.txt`: readable quality report.
- `logs/cleaning.log`: execution log.

Invalid or ambiguous records are rejected rather than silently guessed. Sample input is synthetic.
