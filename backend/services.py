import os
import logging
import pandas as pd
from typing import Tuple, Optional
from models import AssetClass, AlarmType, Alarm
import asyncio
import aiohttp
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import yfinance as yf

logger = logging.getLogger(__name__)

# ================================================================
# PRICE FETCHERS
# ================================================================
def fetch_price(asset_class: AssetClass, symbol: str) -> Optional[float]:
    """Sync version (legacy)."""
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
            ticker = yf.Ticker(symbol)
            price = ticker.info.get("regularMarketPrice")
            if price is None:
                raise ValueError(f"No price data for {symbol}")
            return float(price)
            
    except Exception as e:
        logger.error(f"Error fetching price for {symbol}: {e}")
    return None


async def async_fetch_price(asset_class: AssetClass, symbol: str) -> Optional[float]:
    """Async version using aiohttp."""
    if os.getenv("ENV") == "development":
        logger.debug(f"DEV MODE: Returning mock price for {symbol}")
        return 100.0
    
    try:
        if asset_class == AssetClass.CRYPTO:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status != 200:
                        raise ValueError(f"Binance API error: {resp.status}")
                    data = await resp.json()
                    return float(data["price"])
                    
        elif asset_class in [AssetClass.FOREX, AssetClass.STOCK]:
            return await asyncio.to_thread(fetch_price, asset_class, symbol)
            
    except asyncio.TimeoutError:
        logger.error(f"Timeout fetching price for {symbol}")
    except Exception as e:
        logger.error(f"Async fetch error for {symbol}: {e}")
    return None


# ================================================================
# TECHNICAL INDICATORS
# ================================================================
def calc_rsi(prices: pd.Series, period: int = 14) -> float:
    """Calculate RSI technical indicator"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs.iloc[-1]))


def calc_bollinger(prices: pd.Series, period: int = 20, std_dev: float = 2.0) -> Tuple[float, float]:
    """Calculate Bollinger Bands technical indicator"""
    sma = prices.rolling(window=period).mean().iloc[-1]
    std = prices.rolling(window=period).std().iloc[-1]
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    return upper, lower


def evaluate_condition(alarm: Alarm, current_price: float) -> bool:
    """Evaluate if alarm condition is met"""
    try:
        if alarm.alarm_type == AlarmType.PRICE:
            return current_price >= alarm.params["target_price"]

        elif alarm.alarm_type == AlarmType.RSI:
            # TODO: Implement real price history fetching
            prices = pd.Series([90.0, 95.0, 100.0])  # Mock data
            current_rsi = calc_rsi(prices, alarm.params["period"])
            return current_rsi >= alarm.params["threshold"]

        elif alarm.alarm_type == AlarmType.BOLLINGER:
            # TODO: Implement real price history fetching
            prices = pd.Series([90.0, 95.0, 100.0])  # Mock data
            upper, lower = calc_bollinger(
                prices,
                alarm.params["period"],
                alarm.params["std_dev"]
            )
            return current_price >= upper or current_price <= lower

        return False
    except Exception as e:
        logger.exception(f"Error evaluating condition for alarm {alarm.id}: {e}")
        return False


# ================================================================
# EMAIL SENDER
# ================================================================
def send_email(alarm: Alarm, current_price: float) -> bool:
    """Sync fallback email sender."""
    if os.getenv("ENV") == "development":
        logger.info(f"DEV MODE: Would send email for alarm {alarm.id}")
        return True

    from smtplib import SMTP
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

        with SMTP(
            os.getenv("SMTP_HOST", ""),
            int(os.getenv("SMTP_PORT", "587"))
        ) as server:
            server.starttls()
            server.login(
                os.getenv("SMTP_USER", ""),
                os.getenv("SMTP_PASSWORD", "")
            )
            server.send_message(msg)

        logger.info(f"Email sent successfully for alarm {alarm.id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email for alarm {alarm.id}: {e}")
        return False


async def async_send_email(alarm: Alarm, current_price: float) -> bool:
    """Async email sender using aiosmtplib."""
    if os.getenv("ENV") == "development":
        logger.info(f"DEV MODE: Would send email for alarm {alarm.id}")
        return True

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

    try:
        await aiosmtplib.send(
            msg,
            hostname=os.getenv("SMTP_HOST", ""),
            port=int(os.getenv("SMTP_PORT", "587")),
            username=os.getenv("SMTP_USER", ""),
            password=os.getenv("SMTP_PASSWORD", ""),
            start_tls=True,
            timeout=30
        )
        logger.info(f"Async email sent successfully for alarm {alarm.id}")
        return True
    except Exception as e:
        logger.error(f"Async email send failed for alarm {alarm.id}: {e}")
        return False