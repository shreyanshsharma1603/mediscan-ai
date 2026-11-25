#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
export PATH="$ROOT_DIR/.tools/node/bin:$PATH"

echo "Starting MediScan AI Backend on http://127.0.0.1:8000 ..."
(cd "$ROOT_DIR/backend" && "$ROOT_DIR/.venv/bin/uvicorn" app.main:app --host 127.0.0.1 --port 8000) &
BACK_PID=$!

echo "Starting MediScan AI Frontend on http://127.0.0.1:5173 ..."
(cd "$ROOT_DIR/frontend" && npm run dev) &
FRONT_PID=$!

trap 'kill $BACK_PID $FRONT_PID 2>/dev/null || true' EXIT INT TERM
wait
