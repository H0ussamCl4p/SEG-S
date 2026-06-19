# IIoT Predictive Maintenance Platform

An end‑to‑end Industrial IoT platform that ingests live machine telemetry, scores each
reading for anomalies, predicts **Remaining Useful Life (RUL)**, and lets technicians ask a
**RAG chatbot** grounded in the equipment manuals — all behind a secured microservice backend.

---

## 1. What it does

- **Real‑time monitoring** — vibration, temperature and humidity per machine, streamed live to the dashboard.
- **Anomaly detection** — every reading is scored and classified `NORMAL` / `WARNING` / `ANOMALY`.
- **Predictive maintenance** — estimates a health score, time‑to‑failure (RUL) and a maintenance schedule.
- **Decision support** — Pareto analysis of failure causes and an Eisenhower‑matrix task prioritizer.
- **AI assistant** — a multilingual RAG chatbot that answers maintenance questions strictly from uploaded manuals.

---

## 2. Architecture & Tech Stack

The system is a set of containerized microservices (Docker; Azure Container Apps in production).

| Layer | Technology | Role |
|-------|-----------|------|
| **Frontend** | Next.js / React / TypeScript, Tailwind, shadcn/ui, SWR | Dashboard, charts, prediction & chat UI (polls the API) |
| **AI Engine** | FastAPI (Python 3.10), runs **two** processes under supervisord | REST API (`api.py`) **+** MQTT consumer (`main.py`) |
| **Auth Service** | FastAPI + SQLAlchemy + PostgreSQL | JWT login, bcrypt hashing, RBAC (admin / operator) |
| **Ingestion** | `simulator` (paho‑mqtt) → **Mosquitto** MQTT broker | Publishes/transports machine telemetry |
| **Time‑series DB** | **InfluxDB 1.8** | Stores telemetry (`machine_telemetry`, `esp_motor`, `signal_features`) |
| **ML / Anomaly** | scikit‑learn (Isolation Forest, Random Forest), NumPy | Scoring, RUL, failure prediction |
| **Chatbot (RAG)** | LangChain + **ChromaDB** + `sentence-transformers` (multilingual MiniLM) + OpenAI‑compatible LLM (DeepSeek / Groq Llama‑3.3‑70B, or local Ollama) | Manual‑grounded Q&A |
| **Edge (optional)** | ESP32 / PLC over MQTT or HTTP | Real hardware telemetry source |

```
                                   ┌────────────────────────────────────────────┐
   Sensors / ESP32 / PLC           │                AI ENGINE                     │
   (or simulator)                  │  ┌───────────────┐      ┌─────────────────┐  │
        │  vibration, temp, hum    │  │  MQTT consumer │      │   FastAPI API   │  │
        ▼                          │  │   (main.py)    │      │    (api.py)     │  │
  ┌───────────┐   MQTT             │  │  • score each  │      │ /api/live,      │  │
  │ Mosquitto │ ───topic────────►  │  │    reading     │      │ /history,/rul,  │  │
  │  broker   │ factory/plc/data   │  │  • write       │ ───► │ /stats,/alerts, │  │
  └───────────┘                    │  │    InfluxDB    │      │ /predict,/chat  │  │
        ▲ HTTP (ESP/signal)        │  └───────┬────────┘      └────────┬────────┘  │
        │                          │          ▼                        ▲           │
        │                          │     ┌──────────┐                  │ reads     │
        └──────────────────────────┼────►│ InfluxDB │ ◄────────────────┘           │
                                   │     └──────────┘                              │
                                   └───────────────────────────┬──────────────────┘
                                                                │ HTTPS (SWR polling)
                                                                ▼
                                                        ┌───────────────┐
                                                        │ Next.js UI     │
                                                        │ charts · RUL · │
                                                        │ chatbot        │
                                                        └───────────────┘
```

---

## 3. Data pipeline — from input to prediction to chatbot

