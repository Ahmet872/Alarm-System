from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from models import Alarm, AlarmStatus
from schemas import AlarmCreate

logger = logging.getLogger(__name__)

def create_alarm(db: Session, alarm: AlarmCreate) -> Alarm:
    """Persist a new alarm to the database"""
    db_alarm = Alarm(**alarm.model_dump())
    try:
        db.add(db_alarm)
        db.commit()
        db.refresh(db_alarm)
        logger.info(f"Created alarm id={db_alarm.id} type={alarm.alarm_type}")
        return db_alarm
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating alarm: {str(e)}")
        raise

def get_alarm(db: Session, alarm_id: int) -> Optional[Alarm]:
    """Retrieve a single alarm by ID"""
    return db.query(Alarm).filter(Alarm.id == alarm_id).first()

def get_pending_alarms(db: Session) -> List[Alarm]:
    """Retrieve all alarms with pending status in chronological order"""
    return (
        db.query(Alarm)
        .filter(Alarm.status == AlarmStatus.PENDING)
        .order_by(Alarm.created_at)
        .all()
    )

def get_alarms_by_email(db: Session, email: str) -> List[Alarm]:
    """Retrieve all alarms associated with a specific email address"""
    return (
        db.query(Alarm)
        .filter(Alarm.email == email)
        .order_by(Alarm.created_at.desc())
        .all()
    )

def update_alarm_status(
    db: Session, 
    alarm_id: int, 
    status: AlarmStatus,
    error_message: Optional[str] = None
) -> Optional[Alarm]:
    """Update alarm status with optional error message and last check timestamp"""
    alarm = get_alarm(db, alarm_id)
    if not alarm:
        return None
    
    alarm.status = status
    alarm.last_check_at = func.now()
    if error_message:
        alarm.last_error = error_message
    
    try:
        db.commit()
        db.refresh(alarm)
        logger.info(f"Updated alarm id={alarm_id} status={status}")
        return alarm
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating alarm {alarm_id}: {str(e)}")
        raise

def delete_alarm(db: Session, alarm_id: int) -> bool:
    """Remove an alarm from the database"""
    try:
        result = db.query(Alarm).filter(Alarm.id == alarm_id).delete()
        db.commit()
        logger.info(f"Deleted alarm id={alarm_id}")
        return result > 0
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting alarm {alarm_id}: {str(e)}")
        raise

def cleanup_old_alarms(db: Session, days: int = 30) -> int:
    """Remove triggered and failed alarms older than specified days"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    try:
        result = (
            db.query(Alarm)
            .filter(
                Alarm.created_at < cutoff_date,
                Alarm.status.in_([AlarmStatus.TRIGGERED, AlarmStatus.FAILED])
            )
            .delete(synchronize_session=False)
        )
        db.commit()
        logger.info(f"Cleaned up {result} old alarms")
        return result
    except Exception as e:
        db.rollback()
        logger.error(f"Error cleaning up old alarms: {str(e)}")
        raise