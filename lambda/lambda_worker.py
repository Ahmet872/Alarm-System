import pandas as pd
import os
import logging
import json
import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import boto3
import pymysql
import requests
from botocore.exceptions import ClientError

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="[%(asctime)s] %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class MarketDataService:
    """Fetch market prices and historical data from external API"""
    
    def __init__(self):
        self.api_url = os.getenv("PRICE_API_URL")
        self.api_key = os.getenv("PRICE_API_KEY")
        self.timeout = int(os.getenv("API_TIMEOUT", "10"))
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))

    def get_price(self, symbol: str) -> Optional[float]:
        """Retrieve current price with exponential backoff retry logic"""
        for attempt in range(self.max_retries):
            try:
                headers = {"X-API-KEY": self.api_key} if self.api_key else {}
                response = requests.get(
                    f"{self.api_url}/price",
                    params={"symbol": symbol},
                    headers=headers,
                    timeout=self.timeout)
                
                response.raise_for_status()
                data = response.json()
                return float(data.get("price", 0))
            except Exception as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"Price fetch failed for {symbol}: {e}")
                    return None
                time.sleep(2 ** attempt)
        return None

    def get_historical_data(self, symbol: str, period: int) -> Optional[pd.DataFrame]:
        """Fetch historical price data for technical analysis"""
        try:
            headers = {"X-API-KEY": self.api_key} if self.api_key else {}
            response = requests.get(
                f"{self.api_url}/history",
                params={"symbol": symbol, "period": period},
                headers=headers,
                timeout=self.timeout)
            
            response.raise_for_status()
            data = response.json()
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df.set_index('timestamp')
        except Exception as e:
            logger.error(f"Historical data fetch failed for {symbol}: {e}")
            return None

