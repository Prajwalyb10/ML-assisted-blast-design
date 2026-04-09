# Blast Design Dashboard

ML-backed blast design and visualization app built as a small monorepo:

- `frontend/`: React + Vite app for the UI
- `backend/`: FastAPI + scikit-learn API for prediction and layout generation

## Local Run

Backend:

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

Frontend:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Backend:

```bash
CORS_ORIGINS=http://127.0.0.1:3000
```

Example env files are included at:

- [`frontend/.env.example`](/D:/BadAss%20Project%20??/ml-assist-blast%20design/frontend/.env.example)
- [`backend/.env.example`](/D:/BadAss%20Project%20??/ml-assist-blast%20design/backend/.env.example)

## Deploy Online

Use different project roots for each platform:

### Render Backend

Repo: [ML-assisted-blast-design](https://github.com/Prajwalyb10/ML-assisted-blast-design)

Settings:

- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Environment Variable: `PYTHON_VERSION=3.11.9`

After Vercel gives you a frontend URL, add:

```bash
CORS_ORIGINS=https://your-frontend.vercel.app
```

This repo also includes [`render.yaml`](/D:/BadAss%20Project%20??/ml-assist-blast%20design/render.yaml) with `rootDir: backend`.

### Vercel Frontend

Repo: [ML-assisted-blast-design](https://github.com/Prajwalyb10/ML-assisted-blast-design)

Settings:

- Root Directory: `frontend`
- Framework Preset: `Vite`

Environment variable:

```bash
VITE_API_BASE_URL=https://your-backend.onrender.com
```

The frontend config file is at [`frontend/vercel.json`](/D:/BadAss%20Project%20??/ml-assist-blast%20design/frontend/vercel.json).

## API Endpoints

- `GET /health`
- `GET /reference-data`
- `GET /patterns`
- `POST /generate-pattern`

## Notes

- The ML models train from [`backend/blast_ml_dataset.csv`](/D:/BadAss%20Project%20??/ml-assist-blast%20design/backend/blast_ml_dataset.csv) at app startup.
- The frontend loads defaults from the backend `/reference-data` endpoint.
- The app returns predicted burden, spacing, explosive loading, flyrock estimate, selected pattern, and plotted hole coordinates in one response.
