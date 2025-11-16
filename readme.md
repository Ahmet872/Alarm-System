# Financial Alarm System

A real-time monitoring system for cryptocurrency, forex, and stock prices with automated email notifications. Set custom alerts based on price targets, RSI levels, or Bollinger Band breakouts.

## Features

- **Multi-Asset Support**: Cryptocurrencies (BTC-USD, ETH-USD), Forex pairs (EUR/USD, GBP/USD), and Stocks (AAPL, GOOGL)
- **Technical Indicators**: Price alerts, RSI momentum tracking, Bollinger Band breakouts
- **Email Notifications**: Instant alerts via AWS SES when conditions are met
- **Auto-Cleanup**: Triggered alarms are automatically removed from the system
- **Cloud-Native**: Built on AWS Lambda, RDS, and EventBridge for serverless monitoring

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Git

### Local Setup

```bash
git clone https://github.com/Ahmet872/alarm-system.git
cd alarm-system
docker-compose up --build
```

Acces the application at **http://localhost:3000**

The local environment includes:
- Frontend: http://localhost:300
- Backend API: http://localhost:8000/docs
- MySQL: localhost:3306
- MailDev (Email Testing): http://localhost:1080

## Enviornment Configuration

### Local Development

```env
# Database
DATABASE_URL=mysql+pymysql://alarm_user:alarm_password@alarm_mysql:3306/alarm_system

# Frontend
FRONTEND_ORIGIN=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000

# Market Data
PRICE_API_URL=https://api.coingecko.com/api/v3

# Email (MailDev for local testing)
MAIL_BACKEND=smtp
SMTP_HOST=maildev
SMTP_PORT=1025
SES_SOURCE_EMAIL=noreply@alarm-system.local
```

### Production (AWS)

```env
# Database (RDS)
RDS_HOST=alarm-system-db.c6xeueea0etk.us-east-1.rds.amazonaws.com
RDS_USER=alarm_user
RDS_PASSWORD=Alarm_system123.
RDS_DB=alarm_system
RDS_PORT=3306

# Email (AWS SES)
MAIL_BACKEND=aws_ses
SES_SOURCE_EMAIL=noreply@example.com

# Market Data
PRICE_API_URL=https://api.coingecko.com/api/v3
```

## How It Works

1. User creates an alarm through the web interface.
2. Backend stores the alarm in MySQL
3. AWS Lambda checks conditions every minute via EventBridge
4. When a condition is met, an email is sent via SES and the alarm is deleted
5. All operations are logged to an audit table for tracking

## Alarm Types

### Price Alert

Triggers when an asset reaches a specific price point.

```json
{
  "alarm_type": "price",
  "asset_class": "crypto",
  "asset_symbol": "BTC-USD",
  "email": "user@example.com",
  "params": {
    "target_price": 50000,
    "direction": "above"
  }
}
```

### RSI Alert

Trigers based on Relative Strength İndex momentum indicator (oversold/overbought conditions).

```json
{
  "alarm_type": "rsi",
  "asset_class": "crypto",
  "asset_symbol": "ETH-USD",
  "email": "user@example.com",
  "params": {
    "period": 14,
    "threshold": 30
  }
}
```

### Bollinger Bands Alert

Triggers when price breaks above or below Bollinger Bands.

```json
{
  "alarm_type": "bollinger",
  "asset_class": "stocks",
  "asset_symbol": "AAPL",
  "email": "user@example.com",
  "params": {
    "period": 20,
    "std_dev": 2
  }
}
```

## API Referencee

### Create Alarm

```bash
curl -X POST http://localhost:8000/alarms \
  -H "Content-Type: application/json" \
  -d '{
    "asset_class": "crypto",
    "asset_symbol": "BTC-USD",
    "alarm_type": "price",
    "email": "you@example.com",
    "params": {
      "target_price": 50000,
      "direction": "above"
    }
  }'
```

### List Alarms

```bash
curl "http://localhost:8000/alarms?email=you@example.com"
```

### Delete Alarm

```bash
curl -X DELETE http://localhost:8000/alarms/1
```

### Health Check

```bash
curl http://localhost:8000/health
```

Full API documentation is available at http://localhost:8000/docs (Swagger UI)

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Next.js, React, TypeScript, Tailwind CSS |
| Backend | FastAPI, SQLAlchemy, PyMySQL |
| Database | MySQL 8.0 |
| Cloud Infrastructure | AWS Lambda, RDS, SES, EventBridge |
| Market Data | CoinGecko API |
| Monitoring | CloıdWatch |
| Email (Local) | MailDev |
| Email (Production) | AWS SES |

## AWS Production Deployment

### Lambda Configuration

Set the following environment variables in your Lambda function:

```
RDS_HOST = alarm-system-db.c6xeueea0etk.us-east-1.rds.amazonaws.com
RDS_USER = alarm_user
RDS_PASSWORD = Alarm_system123.
RDS_DB = alarm_system
RDS_PORT = 3306
MAIL-BACKEND = aws_ses
SES_SOURCE_EMAIL = noreply@example.com
PRICE_API_URL = https://api.coingecko.com/api/v3
```

### EventBridge Schedule

Configure EventBridge to trigger the Lambda function every minute:

```
Rate: 1 minute
Cron Expression: cron(* * * * ? *)
Target: financial-alarm-worker Lambda function
```

### Testing Lambda

```bash
aws lambda invoke \
  --function-name financial-alarm-worker \
  --region us-east-1 \
  response.json
```

### Monitoring

```bash
aws logs tail /aws/lambda/financial-alarm-worker --follow
```

### Deployment Checklist

- [ ] RDS instance creted and publicly accesible
- [ ] Lambda function deployed (Python 3.11 runtime)
- [ ] Lambda environment variables configured
- [ ] EventBridge rule created with 1-minute schedule
- [ ] SES domain/email verified
- [ ] Test email successfully sent
- [ ] CloudWatch alarms configured
- [ ] Alarm cleanup verified

**Features**
- Multiple recipients per alarm
- Webhook integrations (Discord, Slack, Telegram)
- Alarm editing and history
- Price charts with historical data
- Additional indicators (MACD, Stocastic, Divergence)
- Mobile app (React Native)


## Contact

- **Email**: seyyitahmetarslan872@gmail.com
- **Issues**: [GitHub Issues](https://github.com/Ahmet872/financial-alarm-system/issues)

## License

MIT License - See LICENSE file for details

---

**Last Updated**: November 16, 2025  
**Author**: [Ahmet8721](https://github.com/Ahmet8721)  
**Status**: 🚀 Production Ready - Lambda + RDS running on AWS