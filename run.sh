#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

# Ensure virtualenv exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
fi

# Ensure databases are initialized
.venv/bin/python3 -m app.db.init_db

echo "Starting Domus PWA server on http://localhost:9035 ..."
exec .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 9035 --reload
