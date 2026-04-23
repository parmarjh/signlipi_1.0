#!/usr/bin/env bash
# One-shot local dev starter. Requires: python3.10+, node 18+, and (optionally) ollama.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "▶ Backend setup"
cd "$ROOT/backend"
if [ ! -d .venv ]; then python3 -m venv .venv; fi
source .venv/bin/activate
pip install -q -r requirements.txt
[ -f .env ] || cp .env.example .env

echo "▶ Starting FastAPI on :8000"
(uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &) 
BACK_PID=$!

echo "▶ Frontend setup"
cd "$ROOT/frontend"
if [ ! -d node_modules ]; then npm install; fi
echo "▶ Starting Vite on :5173"
npm run dev
