from sqlalchemy.orm import Session
import models
import schemas
from typing import List, Optional

def create_alarm(db: Session, alarm: schemas.AlarmCreate) -> models.Alarm:
    """Create a new alarm in the database."""
    db_alarm = models.Alarm(
        asset_class=alarm.asset_class,
        asset_symbol=alarm.asset_symbol,
        alarm_type=alarm.alarm_type,
        params=alarm.params,
        email=alarm.email,
        status="pending"
    )
    db.add(db_alarm)
    db.commit()
    db.refresh(db_alarm)
    return db_alarm

def get_alarm(db: Session, alarm_id: int) -> Optional[models.Alarm]:
    """Retrieve a specific alarm by ID."""
    return db.query(models.Alarm).filter(models.Alarm.id == alarm_id).first()

def get_pending_alarms(db: Session) -> List[models.Alarm]:
    """Get all pending alarms for processing."""
    return db.query(models.Alarm).filter(models.Alarm.status == "pending").all()

def update_alarm_status(db: Session, alarm_id: int, status: str) -> Optional[models.Alarm]:
    """Update the status of an alarm."""
    alarm = get_alarm(db, alarm_id)
    if alarm:
        alarm.status = status
        db.commit()
        db.refresh(alarm)
    return alarm

def delete_alarm(db: Session, alarm_id: int) -> bool:
    """Delete an alarm from the database."""
    alarm = get_alarm(db, alarm_id)
    if alarm:
        db.delete(alarm)
        db.commit()
        return True
    return False