**A. Ingestion (input).** Each machine emits a JSON reading `{machine_id, vibration, temperature, humidity}`.
- **MQTT path (main telemetry):** publisher → Mosquitto topic `factory/plc/data` → the AI‑engine **consumer** (`main.py`) subscribes, **scores the reading**, and writes a point to InfluxDB measurement `machine_telemetry` (fields `vibration, temperature, humidity, ai_score`; tags `machine_id, equipment_name, status`).
- **HTTP path (edge devices):** ESP32 motor and vibration‑signal features are POSTed to `/api/esp/ingest` and `/api/signal/ingest` and stored in `esp_motor` / `signal_features`.

**B. Scoring (at ingest time).** The consumer assigns an `ai_score ∈ [-1, 1]`:
- If a trained **Isolation Forest** model is loaded → use the model.
- Otherwise → a **heuristic** score derived from vibration & temperature (see §4). This guarantees the dashboard, alerts and RUL always have meaningful signal even without a trained model.

**C. Serving (output / prediction).** The FastAPI layer reads InfluxDB and exposes:
- `/api/live`, `/api/history`, `/api/machines` — current & historical readings + status.
- `/api/stats`, `/api/alerts`, `/api/pareto/anomalies` — fleet KPIs, alerts, root‑cause Pareto.
- `/api/rul` — Remaining Useful Life & predicted failure date.
- `/predict` — combined real‑time anomaly + future‑failure assessment.

**D. Visualization.** The Next.js dashboard polls these endpoints with **SWR** (1–10 s intervals) and renders metrics, trend charts, machine status, RUL and the prediction panel.

**E. Chatbot (RAG).** Independently, a technician asks a question →
1. the question is embedded with a **multilingual** sentence‑transformer,
2. **ChromaDB** retrieves the top‑k (=3) most similar chunks from the ingested PDF manuals,
3. the LLM answers **strictly from that manual context**, in the same language as the question.

---

## 4. AI & algorithms

**Anomaly detection — Isolation Forest (primary) + heuristic (fallback).**
- *Isolation Forest* (unsupervised) isolates outliers; it returns `-1` (anomaly) / `1` (normal) plus a continuous `score_samples`, normalized to `[0, 1]`.
- *Heuristic fallback* (used when no model file is present): compute a normalized `impact = 0.6·vibₙ + 0.4·tempₙ` against expected maxima (auto‑calibrated from the last ~2 h of InfluxDB data), then `score = 1 − 2·impact ∈ [-1, 1]`. Vibration is weighted higher because it is the leading failure indicator.

**Status classification (one convention everywhere).** Using the normalized score `n = (score+1)/2`:
`ANOMALY` if `n < 0.1`, `WARNING` if `n < 0.3`, else `NORMAL`. The same thresholds drive `/api/live`, `/api/history`, `/api/stats` and `/api/alerts`, so all views agree.

**Health score — weighted rule model (0–100).** Combines absolute vibration thresholds, temperature thresholds and the AI score into an interpretable health percentage and a status band (EXCELLENT → CRITICAL).

**Remaining Useful Life (RUL) — degradation + stress model.**
1. Build a per‑bucket health series from stored telemetry (6 h buckets over 7 days).
2. Measure the **downward** health trend by linear regression (improving health does not count as wear).
3. `RUL_days = (current_health − 20%) / wear_rate`, where
   `wear_rate = max(measured downward trend, stress_baseline)` and
   `stress_baseline = 0.2 + 4·stress²`, `stress = 0.6·vibₙ + 0.4·tempₙ`.
   This means a hot, heavily‑vibrating machine ages faster, so machines differentiate correctly, and a genuine downward trend collapses RUL toward `CRITICAL`. A predicted failure date is derived from `RUL_days`.

**Future failure prediction — Random Forest Regressor (`/predict`).** When a trained MTTF model is present it predicts Mean‑Time‑To‑Failure and surfaces feature importances; otherwise the same health/wear model provides a consistent heuristic forecast. Overall risk = `max(current anomaly risk, future failure risk)`.

**Decision support.**
- *Pareto analysis* ranks anomaly causes / maintenance task types by frequency (80‑20 focus).
- *Eisenhower matrix* classifies maintenance tasks by urgency × importance for prioritization.

**RAG chatbot.** Multilingual MiniLM embeddings + ChromaDB similarity search (k=3) + an LLM constrained to answer only from the retrieved manual context, in a fixed maintenance‑report format.

