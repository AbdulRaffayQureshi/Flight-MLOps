<div align="center">

<img src="assets/radar-banner.svg" alt="Global Flight Disruption Predictor" width="100%"/>

<br/>

![Python](https://img.shields.io/badge/Python-3.11-6FFFB0?style=for-the-badge&logo=python&logoColor=05080d)
![FastAPI](https://img.shields.io/badge/FastAPI-05080d?style=for-the-badge&logo=fastapi&logoColor=6FFFB0)
![DuckDB](https://img.shields.io/badge/DuckDB-05080d?style=for-the-badge&logo=duckdb&logoColor=FFB020)
![XGBoost](https://img.shields.io/badge/XGBoost-05080d?style=for-the-badge&logo=xgboost&logoColor=6FFFB0)
![MLflow](https://img.shields.io/badge/MLflow-05080d?style=for-the-badge&logo=mlflow&logoColor=4FD8EA)
![Docker](https://img.shields.io/badge/Docker-05080d?style=for-the-badge&logo=docker&logoColor=4FD8EA)
![Three.js](https://img.shields.io/badge/Three.js-05080d?style=for-the-badge&logo=three.js&logoColor=FFB020)

**A self-sustaining MLOps system that watches the sky over JFK and predicts disruption before it happens.**

No paid infrastructure. No cloud bill. Just live air-traffic state vectors, live weather, and a model that keeps learning.

</div>

---

## What this actually is

Most ML portfolio projects stop at a notebook and an accuracy score. This one doesn't stop — it *runs*. Every few hours, without anyone touching it, the system pulls live aircraft state vectors from OpenSky and live weather from Open-Meteo, folds them into a local warehouse, retrains, and serves a fresh disruption-risk prediction through a REST API and an ATC-style radar dashboard.

It's built to answer one question honestly: **can this pipeline still be trusted a week from now, with zero human babysitting, and zero infrastructure cost?**

## Live Radar Dashboard

The inference endpoint isn't just JSON in a terminal — it's rendered as a real-time radar scope, echoing the instrument it's modeling after.

<div align="center">
<img src="assets/dashboard-demo.gif" alt="Radar dashboard demo" width="85%"/>
<br/>
<sub>Sweeping 3D radar (Three.js) · live telemetry console · risk-coded target blip</sub>
</div>

> Replace `assets/dashboard-demo.gif` with a real screen recording of your dashboard once it's deployed — a 5–8s loop of the sweep + a prediction updating is enough.

## Architecture

The pipeline runs on a strict, self-triggering cycle — no cron server, no external scheduler, no manual retraining.

```mermaid
graph TD
    subgraph INGEST["① Automated Ingestion — every 4h"]
        A[FastAPI Background Scheduler] -->|bounding box query| B[OpenSky API<br/>live aircraft state vectors]
        A -->|lat/lon query| C[Open-Meteo API<br/>wind + precipitation]
    end

    subgraph STORE["② Storage & Training"]
        B --> D[(DuckDB<br/>local OLAP store)]
        C --> D
        D -->|feature extraction| E[XGBoost Classifier<br/>+ SMOTE for class balance]
        E -->|params, metrics, SHAP| F[MLflow Tracking Server]
    end

    subgraph SERVE["③ Serving"]
        E -->|loads latest run| G[FastAPI /api/predict]
        D -->|latest snapshot| H[FastAPI /api/latest-data]
        G --> I[Radar Dashboard]
        H --> I
    end

    classDef ingest fill:#0a141c,stroke:#4FD8EA,stroke-width:1.5px,color:#E8F4EF;
    classDef store fill:#0a141c,stroke:#FFB020,stroke-width:1.5px,color:#E8F4EF;
    classDef serve fill:#0a141c,stroke:#6FFFB0,stroke-width:1.5px,color:#E8F4EF;

    class A,B,C ingest;
    class D,E,F store;
    class G,H,I serve;
```

## Why each piece is there

| Decision | Reasoning |
|---|---|
| **DuckDB over Postgres** | Time-series telemetry at this scale doesn't need a server process — an embedded OLAP file gives fast columnar queries with zero ops overhead. |
| **SMOTE before training** | Severe-delay events are rare. Without rebalancing, XGBoost just learns to predict "nothing's wrong" and looks accurate while being useless. |
| **MLflow, self-hosted** | Every retrain is logged — hyperparameters, metrics, SHAP feature-importance artifacts — so a model regression is traceable instead of a mystery. |
| **Background scheduler, not a queue** | At a 4-hour cadence with a single ingestion job, a threading scheduler inside the FastAPI process is simpler and cheaper than standing up Celery/Redis for the same guarantee. |
| **Docker Compose** | The API and MLflow server are two processes that need to agree on a network and a volume — Compose makes "works on my machine" also mean "works on any machine." |

## Tech stack

<table>
<tr>
<td valign="top" width="33%">

**Ingestion & Serving**
- FastAPI
- Uvicorn
- Python threading scheduler
- OpenSky Network API
- Open-Meteo API

</td>
<td valign="top" width="33%">

**Data & ML**
- DuckDB
- XGBoost
- SMOTE (imbalanced-learn)
- SHAP
- MLflow

</td>
<td valign="top" width="33%">

**Frontend & Ops**
- Three.js (radar scope)
- Tailwind CSS (compiled, no runtime JIT)
- Docker / Docker Compose

</td>
</tr>
</table>

## Project structure

```
flight-mlops/
├── app/
│   ├── ingest/            # OpenSky + Open-Meteo fetchers, run on schedule
│   ├── db/
│   │   ├── seed.py        # historical backfill for first run
│   │   └── schema.sql
│   ├── ml/
│   │   ├── train.py       # XGBoost + SMOTE, logs to MLflow
│   │   └── predict.py     # loads latest MLflow run for inference
│   ├── static/
│   │   ├── index.html     # radar dashboard
│   │   ├── script.js
│   │   └── styles.css     # compiled Tailwind — no CDN, no eval()
│   └── main.py             # FastAPI app + scheduler bootstrap
├── assets/
│   ├── radar-banner.svg
│   └── dashboard-demo.gif
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## Quickstart

The whole stack is containerized — one command boots the API, the scheduler, and MLflow together.

```bash
git clone <your-repo-url>
cd flight-mlops
docker compose up --build -d
```

**First run only** — seed historical context so the model has something to train on:

```bash
docker exec -it flight_mlops_api python app/db/seed.py
docker exec -it flight_mlops_api python app/ml/train.py
```

**Interfaces:**

| Service | URL | Purpose |
|---|---|---|
| Radar Dashboard | `http://localhost:8000` | Live telemetry + risk prediction |
| MLflow UI | `http://localhost:5000` | Experiment history, metrics, SHAP artifacts |

## API

| Endpoint | Method | Returns |
|---|---|---|
| `/api/latest-data` | `GET` | Most recent ingested traffic + weather snapshot |
| `/api/predict` | `GET` | Current disruption risk level + probability |

# Image

<img width="1346" height="754" alt="image" src="https://github.com/user-attachments/assets/4bf674f1-37b5-404c-8b9f-3e20ebe442aa" />


## Roadmap

- [ ] Swap the threading scheduler for APScheduler with persistent job state
- [ ] Add a `/api/history` endpoint to chart risk trend over the last 24h
- [ ] Extend beyond KJFK to a small multi-airport panel
- [ ] CI job that fails the build if retrain metrics regress past a threshold

---

<div align="center">

Built by **Abdul Raffay Qureshi** · Bioinformatics × ML × Systems

[![LinkedIn](https://img.shields.io/badge/LinkedIn-05080d?style=for-the-badge&logo=linkedin&logoColor=4FD8EA)](https://linkedin.com/in/your-profile)
[![GitHub](https://img.shields.io/badge/GitHub-05080d?style=for-the-badge&logo=github&logoColor=E8F4EF)](https://github.com/AbdulRaffayQureshi)

</div>
