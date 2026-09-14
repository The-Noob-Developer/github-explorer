# GitHub Explorer — Backend

FastAPI service that turns a natural-language query into live GitHub repository
results. It is the only part of the system that talks to Groq and to GitHub —
the frontend only ever calls this service over HTTP.

## Local development

\`\`\`bash
cd backend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then fill in GROQ_API_KEY and GITHUB_TOKEN
uvicorn app.main:app --reload
\`\`\`

The API is served at `http://localhost:8000`. Interactive docs are available at
`http://localhost:8000/docs`.

## Running tests

\`\`\`bash
pytest
\`\`\`

## Environment variables

See `.env.example` for the full list. At minimum you need:

- `GROQ_API_KEY` — a Groq API key (https://console.groq.com)
- `GROQ_MODEL` — a Groq chat model id, e.g. `llama-3.3-70b-versatile`
- `GITHUB_TOKEN` — a GitHub personal access token with public repo read access
- `ALLOWED_ORIGIN` — the frontend origin allowed by CORS, e.g. `http://localhost:3000`

`REDIS_URL` is optional — when unset, an in-memory TTL cache is used instead.

## Endpoints

- `POST /api/search` — the main search pipeline (see the root project README for the full contract)
- `GET /api/facts` — a random GitHub fact
- `GET /api/health` — liveness/readiness probe

## Deployment

This service is fully independent of the frontend's build/deploy process. Deploy it
to any Python-friendly host (Render, Railway, Fly.io, Cloud Run) by running:

\`\`\`bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
\`\`\`

Set all variables from `.env.example` in that host's environment configuration, with
`ALLOWED_ORIGIN` pointed at your deployed frontend's URL.
