from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
import os
from datetime import datetime
from typing import List, Optional

from database import get_db, Base, engine
import crud
import models
import schemas

_log_level_env = os.getenv("LOG_LEVEL", "INFO").upper()
_log_level = getattr(logging, _log_level_env, logging.INFO)

logging.basicConfig(
    level=_log_level,
    format="[%(asctime)s] %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Financial Alarm System",
    description="API for managing financial alarms",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# CREATE OPERATIONS

@app.post("/alarms", response_model=schemas.AlarmResponse)
async def create_alarm(alarm: schemas.AlarmCreate, db: Session = Depends(get_db)):
    """Create a new financial alarm"""
    try:
        db_alarm = crud.create_alarm(db=db, alarm=alarm)
        return {
            "status": "ok",
            "message": "Alarm created successfully",
            "alarm_id": db_alarm.id
        }
    except Exception as e:
        logger.error(f"Error creating alarm: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# READ OPERATIONS

@app.get("/alarms", response_model=List[schemas.AlarmInDB])
async def list_alarms(
    email: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Retrieve all alarms with optional filtering by email or status"""
    try:
        if email:
            alarms = crud.get_alarms_by_email(db=db, email=email)
        else:
            alarms = db.query(models.Alarm).order_by(models.Alarm.created_at.desc()).all()
        
        return alarms
    except Exception as e:
        logger.error(f"Error listing alarms: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/alarms/{alarm_id}", response_model=schemas.AlarmInDB)
async def get_alarm(alarm_id: int, db: Session = Depends(get_db)):
    """Retrieve a specific alarm by ID"""
    try:
        alarm = crud.get_alarm(db=db, alarm_id=alarm_id)
        if not alarm:
            raise HTTPException(status_code=404, detail="Alarm not found")
        return alarm
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting alarm {alarm_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# UPDATE OPERATIONS

@app.put("/alarms/{alarm_id}", response_model=schemas.AlarmInDB)
async def update_alarm(
    alarm_id: int,
    alarm_update: schemas.AlarmUpdate,
    db: Session = Depends(get_db)
):
    """Update alarm status and error information"""
    try:
        alarm = crud.get_alarm(db=db, alarm_id=alarm_id)
        if not alarm:
            raise HTTPException(status_code=404, detail="Alarm not found")
        
        if alarm_update.status:
            alarm.status = alarm_update.status
        if alarm_update.last_error is not None:
            alarm.last_error = alarm_update.last_error
        
        db.commit()
        db.refresh(alarm)
        logger.info(f"Updated alarm id={alarm_id}")
        return alarm
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating alarm {alarm_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# DELETE OPERATIONS

@app.delete("/alarms/{alarm_id}", status_code=204)
async def delete_alarm(alarm_id: int, db: Session = Depends(get_db)):
    """Delete an alarm"""
    try:
        success = crud.delete_alarm(db=db, alarm_id=alarm_id)
        if not success:
            raise HTTPException(status_code=404, detail="Alarm not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting alarm {alarm_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# HEALTH CHECK

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Verify API and database connectivity"""
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

# ROOT ENDPOINT

@app.get("/")
async def root():
    """Provide API documentation and available endpoints"""
    return {
        "status": "ok",
        "message": "Financial Alarm System API",
        "endpoints": {
            "create_alarm": "POST /alarms",
            "list_alarms": "GET /alarms",
            "get_alarm": "GET /alarms/{id}",
            "update_alarm": "PUT /alarms/{id}",
            "delete_alarm": "DELETE /alarms/{id}",
            "health": "GET /health"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)