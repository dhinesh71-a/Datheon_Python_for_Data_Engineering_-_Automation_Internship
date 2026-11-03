import logging, os, time
from pathlib import Path
import schedule
from pipeline import run_pipeline

ROOT = Path(__file__).resolve().parent
(ROOT / "logs").mkdir(exist_ok=True)
logging.basicConfig(filename=ROOT/"logs"/"scheduler.log", level=logging.INFO,
                    format="%(asctime)s | %(levelname)s | %(message)s")

def job():
    try:
        run_pipeline()
    except Exception:
        logging.exception("Scheduled ETL run failed")

def main():
    run_time = os.getenv("PIPELINE_RUN_TIME", "09:00")
    schedule.every().day.at(run_time).do(job)
    logging.info("Scheduler started; daily run at %s", run_time)
    print(f"Daily ETL scheduled for {run_time}. Keep this terminal/computer running; Ctrl+C stops.")
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Scheduler stopped")
        print("Scheduler stopped.")

if __name__ == "__main__":
    main()
