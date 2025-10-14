import logging
from time import sleep
from datetime import datetime
import typer

import crud
import services
from database import SessionLocal

# Logging
logging.basicConfig(
    level=logging.DEBUG, 
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("alarm-worker")
app = typer.Typer(help="Financial One-shot Alarm Worker (sync)")

def process_alarm(alarm):
    db = SessionLocal()
    try:
        # Update status to processing
        crud.update_alarm_status(db, alarm.id, "processing")

        # Fetch price (sync)
        current_price = services.fetch_price(alarm.asset_class, alarm.asset_symbol)
        if current_price is None:
            logger.error(f"Failed to fetch price for alarm {alarm.id}")
            crud.update_alarm_status(db, alarm.id, "failed")
            return

        # Evaluate condition
        if services.evaluate_condition(alarm, current_price):
            sent = services.send_email(alarm, current_price)
            if sent:
                logger.info(f"Alarm {alarm.id} triggered and email sent")
                crud.delete_alarm(db, alarm.id)
            else:
                logger.error(f"Email failed for alarm {alarm.id}")
                crud.update_alarm_status(db, alarm.id, "failed")
        else:
            crud.update_alarm_status(db, alarm.id, "pending")

    except Exception as e:
        logger.exception(f"Error processing alarm {alarm.id}: {e}")
        try:
            crud.update_alarm_status(db, alarm.id, "failed")
        except Exception:
            pass
    finally:
        db.close()

def process_all_alarms():
    db = SessionLocal()
    try:
        alarms = crud.get_pending_alarms(db)
        if not alarms:
            logger.debug("No pending alarms found.")
            return

        for alarm in alarms:
            process_alarm(alarm)
    finally:
        db.close()

# Main loop
@app.command()
def run(
    once: bool = typer.Option(False, "--once", help="Run once and exit"),
    delay: int = typer.Option(60, "--delay", help="Scan interval in seconds")
):
    logger.info("🚀 Alarm worker started (once=%s, delay=%ds)", once, delay)
    while True:
        try:
            process_all_alarms()
        except Exception:
            logger.exception("Unhandled error in process_all_alarms")
        if once:
            logger.info("Worker finished single run.")
            break
        sleep(delay)

if __name__ == "__main__":
    app()
