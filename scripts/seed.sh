#!/usr/bin/env bash
set -euo pipefail

echo "🌱 Running LOANORBIT Idempotent Database Seed..."
docker compose exec -T backend python -m app.scripts.seed
