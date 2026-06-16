# ECG Arrhythmia Classification Platform

[![CI](https://github.com/Ahmadmoghrabi/ecg-arrhythmia-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/Ahmadmoghrabi/ecg-arrhythmia-platform/actions/workflows/ci.yml)

A full-stack platform that classifies heartbeats from ECG recordings into the **5-class AAMI standard** (Normal, Supraventricular, Ventricular, Fusion, Unclassifiable). Built as a portfolio project targeting health-tech SWE, QA, and security roles.

**Live demo flow:** register → login → upload MIT-BIH record → classify → view results (via Postman).

## Architecture

```
Client (Postman)
       │
       ▼
Spring Boot API :8080  ──►  MongoDB (users, records, results)
       │
       ▼
Flask ML API :5001  ──►  Random Forest model + MIT-BIH data
```

| Component | Tech | Port |
|-----------|------|------|
| ML service | Python, scikit-learn, Flask | 5001 |
| Backend API | Java 21, Spring Boot, JWT, MongoDB | 8080 |
| AWS (planned) | S3, Lambda, DynamoDB | — |

## Prerequisites

- **Python 3.10+**
- **Java 21** and **Maven**
- **MongoDB** running locally (`mongodb://localhost:27017`)
- **MIT-BIH dataset** in `ml/data/mitdb/` (48 WFDB records — not stored in git)
- **Trained model** at `ml/models/ecg_classifier.pkl` (not stored in git — see below)

## Setup

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Download MIT-BIH data

Place 48 MIT-BIH Arrhythmia Database records (`.dat`, `.hea`, `.atr`) in `ml/data/mitdb/`.  
Obtain from [PhysioNet MIT-BIH Arrhythmia Database](https://physionet.org/content/mitdb/1.0.0/).

### 3. Train the model (if missing)

```bash
cd ml/src && python3 save_model.py
```

This saves `ml/models/ecg_classifier.pkl` (~115 MB, git-ignored).

### 4. Configure backend paths (optional)

By default, the backend looks for ECG data at `../ml/data/mitdb` relative to the `backend/` directory. Override with an environment variable:

```bash
export MITDB_PATH=/absolute/path/to/ml/data/mitdb
```

## Run locally

Start both servers — the backend depends on the ML service.

**Terminal 1 — ML API**

```bash
cd ~/Documents/ecg-platform   # or your clone path
python3 ml/api/app.py
```

**Terminal 2 — Backend**

```bash
cd backend && mvn spring-boot:run
```

**Terminal 3 — Health check**

```bash
curl http://localhost:8080/api/v1/health
```

Expected response when both services are up:

```json
{"status":"ok","classifier":"up"}
```

## API endpoints

All routes are under `/api/v1`. Protected routes require `Authorization: Bearer <token>`.

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/health` | No | Check backend + ML service status |
| POST | `/auth/register` | No | Create account, returns JWT |
| POST | `/auth/login` | No | Login, returns JWT |
| POST | `/ecg/upload` | JWT | Register a MIT-BIH record ID |
| POST | `/ecg/{id}/classify` | JWT | Run ML classification, save to MongoDB |
| GET | `/ecg/{id}/results` | JWT | Fetch classification results |
| GET | `/ecg` | JWT | List all records for current user |

### Example: register and classify

```bash
# Register
curl -s -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@ecgplatform.com","password":"securepass123"}'

# Use the returned token
export TOKEN="<token from response>"

# Upload record 100
curl -s -X POST http://localhost:8080/api/v1/ecg/upload \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"recordId":"100"}'

# Classify (use id from upload response)
curl -s -X POST http://localhost:8080/api/v1/ecg/<id>/classify \
  -H "Authorization: Bearer $TOKEN"
```

## Postman

Import the collection from `postman/collections/ECG-Platform/`. Run requests in order:

1. **Health** → Health Check  
2. **Auth** → Register → Login  
3. **ECG** → Upload ECG → Classify → Get Results → List ECG  

Collection variables (`apiUrl`, `token`, `ecgRecordId`) are set automatically by test scripts.

## ML pipeline

`ml/src/classifier.py` is the source of truth for feature extraction and AAMI label mapping.

1. Load MIT-BIH records via `wfdb` (lead MLII)
2. Extract a 360-sample window per beat (180 before + 180 after at 360 Hz)
3. Compute 7 statistical features per beat
4. Classify with `RandomForestClassifier` (100 trees, 80/20 split)

### AAMI 5-class labels

| Label | Class | MIT-BIH symbols |
|-------|-------|-----------------|
| N | Normal | N, L, R, e, j |
| S | Supraventricular ectopic | A, a, J, S |
| V | Ventricular ectopic | V, E |
| F | Fusion | F |
| Q | Unclassifiable/Paced | /, f, Q, ? |

## Tests

```bash
# Python unit tests (no model file needed for API tests)
python3 -m pytest tests/unit/ -v

# Backend integration tests (requires MongoDB)
cd backend && mvn test
```

## Project structure

```
ecg-platform/
├── ml/                 # Python ML pipeline + Flask inference API
├── backend/            # Java Spring Boot REST API
├── aws/                # Cloud deployment (Day 12+, in progress)
├── tests/unit/         # Python unit tests
├── postman/            # API collections for manual testing
└── requirements.txt
```

## Roadmap

- [x] 5-class AAMI Random Forest classifier
- [x] Flask inference API
- [x] Spring Boot REST API + MongoDB
- [x] JWT authentication
- [x] Postman demo collection
- [x] GitHub Actions CI
- [ ] AWS deployment (S3, Lambda, DynamoDB, API Gateway)
- [ ] Backend integration test expansion

## License

MIT — see [LICENSE](LICENSE).
