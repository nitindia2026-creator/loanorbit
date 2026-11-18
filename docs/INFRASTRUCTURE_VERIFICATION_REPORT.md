# LOANORBIT — Infrastructure & Deployment Verification Report

**Audit Type:** Phase 8 Infrastructure, Docker Compose, Nginx & Disaster Recovery Verification  
**Evaluation Date:** November 18, 2026  
**Auditor:** Principal DevOps & Infrastructure Security Engineer  
**Status:** PASS — Verified & Production-Ready  

---

## 1. Infrastructure Overview

LOANORBIT is packaged as a multi-container Docker Compose application configured for deployment on Hostinger VPS (or any standard Linux VPS hosting environment). The architecture enforces strict separation of concerns, container isolation, persistent state storage, reverse-proxy routing, and automated disaster recovery.

```
                           [ Internet / User Traffic ]
                                        │
                                        ▼
                             ┌─────────────────────┐
                             │  loanorbit_gateway  │
                             │   (Nginx Alpine)    │
                             │    Port 80 / 443    │
                             └──────────┬──────────┘
                                        │
                 ┌──────────────────────┴──────────────────────┐
                 ▼                                             ▼
       /api/v1/, /docs, /openapi.json                       /admin/
    ┌───────────────────────┐                     ┌───────────────────────┐
    │   loanorbit_backend   │                     │    loanorbit_admin    │
    │  (FastAPI Async REST) │                     │   (Nginx Static Web)  │
    └───────────┬───────────┘                     └───────────────────────┘
                │
         ┌──────┴──────────────┬───────────────────┐
         ▼                     ▼                   ▼
┌──────────────────┐  ┌──────────────────┐  ┌─────────────────────┐
│loanorbit_postgres│  │ loanorbit_redis  │  │  loanorbit_celery   │
│ (PostgreSQL 16)  │  │ (Redis 7 AOF)    │  │ (Async Task Worker) │
│  Volume: pgdata  │  │  Volume: rdata   │  │ Volume: storagedata │
└──────────────────┘  └──────────────────┘  └─────────────────────┘
```

---

## 2. Container Topology & Health Checks

| Container Name | Base Image | Role | Health Check | Restart Policy |
| :--- | :--- | :--- | :--- | :--- |
| `loanorbit_postgres` | `postgres:16-alpine` | Relational store & financial ledger | `pg_isready -U user -d db` (5s interval, 5 retries) | `unless-stopped` |
| `loanorbit_redis` | `redis:7-alpine` | Token revocation cache, rate limiting, Celery broker | `redis-cli ping` (5s interval, 5 retries) | `unless-stopped` |
| `loanorbit_backend` | Python 3.11 Slim | FastAPI REST application server | Dependent on `postgres` & `redis` healthy | `unless-stopped` |
| `loanorbit_celery` | Python 3.11 Slim | Background worker for asynchronous disbursements & reports | Dependent on `postgres` & `redis` healthy | `unless-stopped` |
| `loanorbit_admin` | Node / Nginx Alpine | React 18 Admin Portal single-page application | Nginx native process monitoring | `unless-stopped` |
| `loanorbit_gateway` | `nginx:alpine` | Reverse proxy, SSL termination, and security headers | Upstream proxy health | `unless-stopped` |

---

## 3. Storage & Persistence Verification

Four named Docker volumes are declared in `docker-compose.yml` to guarantee zero data loss across container lifecycle events:

1. **`postgres_data` (`/var/lib/postgresql/data`):**
   - Stores all relational tables, financial double-entry ledger entries, loan contracts, and customer state.
   - Preserves state across container restarts and rebuilds.

2. **`redis_data` (`/data`):**
   - Configured with `command: ["redis-server", "--appendonly", "yes"]` to enable Append-Only File (AOF) persistence.
   - Prevents loss of active token revocation denylists across Redis restarts.

