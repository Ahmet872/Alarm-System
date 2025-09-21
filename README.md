# Financial One-shot Alarm System

## Overview
This project is a minimal web application that allows users to create one-shot financial alarms without any account or login. Once an alarm is triggered, an email notification is sent and the alarm is automatically removed from the database. The application is intended as a professional showcase for a full-stack project with modern tools.

## Tech Stack
- **Frontend:** Next.js + React + TailwindCSS  
- **Backend:** FastAPI + SQLAlchemy + MySQL  
- **Worker:** Python script for scheduled alarm evaluation  
- **Database:** MySQL (Docker container)  
- **Email Notifications:** SMTP (configurable via .env)  
- **Containerization:** Docker + Docker Compose  
- **Testing & CI:** Pytest + GitHub Actions  

## Features
- Single-page, no-login UX
- Supports crypto, forex, and stock alarms
- Alarm types: Price, RSI, Bollinger Bands
- Configurable alarm parameters
- Email notification on trigger
- Dockerized local development
- Minimal unit and integration tests

## Development Setup
1. Clone the repository:
```bash
git clone git@github.com:USERNAME/alarm-system.git
cd alarm-system