class TechnicalIndicators:
    """Calculate technical analysis indicators for alarm evaluation"""
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int) -> Optional[float]:
        """Compute Relative Strength Index momentum indicator"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return float(rsi.iloc[-1])
        except Exception as e:
            logger.error(f"RSI calculation failed: {e}")
            return None

    @staticmethod
    def calculate_bollinger_bands(prices: pd.Series, period: int, std_dev: float) -> Optional[tuple]:
        """Compute Bollinger Bands upper and lower boundaries"""
        try:
            sma = prices.rolling(window=period).mean()
            std = prices.rolling(window=period).std()
            upper = sma + (std * std_dev)
            lower = sma - (std * std_dev)
            return float(upper.iloc[-1]), float(lower.iloc[-1])
        except Exception as e:
            logger.error(f"Bollinger Bands calculation failed: {e}")
            return None

class DatabaseManager:
    """Manage database connections and alarm state operations"""
    
    def __init__(self):
        self.connection = None
        self.connect()

    def connect(self):
        """Establish connection to RDS MySQL database"""
        try:
            self.connection = pymysql.connect(
                host=os.getenv("RDS_HOST"),
                user=os.getenv("RDS_USER"),
                password=os.getenv("RDS_PASSWORD"),
                database=os.getenv("RDS_DB"),
                cursorclass=pymysql.cursors.DictCursor
            )
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def get_pending_alarms(self) -> List[Dict]:
        """Retrieve all alarms awaiting processing"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM alarms WHERE status = 'pending'"
                )
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Failed to fetch pending alarms: {e}")
            self.connect()
            return []

    def delete_alarm(self, alarm_id: int) -> bool:
        """Remove triggered alarm from database"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM alarms WHERE id = %s",
                    (alarm_id,)
                )
                self.connection.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to delete alarm {alarm_id}: {e}")
            return False

    def update_alarm_status(self, alarm_id: int, status: str, error: Optional[str] = None) -> bool:
        """Update alarm state and track last check time"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    """UPDATE alarms 
                       SET status = %s, 
                           last_error = %s,
                           last_check_at = NOW()
                       WHERE id = %s""",
                    (status, error, alarm_id)
                )
                self.connection.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to update alarm {alarm_id}: {e}")
            return False

class EmailService:
    """Send email notifications via AWS SES"""
    
    def __init__(self):
        self.ses = boto3.client('ses', region_name=os.getenv('AWS_REGION', 'us-east-1'))
        self.source_email = os.getenv('SES_SOURCE_EMAIL')

    def send_alert(self, to_address: str, subject: str, body: str) -> bool:
        """Dispatch alert email to recipient"""
        try:
            response = self.ses.send_email(
                Source=self.source_email,
                Destination={'ToAddresses': [to_address]},
                Message={
                    'Subject': {'Data': subject},
                    'Body': {'Text': {'Data': body}}
                }
            )
            logger.info(f"Email sent: {response['MessageId']}")
            return True
        except ClientError as e:
            logger.error(f"Failed to send email: {e}")
            return False

class AlarmProcessor:
    """Process alarms, evaluate conditions, and trigger notifications"""
    
    def __init__(self):
        self.market_data = MarketDataService()
        self.technical = TechnicalIndicators()
        self.db = DatabaseManager()
        self.email = EmailService()
        self.metrics = []

    def process_price_alarm(self, alarm: Dict) -> bool:
        """Evaluate if current price crosses target threshold"""
        current_price = self.market_data.get_price(alarm['asset_symbol'])
        if current_price is None:
            return False

        params = alarm['params']
        target_price = float(params['target_price'])
        direction = params.get('direction', 'above')

        if direction == 'above':
            return current_price >= target_price
        return current_price <= target_price

    def process_rsi_alarm(self, alarm: Dict) -> bool:
        """Evaluate if RSI value crosses defined threshold"""
        params = alarm['params']
        df = self.market_data.get_historical_data(
            alarm['asset_symbol'],
            params['period']
        )
        if df is None:
            return False

        rsi = self.technical.calculate_rsi(df['close'], params['period'])
        if rsi is None:
            return False

        return rsi <= params['threshold']

    def process_bollinger_alarm(self, alarm: Dict) -> bool:
        """Evaluate if price moves beyond Bollinger Bands boundaries"""
        params = alarm['params']
        df = self.market_data.get_historical_data(
            alarm['asset_symbol'],
            params['period']
        )
        if df is None:
            return False

        bands = self.technical.calculate_bollinger_bands(
            df['close'],
            params['period'],
            params['std_dev']
        )
        if bands is None:
            return False

        current_price = df['close'].iloc[-1]
        upper, lower = bands
        return current_price >= upper or current_price <= lower

    def process_alarm(self, alarm: Dict) -> None:
        """Execute full alarm processing workflow including evaluation and notification"""
        alarm_id = alarm['id']
        try:
            self.db.update_alarm_status(alarm_id, 'processing')

            triggered = False
            if alarm['alarm_type'] == 'price':
                triggered = self.process_price_alarm(alarm)
            elif alarm['alarm_type'] == 'rsi':
                triggered = self.process_rsi_alarm(alarm)
            elif alarm['alarm_type'] == 'bollinger':
                triggered = self.process_bollinger_alarm(alarm)

            if triggered:
                subject = f"Financial Alarm Triggered: {alarm['asset_symbol']}"
                body = self._generate_alert_body(alarm)
                if self.email.send_alert(alarm['email'], subject, body):
                    self.db.delete_alarm(alarm_id)
                    self.metrics.append({'id': alarm_id, 'status': 'triggered'})
                else:
                    self.db.update_alarm_status(alarm_id, 'failed', 'Email sending failed')
                    self.metrics.append({'id': alarm_id, 'status': 'email_failed'})
            else:
                self.db.update_alarm_status(alarm_id, 'pending')
                self.metrics.append({'id': alarm_id, 'status': 'pending'})

        except Exception as e:
            logger.exception(f"Error processing alarm {alarm_id}")
            self.db.update_alarm_status(alarm_id, 'failed', str(e))
            self.metrics.append({'id': alarm_id, 'status': 'error'})

    def _generate_alert_body(self, alarm: Dict) -> str:
        """Format notification email content"""
        return f"""
Financial Alarm Triggered!

Asset: {alarm['asset_symbol']}
Type: {alarm['alarm_type'].upper()}
Conditions: {json.dumps(alarm['params'], indent=2)}
Time (UTC): {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}

This is an automated message from your Financial Alarm System.
        """.strip()

    def publish_metrics(self) -> None:
        """Send processing metrics to CloudWatch"""
        try:
            cloudwatch = boto3.client('cloudwatch')
            
            metrics_data = []
            for status in ['triggered', 'failed', 'pending', 'error']:
                count = len([m for m in self.metrics if m['status'] == status])
                metrics_data.append({
                    'MetricName': f'Alarms{status.capitalize()}',
                    'Value': count,
                    'Unit': 'Count',
                    'Timestamp': datetime.now(timezone.utc)
                })

            cloudwatch.put_metric_data(
                Namespace='FinancialAlarms',
                MetricData=metrics_data
            )
        except Exception as e:
            logger.error(f"Failed to publish metrics: {e}")

def lambda_handler(event: Dict, context: Any) -> Dict:
    """AWS Lambda entry point for alarm processing"""
    logger.info(f"Lambda triggered: {json.dumps(event)}")
    
    processor = AlarmProcessor()
    
    try:
        alarms = processor.db.get_pending_alarms()
        logger.info(f"Found {len(alarms)} pending alarms")

        for alarm in alarms:
            processor.process_alarm(alarm)

        processor.publish_metrics()

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Alarm processing completed",
                "metrics": processor.metrics
            })
        }

    except Exception as e:
        logger.exception("Lambda execution failed")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": str(e)
            })
        }

if __name__ == "__main__":
    lambda_handler({}, None)