3. **`storage_data` (`/opt/loanorbit/storage/private`):**
   - Private volume mounted into both `backend` and `celery_worker`.
   - Stores synthetic KYC uploads, generated KFS PDFs, sanction letters, loan agreements, payment receipts, and NOCs.
   - Strict Unix permissions prevent public directory listing.

4. **`logs_data` (`/opt/loanorbit/logs`):**
   - Persists structured JSON access and audit logs for compliance monitoring.

---

## 4. Nginx Reverse Proxy & Security Hardening

The Nginx configuration (`nginx/default.conf`) was reviewed and verified for production compliance:

### Security Headers Configured
- `X-Content-Type-Options: nosniff` (Prevents MIME-sniffing exploits).
- `X-Frame-Options: DENY` (Mitigates clickjacking attacks).
- `X-XSS-Protection: "1; mode=block"` (Enforces client XSS filter).
- `Referrer-Policy: "strict-origin-when-cross-origin"` (Restricts referrer leakage).
- `client_max_body_size: 10M` (Guards against large payload buffer overflows).

### Upstream Routing Policies
- `/api/v1/` $\rightarrow$ Proxied to `http://backend:8000/api/v1/` with `X-Real-IP`, `X-Forwarded-For`, and `X-Forwarded-Proto` preservation.
- `/docs` & `/openapi.json` $\rightarrow$ Proxied to FastAPI auto-generated interactive documentation.
- `/admin/` $\rightarrow$ Proxied to React Admin container (`http://admin:80/`).
- `/` (Root URL) $\rightarrow$ 302 redirected to `/admin/` for intuitive operator access.

---

## 5. Automated Backup & Disaster Recovery Verification

### Backup Script (`scripts/backup.sh`)
- Generates a timestamped tarball: `/opt/loanorbit/backups/loanorbit_backup_YYYYMMDD_HHMMSS.tar.gz`.
- **Atomic Operations:**
  1. Executes `docker compose exec -T postgres pg_dump -U ...` to capture a consistent SQL dump.
  2. Compresses the SQL dump together with `/opt/loanorbit/storage/private/` (all PDF contracts, receipts, and KYC artifacts).
  3. Automatically cleans up temporary files in `/tmp`.
  4. Enforces a rolling 7-day retention policy via `find ... -mtime +7 -delete`.

### Restore Script (`scripts/restore.sh`)
- Accepts a single backup archive argument: `./scripts/restore.sh <path_to_backup_archive.tar.gz>`.
- Validates archive integrity.
- Extracts archive to a temporary isolated workspace.
- Pipes the SQL dump directly into `psql` within the live `loanorbit_postgres` container.
- Copies all private storage documents back into `/opt/loanorbit/storage/private/`.
- Cleans up temporary extraction artifacts.

---

## 6. Deployment Workflow Verification

The automated deployment script (`scripts/deploy.sh`) provides a zero-friction rollout workflow:
1. `docker compose build --no-cache`: Builds fresh frontend and backend images.
2. `docker compose up -d`: Boots containers in detached mode according to dependency order.
3. Health Polling Loop: Waits until `pg_isready` confirms Postgres is accepting connections.
4. Database Seeding: Executes `python -m app.scripts.seed` to populate baseline admin accounts, roles, loan products, and ledger accounts.
5. Service Verification: Probes `curl -f http://localhost/api/v1/health` to confirm end-to-end routing.

---

## 7. Sandbox Safety Verification

- **External Network Isolation:** Containers do not expose real bureau, banking, or payment gateway network egress points.
- **Environment Isolation:** `.env.example` provides fully functional local placeholders (`loanorbit_secure_password`, `loanorbit_jwt_secret_change_me_in_production`) without exposing production secrets.
- **Watermark Compliance:** The private storage volume only stores generated documents marked with `LOANORBIT DEMO — NOT A REAL LOAN DOCUMENT`.

---

## 8. Infrastructure Sign-Off

The infrastructure, Docker Compose configuration, reverse proxy routing, and disaster recovery procedures are verified as complete, robust, and ready for deployment.
