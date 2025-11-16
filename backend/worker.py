import logging
from time import sleep
import typer
import crud
import services
from database import SessionLocal

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s - %(message)s")
logger = logging.getLogger("alarm-worker")
app = typer.Typer(help="Local Alarm Worker (dev/test only)")

def process_alarm(alarm):
    db = SessionLocal()
    try:
        # mark processing
        crud.update_alarm_status(db, alarm.id, "processing")

        current_price = services.fetch_price(alarm.asset_class, alarm.asset_symbol)
        if current_price is None:
            logger.error("Failed to fetch price for alarm %s", alarm.id)
            crud.update_alarm_status(db, alarm.id, "failed")
            return

        if services.evaluate_condition(alarm, current_price):
            # local stub send
            sent = services.send_email_local_stub(alarm, current_price)
            if sent:
                logger.info("Alarm %s triggered and would be deleted (local mode)", alarm.id)
                crud.delete_alarm(db, alarm.id)
            else:
                logger.error("Email failed for alarm %s", alarm.id)
                crud.update_alarm_status(db, alarm.id, "failed")
        else:
            crud.update_alarm_status(db, alarm.id, "pending")
    except Exception as e:
        logger.exception("Error processing alarm %s: %s", getattr(alarm, "id", None), e)
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

@app.command()
def run(
    loop: bool = typer.Option(False, "--loop", help="Run continuously (dev only)"),
    delay: int = typer.Option(60, "--delay", help="Scan interval in seconds")
):
    logger.info("Local alarm worker started (loop=%s, delay=%s)", loop, delay)
    while True:
        try:
            process_all_alarms()
        except Exception:
            logger.exception("Unhandled error in process_all_alarms")
        if not loop:
            logger.info("Worker finished single run.")
            break
        sleep(delay)

if __name__ == "__main__":
    app()