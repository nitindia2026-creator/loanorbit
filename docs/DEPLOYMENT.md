# LOANORBIT — Deployment & Operations Guide

**Target Environment:** Hostinger VPS (Ubuntu 22.04 / 24.04 LTS)  
**Orchestration:** Docker Compose  
**Reverse Proxy:** Nginx with SSL  
**Storage Architecture:** Persistent Docker Volumes with Automated Backups  

---

## 1. Directory Structure on VPS (`/opt/loanorbit/`)

```
/opt/loanorbit/
├── backend/
│   ├── app/
│   ├── alembic/
│   ├── requirements.txt
│   └── Dockerfile
├── admin/
│   ├── src/
│   ├── package.json
│   ├── nginx.conf
│   └── Dockerfile
├── nginx/
│   └── default.conf
├── storage/
│   └── private/
├── backups/
├── logs/
├── scripts/
│   ├── backup.sh
│   ├── restore.sh
│   ├── deploy.sh
│   └── seed.sh
├── docker-compose.yml
└── .env
```

---

## 2. Docker Compose Services

1. **`postgres`:**
   - PostgreSQL 16 Alpine.
   - Persistent volume `loanorbit_postgres_data:/var/lib/postgresql/data`.
   - Tuned memory limits (shared buffers, work mem) appropriate for VPS tier.
2. **`redis`:**
   - Redis 7 Alpine with Append-Only File (AOF) persistence enabled.
3. **`backend`:**
   - FastAPI container running under Uvicorn with multiple worker processes.
   - Mounts `storage/private/` for generated PDFs and synthetic document uploads.
4. **`celery_worker`:**
   - Background job processor for PDF document generation and async workflows.
5. **`admin`:**
   - Production Nginx container serving compiled React SPA with client-side route fallback.
6. **`gateway` (Nginx):**
   - Main entry point listening on port 80/443.
   - Routes `/api/v1` to `backend:8000`.
   - Routes `/admin` to `admin:80`.
   - Enforces rate limiting, security headers (CSP, HSTS, X-Frame-Options), and client file upload limits.

---

## 3. Deployment & Health Verification Workflow

```bash
# 1. Clone repository to /opt/loanorbit
git clone <repo_url> /opt/loanorbit
cd /opt/loanorbit

# 2. Configure environment variables
cp .env.example .env
# Edit .env with secure random tokens

# 3. Build and launch services
docker compose pull
docker compose build --no-cache
docker compose up -d

# 4. Run database migrations
docker compose exec backend alembic upgrade head

# 5. Populate synthetic seed data
docker compose exec backend python -m app.scripts.seed

# 6. Verify health
curl -f http://localhost/api/v1/health
```

---

## 4. Automated Backup & Disaster Recovery

- **Backup Script (`scripts/backup.sh`):**
  Takes daily pg_dump compressed backups and archives private document storage into timestamped archives (`/opt/loanorbit/backups/backup_YYYYMMDD_HHMMSS.tar.gz`).
- **Retention:**
  Maintains rolling 7 daily backups, 4 weekly backups, automatically pruning older files.
- **Restore Procedure (`scripts/restore.sh`):**
  Accepts backup archive, pauses web traffic, restores Postgres database, extracts document storage, and performs integrity verification.
