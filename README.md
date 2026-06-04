# 🌦️ Kheyti Weather Advisory Pipeline

A production-ready weather advisory system that automatically syncs greenhouse data, fetches weather forecasts, generates rule-based agricultural advisories, and delivers WhatsApp notifications to farmers through WATI.

---

## Features

- Zoho CRM greenhouse synchronization
- Incremental sync using Modified_Time
- Address geocoding using Google Maps API
- Geocode result caching
- Geographic greenhouse clustering
- OpenWeather forecast integration
- YAML-driven advisory rule engine
- Structured advisory generation
- Advisory storage in PostgreSQL JSONB
- WhatsApp delivery through WATI templates
- Advisory deduplication
- Weather caching
- Parallel processing support
- Debug mode for safe testing

---

## System Architecture

```text
Zoho CRM
    ↓
Sync Pipeline
    ↓
PostgreSQL
    ↓
Geocode Pipeline
    ↓
Greenhouse Records
    ↓
Cluster Engine
    ↓
Weather Pipeline
    ↓
OpenWeather API
    ↓
Weather Data
    ↓
YAML Rule Engine
    ↓
Structured Advisory JSON
    ↓
advisory_logs (JSONB)
    ↓
Delivery Pipeline
    ↓
WATI
    ↓
WhatsApp
```

## Project Structure

```text
app/
│
├── config/
├── core/
├── external/
├── repositories/
├── services/
├── pipelines/
│
├── database.py
├── config.py
├── constants.py
└── main.py
```

## Weekly Pipeline

The weekly pipeline maintains greenhouse master data.

### Run

```bash
python -m app.main weekly
```

### Responsibilities

- Fetch greenhouse records from Zoho CRM
- Filter valid greenhouse records
- Insert/update greenhouse data
- Identify missing coordinates
- Geocode missing locations
- Cache geocode results

---

## Daily Pipeline

The daily pipeline generates and delivers weather advisories.

### Run

```bash
python -m app.main daily
```

### Responsibilities

- Build greenhouse clusters
- Fetch weather forecasts
- Generate advisories
- Store advisories
- Deliver WhatsApp notifications

---

## Advisory Storage

Advisories are stored directly as structured JSON in PostgreSQL JSONB.

Example:

```json
{
  "day3": "Rainfall is expected later this week. Plan field operations accordingly.",
  "today": "Heavy rain expected today. Ensure proper drainage and avoid irrigation. Expected rain window: 02:30 PM to 05:30 PM, 09:30 PM to 09:30 PM. Strong winds expected today. Avoid pesticide spraying. Peak winds expected around 09:30 AM.",
  "current": "Strong winds are occurring currently. Avoid pesticide spraying.",
  "tomorrow": "Heavy rainfall is expected tomorrow. Plan irrigation and field activities accordingly. Expected rain window: 02:30 AM to 08:30 AM, 01:30 PM to 11:30 PM. Strong winds are expected tomorrow. Plan spraying activities accordingly. Peak winds expected around 07:30 PM.",
  "greenhouse": "GH-2043"
}
```

---

## WhatsApp Template

| Variable | Value |
|-----------|---------|
| {{1}} | Farmer Name |
| {{2}} | Greenhouse Name |
| {{3}} | Current Conditions |
| {{4}} | Today's Advisory |
| {{5}} | Tomorrow's Advisory |
| {{6}} | Day 3 Outlook |

---

## Database Tables

- greenhouses
- greenhouses_missing_location
- geocode_cache
- weather_cache
- weather_data
- advisory_logs
- sync_metadata

### advisory_logs

| Column | Type |
|----------|----------|
| greenhouse_id | TEXT |
| greenhouse_name | TEXT |
| farmer_name | TEXT |
| phone | TEXT |
| cluster_key | TEXT |
| advisory | JSONB |
| advisory_date | DATE |
| delivery_status | TEXT |
| sent_at | TIMESTAMP |

---

## Environment Variables

```env
DEBUG_MODE=true

ZOHO_CLIENT_ID=
ZOHO_CLIENT_SECRET=
ZOHO_REFRESH_TOKEN=
ZOHO_ACCOUNTS_URL=https://accounts.zoho.com
ZOHO_API_BASE=https://www.zohoapis.com
ZOHO_MODULE=Sheds

GOOGLE_MAPS_API_KEY=

OPENWEATHER_API_KEY=

CLUSTER_MODE= #village/taluk/distance

PILOT_MODE=true
PILOT_VILLAGES=KISHANNAGAR,SADISOPUR

WATI_BASE_URL=
WATI_API_TOKEN=
WATI_TEMPLATE_NAME=weather_advisory_v1

DATABASE_URL=

TEST_DATABASE_URL=
```

---

## Installation

```bash
pip install -r requirements.txt
```

---

## Running Tests

```bash
pytest
```

Coverage:

```bash
pytest --cov=app --cov-fail-under=80 --cov-report=term
```
