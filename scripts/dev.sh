#!/usr/bin/env bash
# Start both development servers and let Honcho manage their lifecycle.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
export BACKEND_PYTHON="${BACKEND_PYTHON:-$PROJECT_ROOT/backend/.venv/bin/python}"

if [[ ! -x "$BACKEND_PYTHON" ]]; then
  echo "Backend Python not found: $BACKEND_PYTHON" >&2
  echo "Create backend/.venv and install backend/requirements-dev.txt first." >&2
  exit 1
fi
if ! "$BACKEND_PYTHON" -c 'import honcho, uvicorn' >/dev/null 2>&1; then
  echo "Install backend/requirements-dev.txt with your backend Python first." >&2
  exit 1
fi
if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required. Install Node.js before starting the frontend." >&2
  exit 1
fi
if [[ ! -d frontend/node_modules ]]; then
  echo "Frontend dependencies missing. Run npm install in frontend/ first." >&2
  exit 1
fi

if [[ ! -f Procfile.dev ]]; then
  echo "Procfile.dev is missing from the project root." >&2
  exit 1
fi

exec "$BACKEND_PYTHON" -m honcho -f Procfile.dev start
