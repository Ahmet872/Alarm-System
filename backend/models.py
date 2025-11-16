from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, JSON, DateTime, Index, Enum
from sqlalchemy.sql import func
from database import Base

class AssetClass(str, PyEnum):
    """Asset classification for alarms (cryptocurrency, forex, stock)"""
    CRYPTO = "crypto"
    FOREX = "forex"
    STOCK = "stock"

    @classmethod
    def values(cls):
        return [member.value for member in cls]

class AlarmType(str, PyEnum):
    """Type of condition to monitor (price, RSI, Bollinger Bands)"""
    PRICE = "price"
    RSI = "rsi"
    BOLLINGER = "bollinger"

    @classmethod
    def values(cls):
        return [member.value for member in cls]

class AlarmStatus(str, PyEnum):
    """Lifecycle states of an alarm"""
    PENDING = "pending"
    PROCESSING = "processing"
    TRIGGERED = "triggered"
    FAILED = "failed"
    DELETED = "deleted"

    @classmethod
    def values(cls):
        return [member.value for member in cls]

class Alarm(Base):
    """Database model for financial alerts with technical indicator support"""
    __tablename__ = "alarms"

    id = Column(Integer, primary_key=True, index=True)
    asset_class = Column(Enum(AssetClass), nullable=False, index=True)
    asset_symbol = Column(String(50), nullable=False, index=True)
    alarm_type = Column(Enum(AlarmType), nullable=False)
    params = Column(JSON, nullable=False)
    email = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    status = Column(Enum(AlarmStatus), default=AlarmStatus.PENDING, nullable=False, index=True)
    last_check_at = Column(DateTime, nullable=True)
    last_error = Column(String(500), nullable=True)
    
    __table_args__ = (
        Index('idx_status_created', 'status', 'created_at'),
        Index('idx_email_status', 'email', 'status'),
        Index('idx_type_status', 'alarm_type', 'status'),
    )

    def to_dict(self):
        """Convert alarm instance to dictionary representation"""
        return {
            "id": self.id,
            "asset_class": self.asset_class,
            "asset_symbol": self.asset_symbol,
            "alarm_type": self.alarm_type,
            "params": self.params,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "status": self.status,
            "last_check_at": self.last_check_at.isoformat() if self.last_check_at else None,
            "last_error": self.last_error
        }