#!/bin/bash
# Iris backend (FastAPI). Runs in its own container; the web terminal shares the same virtualenv.
cd /code/iris || exit 1

# First run: create .env from the template so the app can start (fill in credentials afterwards)
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created code/iris/.env from .env.example - add your credentials there."
fi

uv sync --frozen --extra dev || exit 1

# --reload-dir is limited to Python code so the watcher ignores node_modules.
export WATCHFILES_FORCE_POLLING=true

# uvicorn's reloader keeps the environment it first loaded (python-dotenv never overrides
# existing variables), so a plain --reload would ignore later .env edits such as the
# CTX_SURFACE_ID / MCP_AGENT_KEY that `make setup` writes. Restart the whole server instead.
env_stamp() { stat -c %Y .env; }
pid=""
trap '[ -n "$pid" ] && kill "$pid" 2>/dev/null; exit 0' TERM INT

while true; do
  stamp=$(env_stamp)
  # Keep the Redis Insight import file in sync with .env (see docs/tasks/task-2.md)
  python scripts/insight_import.py >/dev/null 2>&1 || true
  uvicorn backend.app.main:app \
    --host 0.0.0.0 --port 8040 \
    --reload --reload-dir backend --reload-dir domains &
  pid=$!
  while kill -0 "$pid" 2>/dev/null && [ "$(env_stamp)" = "$stamp" ]; do sleep 2; done
  if kill -0 "$pid" 2>/dev/null; then
    # .env changed: let any in-progress writes settle, then restart with fresh settings
    sleep 3
    echo ".env changed, restarting the backend..."
    kill "$pid"
  fi
  wait "$pid" 2>/dev/null
  sleep 1
done
