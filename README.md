# Blast Design Dashboard

ML-backed blast design and visualization app built with FastAPI, scikit-learn, React, and Vite.

## Local Run

Backend:

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Frontend:

```bash
npm install
npm run dev
```

Optional local env file:

```bash
copy .env.example .env
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

For production, set `VITE_API_BASE_URL` to your public backend URL and set `CORS_ORIGINS` to your public frontend URL.

## Deploy Online

Recommended setup:

1. Deploy the FastAPI backend to Render.
2. Deploy the Vite frontend to Vercel.
3. Point the frontend env var to the backend URL.
4. Point the backend CORS env var to the frontend URL.

### Render Backend

This repo includes [`render.yaml`](/D:/BadAss%20Project%20??/ml-assist-blast%20design/render.yaml).

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

Set this environment variable in Render after you know your frontend URL:

```bash
CORS_ORIGINS=https://your-frontend.vercel.app
```

### Vercel Frontend

This repo includes [`vercel.json`](/D:/BadAss%20Project%20??/ml-assist-blast%20design/vercel.json).

Set this environment variable in Vercel:

```bash
VITE_API_BASE_URL=https://your-backend.onrender.com
```

Then redeploy the frontend.

## API Endpoints

- `GET /health`
- `GET /reference-data`
- `GET /patterns`
- `POST /generate-pattern`

## Notes

- The ML models are trained from [`blast_ml_dataset.csv`](/D:/BadAss%20Project%20??/ml-assist-blast%20design/blast_ml_dataset.csv) at app startup.
- The frontend uses the backend's `/reference-data` endpoint to prefill model-driven defaults.
- The app returns predicted geometry, explosive loading, flyrock estimate, selected pattern, and plotted hole coordinates in one response.
