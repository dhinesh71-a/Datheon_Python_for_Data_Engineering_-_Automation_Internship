import os, smtplib
from email.message import EmailMessage
from pathlib import Path

def send_alert(result: dict, report_path: Path) -> bool:
    keys = ["SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD", "ALERT_FROM", "ALERT_TO"]
    config = {key: os.getenv(key) for key in keys}
    if not all(config.values()):
        return False  # Email is optional; reports/logs are still saved.
    msg = EmailMessage()
    msg["Subject"] = f"Datheon ETL Pipeline: {result['status']}"
    msg["From"], msg["To"] = config["ALERT_FROM"], config["ALERT_TO"]
    msg.set_content(
        f"Pipeline status: {result['status']}\\n"
        f"Duration: {result.get('duration_seconds')} seconds\\n"
        f"Database rows: {result.get('database_rows')}\\n"
        f"Error: {result.get('error', 'None')}\\n"
    )
    msg.add_attachment(report_path.read_bytes(), maintype="application",
                       subtype="json", filename=report_path.name)
    with smtplib.SMTP(config["SMTP_HOST"], int(os.getenv("SMTP_PORT", "587")), timeout=30) as server:
        server.starttls()
        server.login(config["SMTP_USERNAME"], config["SMTP_PASSWORD"])
        server.send_message(msg)
    return True
