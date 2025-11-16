import os
import logging
import requests
import pandas as pd
from typing import Optional, Dict, Any, Tuple
from functools import lru_cache
import boto3
from botocore.exceptions import ClientError
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

class MarketDataError(Exception):
    """Exception raised when market data retrieval fails"""
    pass

class PriceService:
    """Fetch current and historical market prices from configured data source"""
    
    def __init__(self):
        self.api_url = os.getenv("PRICE_API_URL", "https://api.coingecko.com/api/v3")
        self.api_key = os.getenv("PRICE_API_KEY", "")
        self.timeout = int(os.getenv("PRICE_API_TIMEOUT", "10"))
        self.max_retries = int(os.getenv("PRICE_API_MAX_RETRIES", "3"))
        logger.info(f"PriceService initialized with URL: {self.api_url}")

    def get_current_price(self, symbol: str) -> Optional[float]:
        """Retrieve current market price with automatic retry on failure"""
        for attempt in range(self.max_retries):
            try:
                headers = {"X-API-KEY": self.api_key} if self.api_key else {}
                
                if "coingecko" in self.api_url.lower():
                    parts = symbol.split("-")
                    if len(parts) != 2:
                        logger.error(f"Invalid symbol format for CoinGecko: {symbol}")
                        raise MarketDataError(f"Invalid symbol format: {symbol}")
                    
                    coin_id = parts[0].lower()
                    vs_currency = parts[1].lower()
                    
                    response = requests.get(
                        f"{self.api_url}/simple/price",
                        params={
                            "ids": coin_id,
                            "vs_currencies": vs_currency,
                            "include_market_cap": "false",
                            "include_24hr_vol": "false"
                        },
                        headers=headers,
                        timeout=self.timeout
                    )
                else:
                    response = requests.get(
                        f"{self.api_url}/price",
                        params={"symbol": symbol},
                        headers=headers,
                        timeout=self.timeout
                    )
                
                response.raise_for_status()
                data = response.json()
                
                if "coingecko" in self.api_url.lower():
                    parts = symbol.split("-")
                    coin_id = parts[0].lower()
                    vs_currency = parts[1].lower()
                    price = float(data[coin_id][vs_currency])
                else:
                    price = float(data.get("price", 0))
                
                logger.info(f"Fetched {symbol} price: {price}")
                return price
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"Failed to fetch price for {symbol} after {self.max_retries} attempts: {str(e)}")
                    return None
                logger.warning(f"Price fetch attempt {attempt + 1} failed for {symbol}, retrying...")
                continue
        return None

    @lru_cache(maxsize=100)
    def get_historical_data(self, symbol: str, period: int = 14) -> Optional[pd.DataFrame]:
        """Retrieve historical price data for technical analysis calculations"""
        try:
            headers = {"X-API-KEY": self.api_key} if self.api_key else {}
            response = requests.get(
                f"{self.api_url}/history",
                params={"symbol": symbol, "period": period},
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            return df
        except Exception as e:
            logger.error(f"Failed to fetch historical data for {symbol}: {str(e)}")
            return None

class TechnicalAnalysis:
    """Calculate technical indicators for market analysis"""
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> Optional[float]:
        """Compute Relative Strength Index (RSI) momentum indicator"""
        try:
            if len(prices) < period:
                logger.warning(f"Not enough data for RSI calculation (need {period}, got {len(prices)})")
                return None
            
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            result = float(rsi.iloc[-1])
            logger.info(f"Calculated RSI: {result}")
            return result
        except Exception as e:
            logger.error(f"RSI calculation failed: {str(e)}")
            return None

    @staticmethod
    def calculate_bollinger_bands(
        prices: pd.Series, 
        period: int = 20, 
        std_dev: float = 2
    ) -> Optional[Tuple[float, float]]:
        """Compute Bollinger Bands upper and lower boundaries"""
        try:
            if len(prices) < period:
                logger.warning(f"Not enough data for Bollinger Bands (need {period}, got {len(prices)})")
                return None
            
            sma = prices.rolling(window=period).mean()
            std = prices.rolling(window=period).std()
            upper_band = sma + (std * std_dev)
            lower_band = sma - (std * std_dev)
            
            result = (float(upper_band.iloc[-1]), float(lower_band.iloc[-1]))
            logger.info(f"Calculated Bollinger Bands: Upper={result[0]}, Lower={result[1]}")
            return result
        except Exception as e:
            logger.error(f"Bollinger Bands calculation failed: {str(e)}")
            return None

class EmailService:
    """Send email notifications via AWS SES or SMTP backend"""
    
    def __init__(self):
        self.backend = os.getenv("MAIL_BACKEND", "smtp")
        
        if self.backend == "aws_ses":
            self.ses_client = boto3.client('ses', region_name=os.getenv('AWS_REGION', 'us-east-1'))
            self.source_email = os.getenv('SES_SOURCE_EMAIL', 'no-reply@example.com')
            logger.info("EmailService initialized with AWS SES")
        else:
            self.smtp_host = os.getenv('SMTP_HOST', 'maildev')
            self.smtp_port = int(os.getenv('SMTP_PORT', '1025'))
            self.smtp_user = os.getenv('SMTP_USER', '')
            self.smtp_password = os.getenv('SMTP_PASSWORD', '')
            self.source_email = os.getenv('SES_SOURCE_EMAIL', 'no-reply@example.com')
            logger.info(f"EmailService initialized with SMTP: {self.smtp_host}:{self.smtp_port}")

    def send_alarm_email(self, to_address: str, subject: str, body: str) -> bool:
        """Send email notification using configured backend"""
        try:
            if self.backend == "aws_ses":
                return self._send_via_ses(to_address, subject, body)
            else:
                return self._send_via_smtp(to_address, subject, body)
        except Exception as e:
            logger.error(f"Failed to send email to {to_address}: {str(e)}")
            return False

    def _send_via_ses(self, to_address: str, subject: str, body: str) -> bool:
        """Dispatch email through AWS SES service"""
        try:
            response = self.ses_client.send_email(
                Source=self.source_email,
                Destination={'ToAddresses': [to_address]},
                Message={
                    'Subject': {'Data': subject},
                    'Body': {'Text': {'Data': body}}
                }
            )
            logger.info(f"Email sent via SES: {response['MessageId']}")
            return True
        except ClientError as e:
            logger.error(f"SES send failed: {str(e)}")
            return False

    def _send_via_smtp(self, to_address: str, subject: str, body: str) -> bool:
        """Dispatch email through SMTP for local testing and development"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.source_email
            msg['To'] = to_address
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.sendmail(self.source_email, to_address, msg.as_string())
            
            logger.info(f"Email sent via SMTP to {to_address}")
            return True
        except Exception as e:
            logger.error(f"SMTP send failed: {str(e)}")
            return False

class AlarmEvaluator:
    """Evaluate if market conditions trigger configured alarms"""
    
    def __init__(self):
        self.price_service = PriceService()
        self.technical = TechnicalAnalysis()
        logger.info("AlarmEvaluator initialized")

    def evaluate_price_alarm(self, symbol: str, params: Dict[str, Any]) -> bool:
        """Determine if current price crosses target threshold"""
        try:
            current_price = self.price_service.get_current_price(symbol)
            if current_price is None:
                logger.warning(f"Could not fetch price for {symbol}")
                return False
            
            target_price = float(params['target_price'])
            direction = params.get('direction', 'above').lower()
            
            if direction == 'above':
                triggered = current_price >= target_price
            else:
                triggered = current_price <= target_price
            
            logger.info(f"Price alarm {symbol}: current={current_price}, target={target_price}, direction={direction}, triggered={triggered}")
            return triggered
        except Exception as e:
            logger.error(f"Error evaluating price alarm: {str(e)}")
            return False

    def evaluate_rsi_alarm(self, symbol: str, params: Dict[str, Any]) -> bool:
        """Determine if RSI value crosses defined threshold"""
        try:
            period = int(params['period'])
            threshold = float(params['threshold'])
            
            df = self.price_service.get_historical_data(symbol, period)
            if df is None or 'close' not in df.columns:
                logger.warning(f"Could not fetch historical data for {symbol}")
                return False
            
            rsi = self.technical.calculate_rsi(df['close'], period)
            if rsi is None:
                logger.warning(f"Could not calculate RSI for {symbol}")
                return False
            
            triggered = rsi <= threshold
            logger.info(f"RSI alarm {symbol}: rsi={rsi}, threshold={threshold}, triggered={triggered}")
            return triggered
        except Exception as e:
            logger.error(f"Error evaluating RSI alarm: {str(e)}")
            return False

    def evaluate_bollinger_alarm(self, symbol: str, params: Dict[str, Any]) -> bool:
        """Determine if price moves beyond Bollinger Bands boundaries"""
        try:
            period = int(params['period'])
            std_dev = float(params['std_dev'])
            
            df = self.price_service.get_historical_data(symbol, period)
            if df is None or 'close' not in df.columns:
                logger.warning(f"Could not fetch historical data for {symbol}")
                return False
            
            bands = self.technical.calculate_bollinger_bands(df['close'], period, std_dev)
            if bands is None:
                logger.warning(f"Could not calculate Bollinger Bands for {symbol}")
                return False
            
            current_price = float(df['close'].iloc[-1])
            upper, lower = bands
            
            triggered = current_price >= upper or current_price <= lower
            logger.info(f"Bollinger alarm {symbol}: price={current_price}, upper={upper}, lower={lower}, triggered={triggered}")
            return triggered
        except Exception as e:
            logger.error(f"Error evaluating Bollinger alarm: {str(e)}")
            return False