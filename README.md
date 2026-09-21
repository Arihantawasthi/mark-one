# Mark One — Backend

> [!TIP]
> This is the backend engine for the Mark One platform.
> You can find the corresponding frontend user interface architecture in the [mark-one-client](https://github.com) repository.

A FastAPI + Celery backend powering the Mark One newsletter analysis platform. It orchestrates scraping, issue analysis, aggregation, and real-time progress streaming.

---

## 🚀 Overview

The backend coordinates the end-to-end analysis pipeline:

* Search newsletters via Google CSE
* Scrape Beehiiv / Substack issues
* Run LLM-based issue analytics
* Aggregate issue-level insights
* Stream progress updates via WebSocket
* Handle manual issue submissions
* Persist everything to PostgreSQL

---

## 🧱 Tech Stack

* **FastAPI** (HTTP + WebSocket endpoints)
* **Celery** (distributed task pipeline)
* **Redis** (broker + progress pub/sub)
* **PostgreSQL** (analysis + issue storage)
* **Playwright** (scraping)

---

## 🔌 Core Features

### **1. Start Analysis**

* `/start-query-analysis` — search terms → search → scrape → analyze
* `/start-links-analysis` — direct links → scrape → analyze

Creates an `analysis_run` entry + triggers Celery pipeline.

### **2. Manual Issue Analysis**

* `/start-manual-issues-analysis`

Allows users to submit individual issue URLs. A Celery task:

* Scrapes provided issue links
* Performs LLM-based analytics
* Streams progress to WebSocket
* Saves results to DB

### **3. Real-Time Progress Streaming**

* `/ws/status/{analysis_run_id}`

Powered by Redis pub/sub. Each pipeline stage emits messages like:

```
{
  "title": "Scraping newsletters",
  "detail": "Fetching pages…",
  "progress": 40
}
```

Frontend listens and renders progress live.

### **4. Fetching Analysis Results**

* `/analysis-status/{id}` → overall pipeline status
* `/analysis/{id}` → issue-level analytics + aggregated metrics
* `/analysis/process-status/{id}` → full historical progress log
* `/analyses/list` → all saved analyses

### **5. Test Route**

* `/ws/test-status` — mocks progress stream for frontend testing

---

## 📁 Project Structure

```
app/
  api/           # Routers & WebSocket handlers
  services/      # Scraper, newsletter, search, pub/sub
  tasks/         # Celery pipelines (scrape → analyze → aggregate)
  db/            # Queries, connectors, schema helpers
  core/          # Settings, logging, celery config
```

---

## ▶️ Development

Install dependencies:

```
pip install -r requirements.txt
```

Start API server:

```
uvicorn app.main:app --reload
```

Start Celery worker:

```
celery -A app.core.celery_app worker -l info
```

(Optional) Start beat scheduler:

```
celery -A app.core.celery_app beat
```

Requires **PostgreSQL**, **Redis**, and **Playwright** properly installed.

---

## 🌐 Environment Variables

```
DATABASE_URL=
REDIS_URL=
GOOGLE_API_KEY=
GOOGLE_SEARCH_CX=
PLAYWRIGHT_DRIVER_PATH=
```

---

## 🧠 Notes

* Progress statuses stored as JSONB
* Celery publishes status updates to Redis
* WebSocket relays updates to frontend
* Manual issue pipeline runs independently of initial analysis

---

## 📜 License

Proprietary — internal use only.

