# LOANORBIT — Production VPS Deployment Guide

**Host Infrastructure:** Hostinger VPS (Ubuntu 22.04 / 24.04 LTS)  
**Deployment Tool:** Docker Compose  

---

## 1. Prerequisites on Hostinger VPS

1. Update packages:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```
2. Install Docker and Docker Compose plugin:
   ```bash
   sudo apt install -y docker.io docker-compose-plugin curl
   sudo systemctl enable --now docker
   ```

---

## 2. Directory Layout & Setup

Clone the repository to `/opt/loanorbit`:
```bash
sudo mkdir -p /opt/loanorbit
sudo chown -R $USER:$USER /opt/loanorbit
git clone <your_repo_url> /opt/loanorbit
cd /opt/loanorbit
```

---

## 3. Environment Configuration

```bash
cp .env.example .env
nano .env
```
Ensure you update:
- `SECRET_KEY`: Set to a cryptographically secure 64-character random string.
- `POSTGRES_PASSWORD`: Set a strong database password.

---

## 4. Launching the Services

Run the automated deployment script:
```bash
chmod +x scripts/*.sh
./scripts/deploy.sh
```

Or execute directly via Docker Compose:
```bash
docker compose pull
docker compose build --no-cache
docker compose up -d
docker compose exec -T backend python -m app.scripts.seed
```

---

## 5. Reverse Proxy Routing (Nginx)

The gateway container handles all inbound traffic on port 80:
- `http://<your-vps-ip>/api/v1/*` $\rightarrow$ Routed directly to FastAPI backend (`backend:8000`).
- `http://<your-vps-ip>/admin/*` $\rightarrow$ Routed to compiled React SPA (`admin:80`).
- `http://<your-vps-ip>/docs` $\rightarrow$ Interactive OpenAPI Swagger documentation.

---

## 6. Daily Automated Backups

Configure a daily cron job to run the backup script:
```bash
crontab -e
```
Add the following line to run backups every night at 2:00 AM UTC:
```cron
0 2 * * * /opt/loanorbit/scripts/backup.sh >> /opt/loanorbit/logs/backup.log 2>&1
```
