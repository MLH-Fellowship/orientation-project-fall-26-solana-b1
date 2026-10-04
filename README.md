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

## Getting started

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then add your GEMINI_API_KEY (free tier: https://aistudio.google.com/apikey)
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

To apply a system instruction to every LLM request, set `SYSTEM_PROMPT` in
`backend/.env`:

```dotenv
SYSTEM_PROMPT="Answer as a concise Solana development mentor."
```

Leave the setting empty to keep the provider's default behavior.

After the backend has initialized the local database, load sample conversations
for frontend development without making an LLM request:

```bash
cd backend
python -m scripts.seed
```

The command is idempotent, so rerunning it does not duplicate the sample data.

Database schema changes are managed with Alembic. Run migration commands from
the `backend` directory:

```bash
# Apply every pending migration
alembic upgrade head

# Create a migration after changing the SQLAlchemy models
alembic revision --autogenerate -m "describe the schema change"

# Revert the latest migration
alembic downgrade -1
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Then visit `http://localhost:5173`.

### Or run both at once

One-time setup from the repository root (Python 3.10–3.13 and Node.js required):

```bash
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install --upgrade pip
backend/.venv/bin/python -m pip install --prefer-binary -r backend/requirements-dev.txt
npm --prefix frontend install
```

Put `GEMINI_API_KEY=your_key_here` in `backend/.env` to enable AI replies.
Then start both servers with:

```bash
./scripts/dev.sh
```

Honcho prefixes output with `backend` or `frontend`. Press Ctrl+C once to stop
both servers and their child processes. If either server exits, Honcho stops the
other too. A port already in use causes startup to fail instead of silently
moving the frontend to a different port.

The script uses `backend/.venv/bin/python` without requiring activation and can
be invoked by path from any directory. Set `BACKEND_PYTHON` to an absolute Python
executable path if your environment lives elsewhere.

By default, open `http://localhost:5173`; the API runs on port 8000. To run another
instance without stopping one already running:

```bash
BACKEND_PORT=8001 FRONTEND_PORT=5174 ./scripts/dev.sh
```

The frontend proxy follows `BACKEND_PORT`. If you call the backend directly from
a different frontend origin, also set `FRONTEND_ORIGIN` to that origin.

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

## Message validation

Message content must be a string containing 1–10,000 characters after surrounding
whitespace is removed. Interior spaces and line breaks are preserved. Invalid
payloads return HTTP 422 with validation details, without saving a message or
calling the LLM.
