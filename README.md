# Restaurant Action Center

A Flask dashboard that analyzes 100 days of restaurant inventory data, flags operational risks, and generates AI-powered recommendations for the most important alerts.

## Overview

This project was built to surface actionable inventory insights for a restaurant owner or operations manager. It combines:

- deterministic alert rules over historical inventory data
- a Flask dashboard for visualizing the top alerts
- AI-generated recommendations for each alert
- a repository-based data access layer designed to make future database changes easier

## Features

- Reorder discipline detection
- Waste cost estimation
- Stockout frequency analysis
- Summary KPI cards on the dashboard
- REST API endpoints for alerts and stats
- On-demand AI suggestions for each flagged alert
- Configurable database backend abstraction for future migration beyond SQLite

## Alert Rules

The app currently evaluates three rule-based alert types over the inventory dataset:

1. Reorder Discipline Issue
   Triggered when an item is at or below its reorder level on at least 2% of tracked days.

2. High Total Waste Cost
   Triggered when estimated waste value exceeds 500 over the analysis period.

3. Stockout Frequency Risk
   Triggered when stock coverage falls below supplier lead time on at least 5% of tracked days.

## Tech Stack

- Python
- Flask
- Pandas
- SQLite
- Google Generative AI
- Bootstrap 5

## Project Structure

```text
restaurant_action_center/
├── app.py
├── config.py
├── requirements.txt
├── README.md
├── ai/
│   └── enrichment.py
├── data/
│   └── restaurant_inventory_100days.csv
├── database/
│   ├── client.py
│   ├── init_db.py
│   └── repository.py
├── services/
│   └── alert_service.py
└── templates/
    └── dashboard.html
```

## How It Works

1. The CSV inventory dataset is loaded and cleaned.
2. Cleaned data is stored in SQLite for local development.
3. Repository methods run the alert queries and return normalized Python dictionaries.
4. Flask routes render the dashboard and expose JSON APIs.
5. Users can request AI suggestions for each alert from the dashboard UI.

## Setup

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd restaurant_action_center
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_api_key_here
PORT=3000
DATABASE_BACKEND=sqlite
```

Environment variables:

- `GEMINI_API_KEY`: API key used for AI recommendations
- `PORT`: Flask app port
- `DATABASE_BACKEND`: currently supports `sqlite`; the code is structured to support adding `bigquery` later

### 5. Run the app

```bash
python3 app.py
```

Open the app at:

```text
http://localhost:3000
```

If `PORT` is not set, the app defaults to `5000`.

## API Endpoints

- `GET /`
- `GET /dashboard`
- `GET /api/alerts`
- `GET /api/stats`
- `POST /api/enrich-alert`

### Example `POST /api/enrich-alert`

```json
{
  "item": "Tomatoes",
  "category": "Produce",
  "supplier": "Fresh Farms",
  "total_days": 100,
  "days_low": 12,
  "pct_days_low": 12.0,
  "avg_stock": 8.5,
  "alert_type": "Reorder Discipline Issue"
}
```


