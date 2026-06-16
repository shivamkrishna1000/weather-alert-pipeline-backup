# 🌦️ Kheyti Weather Advisory Pipeline

A production weather-advisory system for greenhouse farmers. It synchronizes
greenhouse records from Zoho CRM, geocodes their locations, clusters nearby
greenhouses to save on API calls, fetches localized forecasts from OpenWeather,
generates farmer-friendly advisories through a YAML-driven rule engine, appends
official **IMD (India Meteorological Department)** district warnings, and delivers
the result to farmers over WhatsApp via WATI.

---

## Table of Contents

- [Features](#features)
- [System Architecture](#system-architecture)
- [How It Works](#how-it-works)
- [Project Structure](#project-structure)
- [Technology Stack](#technology-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Running the Pipelines](#running-the-pipelines)
- [Database Schema](#database-schema)
- [Advisory Engine & Rules](#advisory-engine--rules)
- [IMD Official Warnings](#imd-official-warnings)
- [WhatsApp Template](#whatsapp-template)
- [Clustering Modes](#clustering-modes)
- [Operational Modes](#operational-modes)
- [Testing & Quality](#testing--quality)
- [Documentation](#documentation)
- [Repository Notes](#repository-notes)

---

## Features

- Zoho CRM greenhouse synchronization (incremental, by `Modified_Time`)
- Address geocoding via Google Maps, with result caching
- Geographic clustering of greenhouses to minimize weather API calls
- OpenWeather **One Call API 3.0** forecast integration
- YAML-driven advisory rule engine (configurable, no code changes required)
- Official IMD district warnings (Red/Orange) appended to advisories
- Structured advisory storage in PostgreSQL `JSONB`
- WhatsApp delivery through WATI templates
- Advisory deduplication and weather caching
- Parallel processing for weather and geocoding
- Pilot mode (village-scoped rollout) and debug mode (generate without sending)

---

## System Architecture

The pipeline is staged: each stage has a single responsibility and communicates
through PostgreSQL, which keeps the modules loosely coupled.

```text
Zoho CRM
    │  Sync Pipeline
    ▼
Greenhouse Database (PostgreSQL)
    │  Geocode Pipeline
    ▼
Greenhouse records (with coordinates)
    │  Cluster generation (daily, in-memory)
    ▼
Weather clusters
    │  Weather Pipeline ──► OpenWeather One Call API
    ▼
Normalized weather payload
    │  Advisory Engine (YAML rules)
    │  + IMD warnings appended ◄── IMD District Warning API
    ▼
advisory_logs (JSONB)
    │  Delivery Pipeline
    ▼
WATI WhatsApp API ──► Farmer
```

> Clusters are not persisted in a dedicated table; they are computed in memory at
> the start of each daily run from the current greenhouse records.

---

## How It Works

The system runs as two independent flows.

### Weekly pipeline — master data

```bash
python -m app.main weekly
```

1. Fetch greenhouse records from Zoho CRM
2. Validate records and detect missing coordinates
3. Geocode missing locations (parallelized) and cache results
4. Update synchronization metadata

Database tables are created automatically on first run (`create_tables()` is
invoked by the sync pipeline), so no manual migration step is required.

### Daily pipeline — advisories

```bash
python -m app.main daily
```

1. Build greenhouse clusters
2. Fetch forecasts (respecting weather-cache freshness)
3. Generate advisories and append IMD warnings; store in `advisory_logs`
4. Deliver WhatsApp notifications for advisories with `pending` status

---

## Project Structure

```text
app/
├── config/
│   ├── advisory_rules.yaml        # Advisory rule definitions (operator-editable)
│   └── weather_schema.yaml        # Weather metric schema for rule evaluation
│
├── core/
│   ├── greenhouse.py              # Split records by presence of coordinates
│   └── geocode.py                 # Build normalized address strings
│
├── external/
│   ├── zoho_client.py             # Zoho CRM integration
│   ├── maps_client.py             # Google Maps geocoding
│   ├── weather_client.py          # OpenWeather One Call API
│   └── imd_client.py              # IMD API (JWT auth + district warnings)
│
├── services/
│   ├── greenhouse_service.py      # Greenhouse validation / transformation
│   ├── geocode_service.py         # Geocoding workflow and retry rules
│   ├── cluster_service.py         # Cluster-key generation + distance clustering
│   ├── weather_service.py         # Weather normalization and summarization
│   ├── advisory_service.py        # Rule evaluation, formatting, IMD append
│   ├── delivery_service.py        # Advisory grouping / section assembly
│   ├── wati_service.py            # WhatsApp delivery via WATI
│   └── imd_warning_service.py     # IMD district resolution + warning decoding
│
├── repositories/
│   ├── greenhouse_repo.py         # Greenhouse + geocode-cache operations
│   ├── weather_repo.py            # Cluster, weather-cache, weather-history
│   └── advisory_repo.py           # Advisory log operations
│
├── pipelines/
│   ├── sync_pipeline.py           # Greenhouse synchronization
│   ├── geocode_pipeline.py        # Geocoding (parallelized)
│   ├── weather_pipeline.py        # Clustering, weather, advisory generation
│   └── delivery_pipeline.py       # Advisory delivery
│
├── database.py                    # Connection + schema creation
├── config.py                      # Environment configuration access
├── constants.py                   # Constants, Zoho field maps, IMD code maps
├── district_mapping.csv           # Greenhouse district → IMD Obj_id / district
└── main.py                        # CLI entry point (weekly | daily)
```

---

## Technology Stack

| Component             | Technology                                         |
|-----------------------|----------------------------------------------------|
| Language              | Python 3.12 (3.10+ for modern union typing)        |
| Database              | PostgreSQL 15 (`JSONB` for advisory storage)       |
| CRM integration       | Zoho CRM                                           |
| Geocoding             | Google Maps Geocoding API                          |
| Weather provider      | OpenWeather One Call API 3.0                       |
| Official warnings     | India Meteorological Department (IMD) API (JWT)    |
| Messaging             | WATI (WhatsApp Business API)                        |
| Clustering            | scikit-learn (DBSCAN) + NumPy (distance mode)      |
| HTTP client           | `requests`                                         |
| Configuration         | Environment variables via `python-dotenv`          |
| Rules / schema        | YAML                                               |
| Concurrency           | `ThreadPoolExecutor` (weather + geocoding)         |
| Lint / format         | `ruff`                                             |
| Docstring coverage    | `interrogate` (≥ 80%, via pre-commit)              |
| Tests                 | `pytest`, `pytest-cov` (coverage ≥ 80%)            |

---

## Prerequisites

- Python 3.12 (recommended; 3.10+ required)
- PostgreSQL 15 (or a hosted equivalent)
- API credentials for Zoho CRM, Google Maps, OpenWeather, WATI, and IMD

---

## Installation

```bash
# 1. Clone
git clone https://github.com/Kheyti-India/weather-alert-pipeline
cd weather-alert-pipeline-backup

# 2. (Recommended) create a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env             # then fill in the values

# 5. (Optional) install git hooks for lint/format/docstring checks
pre-commit install
```

---

## Environment Variables

Copy `.env.example` to `.env` and provide values. Database tables are created
automatically on first run.

| Variable                | Required | Description                                                        |
|-------------------------|----------|--------------------------------------------------------------------|
| `DATABASE_URL`          | Yes      | PostgreSQL connection string                                       |
| `TEST_DATABASE_URL`     | Tests    | PostgreSQL connection string used by the test suite                |
| `ZOHO_CLIENT_ID`        | Yes      | Zoho OAuth client ID                                               |
| `ZOHO_CLIENT_SECRET`    | Yes      | Zoho OAuth client secret                                           |
| `ZOHO_REFRESH_TOKEN`    | Yes      | Zoho OAuth refresh token                                           |
| `ZOHO_ACCOUNTS_URL`     | Yes      | Zoho accounts base (e.g. `https://accounts.zoho.com`)              |
| `ZOHO_API_BASE`         | Yes      | Zoho API base (e.g. `https://www.zohoapis.com`)                    |
| `ZOHO_MODULE`           | Yes      | Zoho module holding greenhouse records (e.g. `Sheds`)              |
| `GOOGLE_MAPS_API_KEY`   | Yes      | Google Maps Geocoding API key                                      |
| `OPENWEATHER_API_KEY`   | Yes      | OpenWeather One Call API key                                       |
| `IMD_API_KEY`           | Yes      | IMD API key (`X-API-KEY` header)                                   |
| `IMD_EMAIL`             | Yes      | IMD account email (JWT auth)                                       |
| `IMD_PASSWORD`          | Yes      | IMD account password (JWT auth)                                    |
| `CLUSTER_MODE`          | No       | `village` (default) · `taluk` · `distance`                         |
| `PILOT_MODE`            | No       | Restrict processing to selected villages (`true`/`false`)          |
| `PILOT_VILLAGES`        | No       | Comma-separated village names (matched case-insensitively)         |
| `DEBUG_MODE`            | No       | Generate advisories without sending WhatsApp (`true`/`false`)      |
| `WATI_BASE_URL`         | Yes      | WATI API base URL                                                  |
| `WATI_API_TOKEN`        | Yes      | WATI API token                                                     |
| `WATI_TEMPLATE_NAME`    | Yes      | WATI WhatsApp template name (e.g. `weather_advisory_v1`)           |
| `RND_WATI_API_URL`      | No       | R&D/testing WATI endpoint (validation module)                      |
| `RND_WATI_API_KEY`      | No       | R&D/testing WATI key                                               |
| `RND_WATI_TEMPLATE_NAME`| No       | R&D/testing WATI template                                          |

---

## Running the Pipelines

```bash
# Weekly: sync greenhouses from Zoho + geocode missing locations
python -m app.main weekly

# Daily: fetch weather, generate advisories (+ IMD), deliver via WhatsApp
python -m app.main daily
```

Invalid or missing modes print a usage hint. The daily run will reconnect and
retry delivery once if the database connection goes stale mid-run.

---

## Database Schema

PostgreSQL is the central persistence layer and the channel between pipelines.

| Table                          | Purpose                                  |
|--------------------------------|------------------------------------------|
| `greenhouses`                  | Master greenhouse records                |
| `greenhouses_missing_location` | Records requiring geocoding              |
| `geocode_cache`                | Address → coordinate cache               |
| `weather_cache`                | Latest weather cache (freshness-checked) |
| `weather_data`                 | Historical weather records               |
| `advisory_logs`                | Advisory generation + delivery history   |
| `sync_metadata`                | Synchronization tracking                 |

### `advisory_logs`

| Column            | Type        |
|-------------------|-------------|
| `greenhouse_id`   | `TEXT`      |
| `greenhouse_name` | `TEXT`      |
| `farmer_name`     | `TEXT`      |
| `phone`           | `TEXT`      |
| `cluster_key`     | `TEXT`      |
| `advisory`        | `JSONB`     |
| `advisory_date`   | `DATE`      |
| `delivery_status` | `TEXT`      |
| `sent_at`         | `TIMESTAMP` |

The `advisory` column stores the structured advisory (including any appended IMD
text). Example:

```json
{
  "current":  "Strong winds are occurring currently. Avoid pesticide spraying.",
  "today":    "Heavy rain expected today. Ensure proper drainage and avoid irrigation. Expected rain window: 02:30 PM to 05:30 PM. 🔴 IMD Red Alert: Heavy Rain expected in your district.",
  "tomorrow": "Heavy rainfall is expected tomorrow. Plan irrigation and field activities accordingly. Expected rain window: 02:30 AM to 08:30 AM.",
  "day3":     "Rainfall is expected later this week. Plan field operations accordingly."
}
```

---

## Advisory Engine & Rules

Advisories are produced by a deterministic, YAML-driven rule engine. Rules live in
`app/config/advisory_rules.yaml` and the available weather metrics in
`app/config/weather_schema.yaml`. Both are **operator-editable** — an agronomist
can adjust conditions, thresholds, priorities, suppression, and message text
without any code change.

Rules are evaluated across four forecast horizons — current (`CUR`), today (`TD`),
tomorrow (`TM`), and day 3 (`D3`) — in descending priority order, with
configurable suppression to avoid contradictory or redundant messages.

> Full rule semantics (fields, operators, priority, suppression, placeholders, and
> the current rule inventory) are documented in the **Weather Advisory Rules
> Document** — see [Documentation](#documentation).

---

## IMD Official Warnings

After rule evaluation, the engine appends official IMD district warnings. This is
independent of the YAML rules and does not affect rule logic, priority, or
suppression.

- The greenhouse district is resolved to an IMD district identifier via
  `app/district_mapping.csv`.
- The IMD API is authenticated with a cached JWT (auto-refreshed before expiry);
  the warning dataset is cached in memory for 30 minutes per run.
- Each record carries a warning code and color for the next three days. Codes are
  decoded into readable descriptions (heavy/very-heavy/extremely-heavy rain,
  thunderstorm & lightning, hailstorm, dust storm, strong surface winds, heat
  wave, cold wave, fog, frost, and more).

| IMD day field          | Advisory section |
|------------------------|------------------|
| `Day_1` / `Day1_Color` | `today`          |
| `Day_2` / `Day2_Color` | `tomorrow`       |
| `Day_3` / `Day3_Color` | `day3`           |

| Color code | Severity | Appended?            |
|------------|----------|----------------------|
| 1          | Red      | Yes                  |
| 2          | Orange   | Yes                  |
| 3          | Yellow   | No (can be enabled)  |
| 4          | Green    | No                   |

Only **Red** and **Orange** warnings are surfaced to farmers. Example fragment:

```text
🔴 IMD Red Alert: Heavy Rain, Thunderstorm & Lightning expected in your district.
```

---

## WhatsApp Template

The structured advisory maps onto the WATI template variables:

| Variable | Value               |
|----------|---------------------|
| `{{1}}`  | Farmer name         |
| `{{2}}`  | Greenhouse name     |
| `{{3}}`  | Current conditions  |
| `{{4}}`  | Today's advisory    |
| `{{5}}`  | Tomorrow's advisory |
| `{{6}}`  | Day 3 outlook       |

---

## Clustering Modes

Clustering reduces weather API calls by grouping greenhouses that can share a
forecast. Set with `CLUSTER_MODE`:

| Mode       | Grouping                                                   |
|------------|------------------------------------------------------------|
| `village`  | District + taluk + village (default)                       |
| `taluk`    | District + taluk                                           |
| `distance` | Geographic proximity via DBSCAN (haversine, ~3 km radius)  |

---

## Operational Modes

- **Production** — processes all eligible greenhouses and delivers messages.
- **Pilot** (`PILOT_MODE=true`, `PILOT_VILLAGES=...`) — restricts processing to
  selected villages for controlled rollouts.
- **Debug** (`DEBUG_MODE=true`) — generates advisories and prints them, but does
  not send WhatsApp messages (treated as not sent).

---

## Testing & Quality

```bash
# Run the test suite
pytest

# Run with coverage (CI gate is 80%)
pytest --cov=app --cov-fail-under=80 --cov-report=term

# Run all pre-commit checks (ruff lint + format, docstring coverage)
pre-commit run --all-files
```

Continuous integration (`.github/workflows/ci.yml`) runs on every push to `main`
and on pull requests. It spins up a PostgreSQL 15 service, installs dependencies
on Python 3.12, runs the pre-commit checks, and then runs the tests with the 80%
coverage gate.

---

## Documentation

- **Weather Advisory Pipeline — Technical Documentation** (architecture,
  integrations, configuration, runbook, IMD details)
- **Weather Advisory Rules Document** (rule framework, schema, priority,
  suppression, placeholders, rule inventory)
- **Walkthrough:** [Loom video](https://www.loom.com/share/b8446c208ca446e5b1a13b13d31a293b)

---

## Repository Notes

- `rnd_weather_validation/` is a separate R&D module used to validate forecast
  accuracy against on-site sensors. It is excluded from coverage and is not part
  of the production pipeline.
- This is a backup mirror of the original repository.
