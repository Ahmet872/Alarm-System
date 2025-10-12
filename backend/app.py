from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import logging

import crud
import models
import schemas
from database import engine, get_db

logger = logging.getLogger("uvicorn.error")

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Financial One-shot Alarm System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Prod ortamda frontend URL ile değiştir
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/alarms", response_model=schemas.Alarm, status_code=201)
def create_alarm(alarm: schemas.AlarmCreate, db: Session = Depends(get_db)):
    """Create a new financial alarm."""
    try:
        return crud.create_alarm(db=db, alarm=alarm)
    except Exception as e:
        logger.exception("Error creating alarm")
        raise HTTPException(status_code=400, detail="Error creating alarm")

@app.get("/assets/{asset_class}", response_model=schemas.AssetsResponse)
def get_assets(asset_class: schemas.AssetClass):
    """Return available assets for the requested asset class."""
    assets_map = {
        schemas.AssetClass.CRYPTO: ["BTCUSDT", "ETHUSDT", "BNBUSDT"],
        schemas.AssetClass.FOREX: ["EURUSD=X", "GBPUSD=X", "USDJPY=X"],
        schemas.AssetClass.STOCK: ["AAPL", "GOOGL", "MSFT"]
    }
    return {"assets": assets_map[asset_class]}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
