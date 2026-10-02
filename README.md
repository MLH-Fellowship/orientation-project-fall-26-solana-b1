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

The pinned backend dependencies support Python 3.10 through 3.13. Python
3.14 is not currently supported by the pinned Pydantic release.

From the repository root, create the virtual environment, install the
dependencies, and copy the environment template with:

```bash
make backend-install
```

If your default `python3` is newer than Python 3.13, select a supported
interpreter explicitly. For example:

```bash
make backend-install PYTHON=python3.13
```

Add your Gemini API key to `backend/.env`, then start the API:

```bash
make backend-run
```

The API is available at `http://localhost:8000`; verify it with
`http://localhost:8000/api/health`. Run the backend tests with:

```bash
make backend-test
```

The equivalent manual setup is:

```bash
cd backend
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
# Add your GEMINI_API_KEY (free tier: https://aistudio.google.com/apikey)
python -m uvicorn app.main:app --reload --port 8000
```

After the backend has initialized the local database, load sample conversations
for frontend development without making an LLM request:

```bash
cd backend
python -m scripts.seed
```

The command is idempotent, so rerunning it does not duplicate the sample data.

### Frontend

The frontend requires Node.js 18 or newer. From the repository root,
install the locked dependencies and start Vite with:

```bash
make frontend-install
make frontend-run
```

Then visit `http://localhost:5173`. To verify that the production bundle
builds successfully, run:

```bash
make frontend-build
```

The equivalent manual setup is:

```bash
cd frontend
npm ci
npm run dev
```

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
