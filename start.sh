#!/usr/bin/env bash
set -e

# If running from repository root, change directory into backend
if [ -d "backend" ]; then
    cd backend
fi

export PYTHONPATH=".:${PYTHONPATH:-}"

echo "=================================================="
echo "🚀 Starting LOANORBIT Backend on Render"
echo "Working Directory: $(pwd)"
echo "Port: ${PORT:-8000}"
echo "Environment: ${ENVIRONMENT:-production}"
echo "=================================================="

# Ensure private storage directory exists
mkdir -p "${STORAGE_DIR:-./storage/private}"

# Run automatic database seeding (idempotent)
echo "🌱 Initializing database state..."
python -m app.scripts.seed || echo "Seed executed or existing records preserved."

# Start uvicorn server binding to $PORT provided by Render
echo "✨ Starting Uvicorn server on 0.0.0.0:${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
