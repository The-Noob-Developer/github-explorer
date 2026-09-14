# GitHub Explorer — Frontend

Next.js (App Router) + TypeScript + Tailwind + shadcn/ui frontend for GitHub Explorer.
It never talks to Groq or GitHub directly — every search goes through the independent
FastAPI backend in `../backend`, reached via `NEXT_PUBLIC_API_URL`.

## Local development

\`\`\`bash
npm install
cp .env.example .env.local   # set NEXT_PUBLIC_API_URL to your running backend, e.g. http://localhost:8000
npm run dev
\`\`\`

Make sure the backend (see `backend/README.md`) is running first — this app has no
mock data and no fallback; every search result comes from a live call to the backend.

## Environment variables

- `NEXT_PUBLIC_API_URL` — base URL of the deployed/running FastAPI backend. Read only
  in `lib/api-client.ts`, never hardcoded.

## Project structure

- `app/page.tsx` — hosts the search experience
- `app/search/` — the search feature: search box, progress steps, results, clarification,
  interpretation panel, empty/error states, fun facts
- `lib/api-client.ts` — the single typed client for calling the backend
- `types/api.ts` — TypeScript types mirroring the backend's response contract

## Deployment

Deploy to Vercel and set `NEXT_PUBLIC_API_URL` in the project's environment variables
to the backend's public URL. The backend is deployed completely independently (Render,
Railway, Fly.io, Cloud Run, etc.) — this app never runs it.
