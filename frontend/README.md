# Agentic RAG — React UI

A modern React frontend for the Enterprise Agentic RAG API — the project's UI.

**Stack:** Vite 8 · React 19 · TypeScript · Tailwind CSS v4 · react-markdown
**Bundle:** ~125 kB gzipped

## Features

- **Streaming-feel answers** — token reveal animation with a live caret.
- **Agent reasoning timeline** — the LangGraph plan steps, collapsible per answer.
- **Retrieved-context panel** — each chunk expandable, with the `CONTENT:`
  prefix stripped automatically.
- **Self-RAG telemetry** — context-verified / low-relevance chip, grader
  confidence %, rewrite count, and end-to-end latency per answer.
- **Guardrail-aware** — errors from the backend (blocked requests, offline API)
  surface in a dismissible banner, never a dead screen.
- **Live backend status** — health polled every 15s; status dot in the sidebar.
- **Conversation memory** — session id persisted to `localStorage` and sent as
  `thread_id`, so the agent remembers context across refreshes.
- **Markdown + GFM** — tables, lists, code blocks with syntax styling.
- **Keyboard-first composer** — Enter to send, Shift+Enter for a newline, Stop
  button to cancel an in-flight request.
- Responsive layout with a mobile drawer.

## Running

Start the API first:

```bash
# from the project root
uvicorn app.main:app --reload --port 8000
```

Then the UI:

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
```

The dev server proxies `/api/*` → `http://localhost:8000/*`, so there is no
CORS friction in development. (The backend also enables CORS for 5173/3000 —
adjust `CORS_ORIGINS` in `.env` if you use another origin.)

## Production build

```bash
cd frontend
# point the app at your deployed API
echo "VITE_API_BASE_URL=https://your-backend.example.com" > .env.local
npm run build         # outputs to frontend/dist
```

Serve `frontend/dist` with any static host (Vercel, Netlify, Nginx, S3). If you
prefer a single deployment, mount `frontend/dist` as `StaticFiles` on the
FastAPI app.

## API contract

The UI targets `POST /query`:

```json
{ "q": "…", "thread_id": "…" }
```

and renders `answer`, `thought_process`, `sources`, plus the optional
`retrieval_grade` / `retrieval_confidence` / `retrieval_retries` telemetry.
