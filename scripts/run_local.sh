#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -d ".venv" ]; then
  python3.11 -m venv .venv
fi

source .venv/bin/activate
export PYTHONPATH="$ROOT_DIR:${PYTHONPATH:-}"

exec uvicorn app.main:app --host 127.0.0.1 --port "${PORT:-8010}" --reload
