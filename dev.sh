#!/usr/bin/env bash

set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$ROOT_DIR"

PIDS=()

cleanup() {
  echo
  echo "Stopping Stable Indexer..."

  for pid in "${PIDS[@]}"; do
    kill "$pid" 2>/dev/null || true
  done

  wait 2>/dev/null || true

  echo "Stopping Docker services..."
  docker compose stop

  echo "Stable Indexer stopped."
}

trap cleanup EXIT INT TERM

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker was not found."
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Docker is not running."
  echo "Start Docker Desktop and try again."
  exit 1
fi

if [[ -f ".venv/Scripts/activate" ]]; then
  source .venv/Scripts/activate
elif [[ -f ".venv/bin/activate" ]]; then
  source .venv/bin/activate
else
  echo "Could not find the Python virtual environment."
  exit 1
fi

echo "Starting PostgreSQL..."
docker compose up -d

echo "Waiting for PostgreSQL..."

until docker compose exec -T postgres \
  pg_isready -U stable -d stable_indexer >/dev/null 2>&1
do
  sleep 1
done

echo "PostgreSQL is ready."

echo "Starting FastAPI..."
uvicorn app.main:app \
  --reload \
  --loop app.uvicorn_loop:create_event_loop &
PIDS+=("$!")

echo "Starting indexer worker..."
python -m app.indexer.worker &
PIDS+=("$!")

echo "Starting React..."
npm --prefix frontend run dev &
PIDS+=("$!")

echo
echo "Stable Indexer is running."
echo
echo "FastAPI: http://127.0.0.1:8000"
echo "React:   http://localhost:5173"
echo
echo "Press Ctrl+C to stop everything."
echo

wait
