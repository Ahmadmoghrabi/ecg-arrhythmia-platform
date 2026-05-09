# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ECG Arrhythmia Classification Platform — portfolio project targeting Apple Health SWE/QA/Security roles.

**Stack:** Python ML · Java Spring Boot · JWT auth · MongoDB · AWS (S3, Lambda, DynamoDB, API Gateway) · GitHub Actions CI/CD

Three runnable components:
1. **ML service** (`ml/`) — Python: data pipeline, 5-class AAMI Random Forest, Flask inference API (port 5001)
2. **Backend** (`backend/`) — Java Spring Boot: REST API, JWT auth, MongoDB, proxies ML to Flask (port 8080)
3. **AWS** (`aws/`) — Lambda inference trigger, S3 ECG storage, DynamoDB results (Day 12+, not yet implemented)

## Commands

### Setup
```bash
pip install -r requirements.txt
```

### ML — train & run

Train + evaluate (prints report, no save):
```bash
python3 ml/src/classifier.py
```

Train + save model to `ml/models/ecg_classifier.pkl`:
```bash
cd ml/src && python3 save_model.py
```

Run inference on a single MIT-BIH record (default: `100`):
```bash
python3 ml/src/predict.py [record_id]
```

Start Flask inference API (port 5001):
```bash
python3 ml/api/app.py
```

### Backend (requires Java 21 + Maven)
```bash
cd backend && mvn spring-boot:run   # port 8080
```

Both servers must be running for the full system to work.

### Tests
```bash
python3 -m pytest tests/unit/ -v              # all unit tests
python3 -m pytest tests/unit/test_api.py -v  # API only (no model file needed)
```

## API Endpoints (Spring Boot — port 8080)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/v1/health` | No | Check both servers are up |
| POST | `/api/v1/auth/register` | No | Create account, returns JWT |
| POST | `/api/v1/auth/login` | No | Login, returns JWT |
| POST | `/api/v1/ecg/upload` | JWT | Register a MIT-BIH record ID |
| POST | `/api/v1/ecg/{id}/classify` | JWT | Run ML classification, save to MongoDB |
| GET | `/api/v1/ecg/{id}/results` | JWT | Fetch classification results |
| GET | `/api/v1/ecg` | JWT | List all records for current user |

All protected routes require `Authorization: Bearer <token>` header.

## Architecture

### Classification: 5-class AAMI EC57 standard

| Label | Class | MIT-BIH symbols |
|-------|-------|-----------------|
| 0 | N — Normal | N, L, R, e, j |
| 1 | S — Supraventricular ectopic | A, a, J, S |
| 2 | V — Ventricular ectopic | V, E |
| 3 | F — Fusion | F |
| 4 | Q — Unclassifiable/Paced | /, f, Q, ? |

### ML pipeline (`ml/src/`)

`classifier.py` is the canonical source of truth for `extract_features()`, `AAMI_MAP`, and `LABEL_NAMES`.

1. Load 48 MIT-BIH records from `ml/data/mitdb/` via `wfdb` (lead MLII, channel 0)
2. Extract 360-sample window per beat (180 before + 180 after at 360 Hz)
3. Compute 7 statistical features: mean, std, max, min, range, median, signal energy
4. Train `RandomForestClassifier(n_estimators=100, stratify=y)` with 80/20 split

### Flask inference API (`ml/api/app.py`)

Loads `.pkl` on startup. Key endpoint: `POST /classify/record` accepts `{"record_path": "..."}` and returns all beats + summary. Runs on port **5001**.

### Spring Boot backend (`backend/`)

- **Auth:** BCrypt password hashing, HS384 JWT tokens (24hr expiry), Spring Security filter chain
- **MongoDB:** 3 collections — `users`, `ecg_records`, `classification_results`
- **EcgService:** orchestrates upload → classify (calls Flask) → save results flow
- JWT secret configured via `JWT_SECRET` env var (has dev default — override in production)
- Flask URL configured via `classifier.url` in `application.properties` (default: `http://localhost:5001`)

### Model file

`ml/models/ecg_classifier.pkl` is git-ignored (>100MB). Regenerate with `cd ml/src && python3 save_model.py`.

### Data

`ml/data/mitdb/` is git-ignored. 48 records in WFDB format (`.dat`, `.hea`, `.atr`). Must be present locally to train.
