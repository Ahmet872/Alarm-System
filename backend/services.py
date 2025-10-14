import os
import logging
import pandas as pd
from typing import Tuple, Optional
from models import AssetClass, AlarmType, Alarm

logger = logging.getLogger(__name__)

# ================================================================
# PRICE FETCHERS
# ================================================================
def fetch_price(asset_class: AssetClass, symbol: str) -> Optional[float]:
    """Sync price fetcher, no aiohttp."""
    if os.getenv("ENV") == "development":
        logger.debug(f"DEV MODE: Returning mock price for {symbol}")
        return 100.0

    try:
        if asset_class == AssetClass.CRYPTO:
            import requests
            r = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}")
            if r.status_code != 200:
                raise ValueError(f"Binance API error: {r.status_code}")
            return float(r.json()["price"])
            
        elif asset_class in [AssetClass.FOREX, AssetClass.STOCK]:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            price = ticker.info.get("regularMarketPrice")
            if price is None:
                raise ValueError(f"No price data for {symbol}")
            return float(price)
            
    except Exception as e:
        logger.error(f"Error fetching price for {symbol}: {e}")
    return None

# ================================================================
# TECHNICAL INDICATORS
# ================================================================
def calc_rsi(prices: pd.Series, period: int = 14) -> float:
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs.iloc[-1]))

def calc_bollinger(prices: pd.Series, period: int = 20, std_dev: float = 2.0) -> Tuple[float, float]:
    sma = prices.rolling(window=period).mean().iloc[-1]
    std = prices.rolling(window=period).std().iloc[-1]
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    return upper, lower

def evaluate_condition(alarm: Alarm, current_price: float) -> bool:
    try:
        if alarm.alarm_type == AlarmType.PRICE:
            return current_price >= alarm.params["target_price"]

        elif alarm.alarm_type == AlarmType.RSI:
            prices = pd.Series([90.0, 95.0, 100.0])  # mock
            current_rsi = calc_rsi(prices, alarm.params.get("period", 14))
            return current_rsi >= alarm.params.get("threshold", 70)

        elif alarm.alarm_type == AlarmType.BOLLINGER:
            prices = pd.Series([90.0, 95.0, 100.0])  # mock
            upper, lower = calc_bollinger(
                prices,
                alarm.params.get("period", 20),
                alarm.params.get("std_dev", 2.0)
            )
            return current_price >= upper or current_price <= lower

        return False
    except Exception as e:
        logger.exception(f"Error evaluating condition for alarm {alarm.id}: {e}")
        return False

# ================================================================
# EMAIL SENDER (SYNC ONLY)
# ================================================================
def send_email(alarm: Alarm, current_price: float) -> bool:
    """Sync email sender, no aiosmtplib."""
    if os.getenv("ENV") == "development":
        logger.info(f"DEV MODE: Would send email for alarm {alarm.id}")
        return True

    from smtplib import SMTP
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    try:
        msg = MIMEMultipart()
        msg["From"] = os.getenv("SMTP_USER", "")
        msg["To"] = alarm.email
        msg["Subject"] = f"Financial Alarm Triggered: {alarm.asset_symbol}"

        body = f"""
        Your financial alarm has been triggered!

        Asset: {alarm.asset_symbol}
        Current Price: {current_price:.2f}
        Alarm Type: {alarm.alarm_type.value}
        Parameters: {alarm.params}
        """
        msg.attach(MIMEText(body, "plain"))

        with SMTP(os.getenv("SMTP_HOST", ""), int(os.getenv("SMTP_PORT", "587"))) as server:
            server.starttls()
            server.login(os.getenv("SMTP_USER", ""), os.getenv("SMTP_PASSWORD", ""))
            server.send_message(msg)

        logger.info(f"Email sent successfully for alarm {alarm.id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email for alarm {alarm.id}: {e}")
        return False
