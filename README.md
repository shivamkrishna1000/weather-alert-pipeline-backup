# 🌦️ Weather Advisory Pipeline for Greenhouse Farmers

A scalable, production-ready pipeline that:
- Syncs greenhouse data from Zoho CRM
- Geocodes missing locations
- Clusters greenhouses geographically
- Fetches weather forecasts
- Generates rule-based advisories
- Sends WhatsApp alerts via WATI

---

## 🚀 System Overview

This system runs in two independent pipelines:

### 1. Weekly Pipeline
- Sync greenhouse data from Zoho
- Clean and filter records
- Geocode missing locations

### 2. Daily Pipeline
- Cluster greenhouses
- Fetch weather data
- Generate advisories
- Send WhatsApp messages

---

## 🧠 Architecture

Zoho CRM → Sync Pipeline → Database
                        ↓
                Geocode Pipeline
                        ↓
                 Clean Dataset
                        ↓
                Clustering Layer
                        ↓
                Weather Pipeline
                        ↓
                Advisory Engine
                        ↓
               Delivery Pipeline (WATI)

---

## 📦 Project Structure

app/
│
├── core/                  # Core logic (rules, transformations)
├── external/              # External API clients
├── repositories/          # DB queries
├── services/              # Business logic
├── pipelines/             # End-to-end workflows
├── database.py            # DB connection & schema
├── config.py              # Environment config
├── constants.py           # Static mappings
├── main.py                # Entry point

---

## ⚙️ Key Features

### ✅ Data Sync from Zoho
- Uses COQL with pagination
- Supports incremental sync using `Modified_Time`

### ✅ Data Cleaning & Filtering
- Filters based on allowed statuses
- Extracts structured fields like phone, location, etc.

### ✅ Geocoding Pipeline
- Builds address from village/taluk/district
- Uses Google Maps API
- Caches results to reduce API cost
- Retry logic with max attempts

### ✅ Clustering System
Supports 3 modes:
- `taluk`
- `village`
- `distance` (DBSCAN clustering)

### ✅ Weather Processing
- Fetches forecast from WeatherAPI
- Extracts key features like:
  - temperature
  - rainfall
  - humidity
  - wind

### ✅ Advisory Engine
- Rule-based system (deterministic)
- Category priority: rain → wind → humidity → temperature
- Conflict handling (e.g., rain overrides irrigation advice)

### ✅ Delivery System
- Groups advisories by farmer
- Sends via WhatsApp (WATI API)
- Debug mode support (no sending, only logging)

---

## 🗄️ Database Schema

Tables created automatically:

- `greenhouses`
- `greenhouses_missing_location`
- `geocode_cache`
- `weather_cache`
- `weather_data`
- `advisory_logs`
- `sync_metadata`

Created via:
create_tables(connection)

---

## 🔁 Pipelines

### Weekly Pipeline

python -m app.main weekly

Runs:
1. Sync pipeline
2. Geocode pipeline

---

### Daily Pipeline

python -m app.main daily

Runs:
1. Weather pipeline
2. Advisory generation
3. Delivery pipeline

---

## 🧾 Environment Setup

Copy `.env.example` → `.env` and fill in the required values.

---

## 🧪 Debug Mode (Important)

If:
DEBUG_MODE=true

Then:
- Messages are NOT sent
- Only printed in terminal
- Delivery status is NOT updated

This prevents accidental spamming.

---

## 🔄 Idempotency & Safety

This system avoids duplicate work:

### ✔ Sync
- Uses `last_sync` timestamp

### ✔ Weather
- Uses cache (same-day freshness check)

### ✔ Advisory
- Prevents duplicate advisory per greenhouse per day

### ✔ Delivery
- Only sends `pending` advisories

---

## ⚡ Parallel Processing

- Geocoding → ThreadPool (20 workers)
- Weather → ThreadPool (10 workers)

Each worker uses a separate DB connection (important for scaling)

---

## 📊 Advisory Rules (Example)

{
  "rain": "Avoid irrigation",
  "wind": "Avoid spraying",
  "humidity": "Monitor fungal risk",
  "temperature": "Ensure irrigation"
}

---

## 🧱 Design Decisions

### 1. Cluster-Based Weather Fetching
- Reduces API calls massively
- Slight trade-off in accuracy

### 2. Rule-Based Advisory System
- Deterministic and explainable
- Easy to modify

### 3. Cache-First Strategy
- Reduces API cost significantly

### 4. Separate Pipelines
- Weekly = heavy operations
- Daily = time-sensitive operations

---

## 🧑‍💻 Running Locally

pip install -r requirements.txt

python -m app.main weekly
python -m app.main daily

---
