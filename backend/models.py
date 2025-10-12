from sqlalchemy import Column, Integer, String, JSON, DateTime, Enum
from sqlalchemy.sql import func
from database import Base
import enum

class AssetClass(str, enum.Enum):
    CRYPTO = "crypto"
    FOREX = "forex"
    STOCK = "stock"

class AlarmType(str, enum.Enum):
    PRICE = "price"
    RSI = "rsi"
    BOLLINGER = "bollinger"

class Alarm(Base):
    __tablename__ = "alarms"

    id = Column(Integer, primary_key=True, index=True)
    asset_class = Column(Enum(AssetClass), nullable=False)
    asset_symbol = Column(String(50), nullable=False)
    alarm_type = Column(Enum(AlarmType), nullable=False)
    params = Column(JSON, nullable=False)
    email = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    status = Column(String(50), default="pending")  # pending, processing, sent, failed

    def __repr__(self):
        return f"<Alarm(id={self.id}, symbol={self.asset_symbol}, type={self.alarm_type})>"