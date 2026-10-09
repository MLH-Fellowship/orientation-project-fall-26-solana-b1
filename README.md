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
docker-compose.yml        # runs both services in development containers
```



## Continuous integration

Pull requests and pushes to `main` run two CI jobs: backend Ruff linting, Ruff
format checking, and pytest; frontend ESLint checks and a production build.
CI uses Python 3.12 and Node.js 22 and does not require an LLM API key.

Run the same checks locally from the repository root:

```bash
backend/.venv/bin/python -m pip install -r backend/requirements-lint.txt
backend/.venv/bin/python -m ruff check backend
backend/.venv/bin/python -m ruff format --check backend
(cd backend && DATABASE_URL=sqlite:// .venv/bin/python -m pytest -q)
npm --prefix frontend ci
npm --prefix frontend run lint
npm --prefix frontend run build
```

To fix Python formatting, run `backend/.venv/bin/python -m ruff format backend`.

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

Set `JWT_SECRET` in `backend/.env` to a random value with at least 32 characters.
Add your Gemini API key if you need AI replies. Then start the API:

```bash
make backend-migrate
make backend-seed
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
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
# Set JWT_SECRET to a random value with at least 32 characters.
# Add GEMINI_API_KEY for AI replies.
python -m alembic upgrade head
python -m uvicorn app.main:app --reload --port 8000
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

One-time setup from the repository root (Python 3.10–3.13 and Node.js required):

```bash
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install --upgrade pip
backend/.venv/bin/python -m pip install --prefer-binary -r backend/requirements-dev.txt
(cd backend && .venv/bin/python -m alembic upgrade head)
npm --prefix frontend install
```

Put `GEMINI_API_KEY=your_key_here` in `backend/.env` to enable AI replies.
Then start both servers with:

```bash
./scripts/dev.sh
```

### Run with Docker

Docker Compose builds both development containers, keeps the SQLite database in
a named volume, and configures the Vite proxy to reach the backend container.

```bash
JWT_SECRET=your-random-secret-with-at-least-32-characters docker compose up --build
```

Then visit `http://localhost:5173`. The backend API is also available at
`http://localhost:8000`. Code changes under `backend/` and `frontend/` are
mounted into their containers for development reloads. The API key is optional
for the health and conversation endpoints, but generating an LLM response
requires it.

Stop both services with:

```bash
docker compose down
```

## What's here vs. what's not

This scaffold gives you: account authentication, a working conversation and
message data model, one endpoint to send a message and get an LLM reply, and a
minimal React UI that can hold a single conversation. It does not include
streaming, a multi-conversation UI, or production deployment configuration.

## Contributing

Pick an issue from `ISSUES.md`, open a branch, and submit a PR. Issues
are labeled by area (`backend`, `frontend`, `database`, `llm`, `infra`)
and difficulty (`good first issue`, `intermediate`, `advanced`).

## API

With the backend running, open [interactive API documentation](http://localhost:8000/docs)
to inspect request/response schemas and try each endpoint. The raw OpenAPI schema is
available at `http://localhost:8000/openapi.json`.


| Method | Path                               | Purpose                                                                                                                                         |
| ------ | ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| GET    | `/api/health`                      | Check that the application responds                                                                                                             |
| POST   | `/api/auth/signup`                 | Create an account from `email` and `password`, then return a success message                                                                      |
| POST   | `/api/auth/login`                  | Verify `email` and `password`, then return a bearer token                                                                                        |
| GET    | `/api/auth/me`                     | Return the user for the bearer token in the `Authorization` header                                                                               |
| POST   | `/api/conversations`               | Create a conversation, e.g. `{"title": "Learning FastAPI"}`                                                                                     |
| GET    | `/api/conversations`               | List conversations newest first; returns `{ items, total, limit, offset }`. Query params: `limit` (1–100, default 20), `offset` (≥0, default 0) |
| GET    | `/api/conversations/{id}`          | Read a conversation and its messages                                                                                                            |
| POST   | `/api/conversations/{id}/messages` | Send `{"content": "Hello!"}` and receive the saved assistant reply                                                                              |


Missing conversation IDs return HTTP 404; invalid request bodies return HTTP 422.
Sending messages requires an LLM API key. Health checks and creating, listing,
or reading conversations do not. The send endpoint returns the saved assistant
message; read the conversation again to retrieve the complete message history.

## Message validation

Message content must be a string containing 1–10,000 characters after surrounding
whitespace is removed. Interior spaces and line breaks are preserved. Invalid
payloads return HTTP 422 with validation details, without saving a message or
calling the LLM.
