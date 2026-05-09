# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ECG Arrhythmia Classification Platform — portfolio project targeting Apple Health SWE/QA/Security roles.

**Stack:** Python ML · Java Spring Boot · JWT auth · MongoDB · AWS (S3, Lambda, DynamoDB, API Gateway) · GitHub Actions CI/CD

Three runnable components:
1. **ML service** (`ml/`) — Python: data pipeline, 5-class AAMI Random Forest, Flask inference API
2. **Backend** (`backend/`) — Java Spring Boot: REST gateway, JWT auth, MongoDB, AWS integration
3. **AWS** (`aws/`) — Lambda inference trigger, S3 ECG storage, DynamoDB results (not yet implemented)

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
cd backend && mvn spring-boot:run   # port 8080, proxies to ml/api on :5001
```

### Tests
```bash
python3 -m pytest tests/unit/ -v              # all unit tests
python3 -m pytest tests/unit/test_api.py -v  # API only (no model file needed)
python3 -m pytest tests/ -v                   # full suite
```

## Architecture

### Classification: 5-class AAMI EC57 standard

| Label | Class | MIT-BIH symbols |
|-------|-------|-----------------|
| 0 | N — Normal | N, L, R, e, j |
| 1 | S — Supraventricular ectopic | A, a, J, S |
| 2 | V — Ventricular ectopic | V, E |
| 3 | F — Fusion | F |
| 4 | Q — Unclassifiable/Paced | /, f, Q, ? |

Symbols not in `AAMI_MAP` (rhythm annotations like `+`, `~`) are skipped during data loading.

### ML pipeline (`ml/src/`)

`classifier.py` is the canonical source of truth for `extract_features()`, `AAMI_MAP`, and `LABEL_NAMES` — `save_model.py` and `predict.py` import from it.

1. Load 48 MIT-BIH records from `ml/data/mitdb/` via `wfdb` (lead MLII, channel 0)
2. Extract 360-sample window per beat (180 before + 180 after at 360 Hz)
3. Compute 7 statistical features: mean, std, max, min, range, median, signal energy
4. Train `RandomForestClassifier(n_estimators=100, stratify=y)` with 80/20 split

### Flask inference API (`ml/api/app.py`)

Loads `.pkl` on startup. Accepts `{"signal": [360 floats]}` or `{"features": [7 floats]}`.
Returns prediction name (N/S/V/F/Q), description, label (0–4), confidence, and all 5 class probabilities.
Runs on port **5001**.

### Spring Boot gateway (`backend/`)

Proxies to Flask via `ClassifierService` (Spring `RestClient`). Exposes `POST /api/v1/classify` and `GET /api/v1/health`. Flask URL configured in `application.properties` (`classifier.url`, default `http://localhost:5001`).

### Model file

`ml/models/ecg_classifier.pkl` is git-ignored (>100MB). Regenerate with `cd ml/src && python3 save_model.py` after any change to feature extraction or training logic.

### Data

`ml/data/mitdb/` is git-ignored. 48 records in WFDB format (`.dat`, `.hea`, `.atr`). Must be present locally to train.
