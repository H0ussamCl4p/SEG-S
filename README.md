# IIoT Predictive Maintenance Dashboard

## Overview
Enterprise-grade IIoT predictive maintenance system with:
- **JWT Authentication** - Secure token-based login with PostgreSQL user storage
- **Microservice Architecture** - Dedicated auth-service, ai-engine, and web-frontend
- **FastAPI Backend** - Real-time API with anomaly detection
- **Next.js Dashboard** - Modern UI with AI-powered insights
- **MQTT Integration** - ESP32/PLC equipment support
- **InfluxDB Time Series** - High-performance sensor data storage
- **Role-Based Access Control** - Admin & Operator roles

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Port availability: 3001, 8000, 8001, 5432, 8086, 1883

### Setup (5 minutes)

1. **Start Services**:
   ```powershell
   docker compose up -d --build
   ```

2. **Access Dashboard**:
   ```powershell
   # Login page
   Start-Process http://localhost:3001/login
   
   # Login with default credentials, then access:
   Start-Process http://localhost:3001/dashboard
   ```

## ☁️ Deployment

- **Azure Container Apps (current target):** see [deploy/azure/README.md](deploy/azure/README.md).
  One-shot: `DEEPSEEK_API_KEY=... POSTGRES_PASSWORD=... bash deploy/azure/setup-azure.sh`.
  The chatbot LLM runs on the DeepSeek API (OpenAI-compatible) — no GPU needed.
- **Single VPS (legacy):** `bash deploy/setup-vps.sh` (nginx + certbot + docker-compose).

## 🔐 Authentication

### JWT with PostgreSQL
- Token-based authentication via dedicated auth-service
- User data persists in PostgreSQL database
- Bcrypt password hashing
- No external OAuth dependencies

### Default Accounts
- Username: `admin` / Password: `admin123` (admin role)
- Username: `operator` / Password: `operator123` (operator role)

**⚠️ Change passwords in production!**

## Backend API
- `GET /api/live`: Latest telemetry and AI assessment.
	- `vibration` (number)
	- `temperature` (number)
	- `score` (number, AI Health Score)
	- `status` (NORMAL|WARNING|ANOMALY)
	- `timestamp` (ISO string)
	- `health` (score/status/color/days_until_maintenance/maintenance_urgency)
- `GET /api/history?limit=50`: Last readings for charts.
	- Array of `{ timestamp, vibration, temperature, score, status }`
- `GET /api/stats`, `GET /api/alerts`, `GET /api/patterns`: Aggregates and insights.

## AI Score: Definition and Meaning
The `score` is the AI Health Score per reading, expressing confidence that the machine is healthy.

- Range: `0.0` to `1.0` (higher is healthier) for visualization consistency.
- Source:
	- With a trained anomaly model (IsolationForest), we derive a per-sample score and normalize it. Lower model scores indicate anomaly; higher indicate normal.
	- If no model score is available, a fallback heuristic estimates the score from vibration and temperature. It auto-calibrates expected maxima from recent data in InfluxDB (last ~2h) so the scale adapts to your environment.
- Status mapping (used across `/api/live` and `/api/history`):
	- `ANOMALY`: score < 0.1
	- `WARNING`: 0.1 ≤ score < 0.3
	- `NORMAL`: score ≥ 0.3

The separate `health` object provides an aggregated 0–100 score and a days-until-maintenance estimate for planning.

## Environment Variables
- `INFLUX_HOST`, `INFLUX_PORT`, `INFLUX_DB`: InfluxDB connection.
- `MQTT_BROKER`: MQTT broker host for simulator data.
- `EXPECTED_MAX_VIBRATION`: Max expected vibration for fallback normalization.
- `EXPECTED_MAX_TEMPERATURE`: Max expected temperature for fallback normalization.

## Quick Start (Windows PowerShell)
```powershell
docker-compose up -d
Start-Sleep -Seconds 3
Start-Process http://localhost:3001/dashboard
```
