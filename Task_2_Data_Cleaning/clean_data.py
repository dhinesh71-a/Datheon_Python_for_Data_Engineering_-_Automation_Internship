from pathlib import Path
import json, logging, re
import pandas as pd

ROOT=Path(__file__).resolve().parent
DATA=ROOT/"data"; LOGS=ROOT/"logs"
DATA.mkdir(exist_ok=True); LOGS.mkdir(exist_ok=True)
logging.basicConfig(filename=LOGS/"cleaning.log", level=logging.INFO,
                    format="%(asctime)s | %(levelname)s | %(message)s")
COLS=["order_id","customer_name","email","amount","order_date","quantity","status","currency"]
CURRENCIES={"INR","USD","EUR","GBP"}
STATUSES={"shipped","delivered","processing","pending","returned"}

def parse_amount(value):
    if pd.isna(value) or not str(value).strip(): return float("nan")
    s=str(value).strip().upper()
    s=re.sub(r"^(INR|USD|EUR|GBP)\s*","",s)
    for symbol in ["₹","$","€","£"]: s=s.replace(symbol,"")
    if re.fullmatch(r"\d+,\d{1,2}",s): s=s.replace(",",".")
    else: s=s.replace(",","")
    s=re.sub(r"[^\d.\-]","",s)
    try: return float(s)
    except ValueError: return float("nan")

def main():
    src=DATA/"raw_orders_dirty.csv"
    if not src.exists(): raise FileNotFoundError(src)
    df=pd.read_csv(src,dtype=str)
    missing=sorted(set(COLS)-set(df.columns))
    if missing: raise ValueError(f"Missing required columns: {missing}")
    input_rows=len(df)
    df=df[COLS].copy()
    for c in ["order_id","customer_name","email","status","currency"]:
        df[c]=df[c].fillna("").astype(str).str.strip()
    df["customer_name"]=df["customer_name"].str.title()
    df["email"]=df["email"].str.lower()
    df["status"]=df["status"].str.lower()
    df["currency"]=df["currency"].str.upper()
    df["amount"]=df["amount"].apply(parse_amount)
    df["order_date"] = pd.to_datetime(
    df["order_date"],
    format="mixed",
    errors="coerce",
    dayfirst=False
)
    df["quantity"]=pd.to_numeric(df["quantity"],errors="coerce")
    before=len(df); df=df.drop_duplicates(); duplicates=before-len(df)
    bad=(df.order_id.eq("") | df.customer_name.eq("") | df.amount.isna() |
         df.order_date.isna() | df.quantity.isna() | (df.quantity<=0) |
         ~df.currency.isin(CURRENCIES) | ~df.status.isin(STATUSES))
    invalid=int(bad.sum()); df=df.loc[~bad].copy()
    df["order_date"]=df["order_date"].dt.strftime("%Y-%m-%d")
    df["quantity"]=df["quantity"].astype("int64")
    df["amount"]=df["amount"].round(2)
    df=df.sort_values("order_id").reset_index(drop=True)
    checks={
      "required_columns_present":list(df.columns)==COLS,
      "order_id_not_null":bool(df.order_id.ne("").all()),
      "amount_numeric":bool(pd.api.types.is_numeric_dtype(df.amount)),
      "quantity_integer":bool(pd.api.types.is_integer_dtype(df.quantity)),
      "date_format_iso":bool(df.order_date.str.fullmatch(r"\d{4}-\d{2}-\d{2}").all()),
      "unique_order_ids":bool(df.order_id.is_unique),
      "allowed_currency_codes":bool(df.currency.isin(CURRENCIES).all())
    }
    if not all(checks.values()): raise ValueError(f"Schema validation failed: {checks}")
    df.to_csv(DATA/"cleaned_orders.csv",index=False)
    summary={"rows_received":input_rows,"exact_duplicates_removed":duplicates,
             "invalid_rows_removed":invalid,"rows_written":len(df),
             "schema_checks":checks,"column_types":{c:str(t) for c,t in df.dtypes.items()},
             "note":"Synthetic sample data; invalid or ambiguous values are rejected, not guessed."}
    (DATA/"cleaning_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    report=["AUTOMATED DATA QUALITY REPORT","="*34,f"Input rows: {input_rows}",
            f"Exact duplicates removed: {duplicates}",f"Invalid rows removed: {invalid}",
            f"Clean rows written: {len(df)}","","SCHEMA VALIDATION"]
    report += [f"{k}: {'PASS' if v else 'FAIL'}" for k,v in checks.items()]
    (LOGS/"quality_report.txt").write_text("\n".join(report)+"\n",encoding="utf-8")
    logging.info("Cleaning completed; %s rows written",len(df))
    print("\n".join(report))
    print("Saved data/cleaned_orders.csv and quality reports.")

if __name__=="__main__": main()
