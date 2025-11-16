from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import logging
import time
from typing import Generator

logger = logging.getLogger(__name__)

SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "mysql+pymysql://alarm_user:alarm_password@alarm_mysql:3306/alarm_system"
)

def get_db_engine(max_retries=5, retry_interval=5):
    """Create database engine with exponential retry logic for connection establishment"""
    for attempt in range(max_retries):
        try:
            engine = create_engine(
                SQLALCHEMY_DATABASE_URL,
                pool_pre_ping=True,
                pool_recycle=300,
                pool_size=5,
                max_overflow=10,
                echo=os.getenv("SQL_ECHO", "false").lower() == "true",
            )
            # Test connection with proper SQLAlchemy query
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                conn.commit()
            logger.info("Database connection established successfully")
            return engine
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed to connect to database after {max_retries} attempts: {e}")
                raise
            logger.warning(f"Database connection attempt {attempt + 1} failed, retrying in {retry_interval}s: {e}")
            time.sleep(retry_interval)

engine = get_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Generator:
    """
    Provide database session for FastAPI dependency injection.
    
    Yields session to endpoint, handles rollback on error, and ensures cleanup.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        logger.exception("Database session error: %s", str(e))
        raise
    finally:
        db.close()