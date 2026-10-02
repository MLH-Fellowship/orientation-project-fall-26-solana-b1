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

## API

With the backend running, open [interactive API documentation](http://localhost:8000/docs)
to inspect request/response schemas and try each endpoint. The raw OpenAPI schema is
available at `http://localhost:8000/openapi.json`.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Check that the application responds |
| POST | `/api/conversations` | Create a conversation, e.g. `{"title": "Learning FastAPI"}` |
| GET | `/api/conversations` | List conversations, newest first |
| GET | `/api/conversations/{id}` | Read a conversation and its messages |
| POST | `/api/conversations/{id}/messages` | Send `{"content": "Hello!"}` and receive the saved assistant reply |

Missing conversation IDs return HTTP 404; invalid request bodies return HTTP 422.
Sending messages requires an LLM API key. Health checks and creating, listing,
or reading conversations do not. The send endpoint returns the saved assistant
message; read the conversation again to retrieve the complete message history.