---

## 5. AI Health Score — definition

The per‑reading `score` expresses confidence that the machine is healthy.
- **Range:** `0.0`–`1.0` (higher = healthier) for visualization consistency.
- **Source:** Isolation Forest model when available, else the auto‑calibrated heuristic above.
- **Status mapping:** `ANOMALY < 0.1 ≤ WARNING < 0.3 ≤ NORMAL`.
- The separate `health` object adds an aggregated 0–100 score and a days‑until‑maintenance estimate for planning.

---

## 6. Security

**Authentication & access control**
- JWT issued by a dedicated **auth‑service**; passwords hashed with **bcrypt**, users in PostgreSQL.
- **RBAC**: `admin` and `operator` roles. Sensitive mutating endpoints (model **training**, **dataset upload**) require an **admin** JWT.

**Injection defenses**
- **SQL (PostgreSQL):** all access goes through the **SQLAlchemy ORM with bound parameters** — no string‑built SQL, so the auth path is not SQL‑injectable.
- **Time‑series (InfluxQL):** every user‑supplied identifier (`machine_id`, `equipmentId`) is validated against a strict allow‑list (`^[A-Za-z0-9_.-]{1,64}$`) and rejected with `400` **before** it is used in a query, closing InfluxQL injection.

**LLM / prompt‑injection hardening**
- The chatbot treats both the retrieved manual context **and** the user's question as **untrusted data**: it ignores embedded instructions (e.g. "ignore previous instructions"), refuses to change its role/format, and never reveals its system prompt. The user question is delimited in its own turn.
- The chatbot has **no tools/actions** — its blast radius is limited to text answers.

**Upload & platform hardening**
- Manual upload accepts **PDF only** and **sanitizes the filename** (basename) to prevent path traversal.
- **TLS/HTTPS** termination with security headers (`X-Frame-Options`, `X-Content-Type-Options`, `X-XSS-Protection`) at the reverse proxy / ingress.
- **Network isolation:** InfluxDB, PostgreSQL and Mosquitto are **internal‑only** (no public ports); only the API, auth and frontend are exposed over HTTPS.


---

## 7. Backend API (selected)

| Endpoint | Description |
|----------|-------------|
| `GET /api/live?machine_id=` | Latest reading + AI assessment: `vibration, temperature, humidity, score, status, timestamp, health{…}` |
| `GET /api/history?machine_id=&limit=` | Recent readings for charts: `[{timestamp, vibration, temperature, humidity, score, status}]` |
| `GET /api/machines` | All machines with latest status |
| `GET /api/stats` | Fleet KPIs: averages, uptime %, anomalies/warnings (last 24 h) |
| `GET /api/alerts` | Recent anomalies & warnings with reasons |
| `GET /api/rul?machine_id=` | Remaining Useful Life, degradation rate, predicted failure date, recommendation |
| `GET /api/pareto/anomalies` · `GET /api/pareto/maintenance` | Root‑cause / task Pareto analysis |
| `POST /predict` | Combined real‑time anomaly + future‑failure assessment |
| `POST /api/chat` · `POST /api/chat/stream` | RAG chatbot (full / streaming) |
| `POST /api/chat/upload` | Upload a PDF manual into the knowledge base |
| `POST /train` · `POST /upload-dataset` · `POST /api/models/train` | **Admin only** — model training & datasets |

---

## 8. Environment variables

| Variable | Purpose |
|----------|---------|
| `INFLUX_HOST`, `INFLUX_PORT`, `INFLUX_DB` | InfluxDB connection |
| `MQTT_BROKER`, `MQTT_PORT` | MQTT broker for telemetry |
| `EXPECTED_MAX_VIBRATION`, `EXPECTED_MAX_TEMPERATURE` | Maxima for the heuristic score / RUL stress model |
| `JWT_SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES` | Auth / token signing |
| `OLLAMA_BASE_URL` / `LLM_API_BASE`, `LLM_API_KEY`, `LLM_MODEL` | Chatbot LLM (local Ollama or OpenAI‑compatible cloud) |
