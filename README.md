# MLH Fellowship LLM Project

## Stack

- **Backend:** Python, FastAPI, SQLAlchemy, SQLite. Talks to an LLM
  (Google Gemini by default) through a small pluggable provider interface.
- **Frontend:** JavaScript, React, Vite (Node-based tooling).
- **Communication:** Frontend calls the backend REST API (Vite dev
  server proxies `/api` to `http://localhost:8000`).

## Project layout

```
backend/
  app/
    main.py          # FastAPI app + router registration
    config.py         # env-based settings
    database.py        # SQLAlchemy engine/session
    models.py          # Conversation, Message
    schemas.py          # Pydantic request/response models
    llm/                # pluggable LLM provider interface
    routes/             # health + conversation/chat endpoints
  tests/
frontend/
  src/
    App.jsx             # barebones single-conversation chat UI
    components/          # MessageList, MessageInput
    api/client.js         # fetch wrapper for backend API
scripts/dev.sh            # runs backend + frontend together
```

## Continuous integration

Pull requests and pushes to `main` run two CI jobs: backend Ruff linting, Black
format checking, and pytest; frontend ESLint checks and a production build.
CI uses Python 3.12 and Node.js 22 and does not require an LLM API key.

Run the same checks locally from the repository root:

```bash
backend/.venv/bin/python -m pip install -r backend/requirements-lint.txt
backend/.venv/bin/python -m ruff check backend
backend/.venv/bin/python -m black --check backend
(cd backend && DATABASE_URL=sqlite:// .venv/bin/python -m pytest -q)
npm --prefix frontend ci
npm --prefix frontend run lint
npm --prefix frontend run build
```

To fix Python formatting, run `backend/.venv/bin/python -m black backend`.
Ruff and ESLint detect common code errors; these checks do not add a separate
static type checker to this Python/JavaScript project.

## Getting started

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then add your GEMINI_API_KEY (free tier: https://aistudio.google.com/apikey)
uvicorn app.main:app --reload --port 8000
```

After the backend has initialized the local database, load sample conversations
for frontend development without making an LLM request:

```bash
cd backend
python -m scripts.seed
```

The command is idempotent, so rerunning it does not duplicate the sample data.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Then visit `http://localhost:5173`.

### Or run both at once

```bash
./scripts/dev.sh
```

## What's here vs. what's not

This scaffold gives you: a working conversation + message data model, one
endpoint to send a message and get an LLM reply, and a minimal React UI
that can hold a single conversation. It deliberately has **no**
authentication, streaming, pagination, multi-conversation UI, migrations,
or Docker setup -- those are the fellowship issues.

## Contributing

Pick an issue from `ISSUES.md`, open a branch, and submit a PR. Issues
are labeled by area (`backend`, `frontend`, `database`, `llm`, `infra`)
and difficulty (`good first issue`, `intermediate`, `advanced`).
