# 🧪 LIMS — Laboratory Information Management System

A full-stack web application for managing laboratory samples, test results, and predictions.

---

## 📁 Folder Structure

```
lims/
├── backend/                     # Flask REST API
│   ├── app.py                   # App entry point + route registration
│   ├── requirements.txt         # Python dependencies
│   ├── .env.example             # Environment variable template
│   ├── models/
│   │   ├── database.py          # MongoDB connection + index setup
│   │   └── schemas.py           # Document schemas + factory functions
│   ├── routes/
│   │   ├── auth.py              # /api/auth — register, login, me
│   │   ├── samples.py           # /api/samples — CRUD + stats
│   │   └── tests.py             # /api/tests — CRUD + AI predict
│   ├── middleware/
│   │   └── auth.py              # JWT decorators (token_required, role_required)
│   └── utils/
│       ├── ai_predictor.py      # Heuristic AI prediction engine
│       └── helpers.py           # Serialisation, pagination, response helpers
│
├── frontend/                    # TypeScript + HTML/CSS frontend
│   ├── index.html               # Single-page application (self-contained)
│   └── src/
│       ├── types/index.ts       # TypeScript type definitions
│       └── services/api.ts      # Typed API client layer
│
└── docs/
    └── README.md                # This file
```

---

## 🔌 API Endpoints

### Auth  `/api/auth`
| Method | Endpoint         | Description              | Auth |
|--------|-----------------|--------------------------|------|
| POST   | `/register`     | Register new user        | No   |
| POST   | `/login`        | Login, get JWT token     | No   |
| GET    | `/me`           | Current user profile     | Yes  |
| GET    | `/users`        | List all users           | Yes  |

### Samples  `/api/samples`
| Method | Endpoint              | Description                       | Auth |
|--------|-----------------------|-----------------------------------|------|
| GET    | `/`                   | List samples (page, filter, search) | Yes |
| POST   | `/`                   | Create sample                     | Yes  |
| GET    | `/<sample_id>`        | Get sample + its test results     | Yes  |
| PUT    | `/<sample_id>`        | Update sample                     | Yes  |
| DELETE | `/<sample_id>`        | Delete sample + tests             | Yes  |
| GET    | `/stats/summary`      | Dashboard stats                   | Yes  |

### Tests  `/api/tests`
| Method | Endpoint          | Description                        | Auth |
|--------|-------------------|------------------------------------|------|
| GET    | `/`               | List tests (page, filter)          | Yes  |
| POST   | `/`               | Create test (auto-runs AI predict) | Yes  |
| GET    | `/<test_id>`      | Get single test                    | Yes  |
| PUT    | `/<test_id>`      | Update test (auto-completes sample)| Yes  |
| DELETE | `/<test_id>`      | Delete test                        | Yes  |
| POST   | `/predict`        | Run standalone AI prediction       | Yes  |

### System
| Method | Endpoint       | Description               |
|--------|---------------|---------------------------|
| GET    | `/api/health` | Health check + DB status  |

---

## 🗃️ Database Schema

### `users` collection
```json
{
  "_id": "ObjectId",
  "username": "string (unique)",
  "email": "string (unique)",
  "password_hash": "string (bcrypt)",
  "role": "admin | technician | viewer",
  "created_at": "datetime",
  "last_login": "datetime | null"
}
```

### `samples` collection
```json
{
  "_id": "ObjectId",
  "sample_id": "string (e.g. LIMS-2024-0001, unique)",
  "name": "string",
  "type": "blood | urine | tissue | swab | serum | other",
  "patient_id": "string",
  "patient_name": "string",
  "collected_by": "string",
  "collection_date": "datetime",
  "status": "received | processing | completed | rejected",
  "priority": "routine | urgent | stat",
  "notes": "string",
  "metadata": {
    "temperature": "float (°C)",
    "volume_ml": "float",
    "container_type": "string"
  },
  "created_at": "datetime",
  "updated_at": "datetime",
  "created_by": "string (username)"
}
```

### `test_results` collection
```json
{
  "_id": "ObjectId",
  "sample_id": "string (→ samples.sample_id)",
  "test_name": "string",
  "test_code": "string (e.g. CBC, GLU)",
  "category": "hematology | biochemistry | microbiology | immunology | urinalysis",
  "status": "pending | in_progress | completed | failed",
  "result_value": "float | null",
  "result_unit": "string",
  "reference_range": { "min": "float", "max": "float" },
  "is_abnormal": "boolean",
  "ai_prediction": {
    "predicted_value": "float",
    "confidence": "float (0–1)",
    "risk_level": "low | medium | high",
    "reference_range": { "min": "float", "max": "float", "unit": "string" },
    "model_version": "string",
    "predicted_at": "datetime"
  },
  "performed_by": "string",
  "performed_at": "datetime",
  "verified_by": "string | null",
  "verified_at": "datetime | null",
  "notes": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

---

## 🚀 Running Locally

### Prerequisites
- Python 3.10+
- MongoDB 6.0+ (running on `localhost:27017`)
- A modern browser (Chrome, Firefox, Edge)

> **No Node.js required** — the frontend is plain HTML/CSS/JS.

---

### 1. Start MongoDB

```bash
# macOS (Homebrew)
brew services start mongodb-community

# Ubuntu/Debian
sudo systemctl start mongod

# Windows
net start MongoDB
```

---

### 2. Set up Backend

```bash
cd lims/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate       # macOS/Linux
# venv\Scripts\activate        # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env if needed (default works out-of-the-box with local MongoDB)

# Start the Flask API
python app.py
```

API will be available at: **http://localhost:5000**

Test it:
```bash
curl http://localhost:5000/api/health
```

---

### 3. Open Frontend

Simply open `lims/frontend/index.html` in your browser:

```bash
# macOS
open lims/frontend/index.html

# Linux
xdg-open lims/frontend/index.html

# Or serve with Python
cd lims/frontend
python -m http.server 3000
# then visit http://localhost:3000
```

---

### 4. Create Your First Account

1. Open the app in browser
2. Click **Register**
3. Fill in username, email, password
4. Select role: `admin` for full access
5. You're in!

---

## 🤖 AI Prediction

The built-in predictor (`utils/ai_predictor.py`) uses a heuristic engine:

- **Inputs**: sample type, priority, collection temperature, volume
- **Outputs**: predicted value, confidence %, risk level (low/medium/high)
- **Supported test codes**: CBC, HGB, PLT, GLU, CREA, ALT, AST, LFT
- **Model**: deterministic heuristic (reproducible per sample_id seed)
- Every new test result automatically receives an AI prediction

To upgrade to ML: replace the `predict()` function with a trained `sklearn` pipeline loaded from disk.

---

## 🔐 Security Notes

- Passwords are hashed with **bcrypt** (salt rounds: default ~12)
- API routes are protected with **JWT Bearer tokens** (24-hour expiry)
- Change `JWT_SECRET_KEY` in `.env` before deploying to production
- CORS is open (`*`) for development — restrict to your frontend domain in production

---

## 📦 Tech Stack

| Layer     | Technology              |
|-----------|------------------------|
| Backend   | Python 3.10 + Flask 3  |
| Database  | MongoDB 6 + PyMongo 4  |
| Auth      | JWT (flask-jwt-extended)|
| Frontend  | HTML5 + CSS3 + vanilla TS-style JS |
| AI        | Custom heuristic engine (scikit-learn ready) |
