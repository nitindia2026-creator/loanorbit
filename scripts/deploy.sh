#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Deploying LOANORBIT on Hostinger VPS..."

# 1. Pull latest images and build
docker compose build --no-cache
docker compose up -d

# 2. Wait for Postgres health
echo "⏳ Waiting for database service to be ready..."
until docker compose exec -T postgres pg_isready -U "${POSTGRES_USER:-loanorbit_user}" -d "${POSTGRES_DB:-loanorbit_db}"; do
    sleep 2
done

# 3. Seed initial synthetic data & accounts
echo "🌱 Running database bootstrap & seed..."
docker compose exec -T backend python -m app.scripts.seed

# 4. Verify healthcheck
echo "🏥 Probing healthcheck endpoint..."
curl -f http://localhost/api/v1/health || curl -f http://localhost:8000/api/v1/health

echo "✨ LOANORBIT is live and operating!"
