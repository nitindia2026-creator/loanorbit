# LOANORBIT — Render Cloud Deployment Guide

This guide walks you through deploying the **LOANORBIT Backend** on [Render](https://render.com).

The backend is configured with:
- Dynamic `$PORT` binding (Render port assignment).
- Automatic PostgreSQL connection string adaptation (`postgres://` / `postgresql://` $\rightarrow$ `postgresql+asyncpg://`).
- Automatic startup migrations and idempotent database seeding.
- Dynamic permissive CORS (`allow_origin_regex`) for web and mobile frontends.
- Stateless PDF rendering with zero required persistent disk for demo mode.

---

## Option 1: One-Click Blueprint Deployment (Recommended)

Render provides Infrastructure-as-Code blueprints using the included [`render.yaml`](file:///d:/firewing/loanorbit/render.yaml).

1. Push your repository to **GitHub** or **GitLab**.
2. Log in to [dashboard.render.com](https://dashboard.render.com).
3. Click **New +** $\rightarrow$ **Blueprint**.
4. Connect your LOANORBIT repository.
5. Render will automatically detect `render.yaml` and prompt you to create:
   - **`loanorbit-postgres`**: Free PostgreSQL database.
   - **`loanorbit-backend`**: Python 3.11 Web Service running FastAPI.
6. Click **Apply**.
7. Render will provision the database, install dependencies, run migrations, seed initial demo accounts, and launch the backend at:
   `https://loanorbit-backend.onrender.com`

---

## Option 2: Manual Dashboard Setup

If you prefer setting up services manually in the Render dashboard:

### Step 1: Create a PostgreSQL Database on Render
1. In Render Dashboard, click **New +** $\rightarrow$ **PostgreSQL**.
2. Set the configuration:
   - **Name:** `loanorbit-postgres`
   - **Database:** `loanorbit_db`
   - **User:** `loanorbit_user`
   - **Region:** Any (e.g. Oregon)
   - **Plan:** Free
3. Click **Create Database**.
4. Once created, copy the **Internal Database URL** (or **External Database URL**).

### Step 2: Create the Backend Web Service
1. In Render Dashboard, click **New +** $\rightarrow$ **Web Service**.
2. Connect your Git repository.
3. Configure the service:
   - **Name:** `loanorbit-backend`
   - **Region:** Same region as your database
   - **Root Directory:** `backend`
   - **Runtime:** `Python` (or `Docker`)
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `bash start.sh` (or `uvicorn app.main:app --host 0.0.0.0 --port $PORT`)
   - **Plan:** Free

### Step 3: Configure Environment Variables
Under the **Environment** tab of your web service, add the following key-value pairs:

| Variable Name | Recommended Value | Notes |
| :--- | :--- | :--- |
| `PYTHON_VERSION` | `3.11.9` | Ensures exact Python runtime |
| `ENVIRONMENT` | `production` | Production mode |
| `IS_SANDBOX_DEMO` | `true` | Enables mock providers & sandbox mode |
| `DEBUG` | `false` | Disables debug tracebacks |
| `SECRET_KEY` | *(Click "Generate")* | 32+ character cryptographically random string |
| `DATABASE_URL` | *(Paste Internal Database URL from Step 1)* | Auto-adapted to `postgresql+asyncpg://` |
| `BACKEND_CORS_ORIGINS` | `*` | Allows React admin and mobile clients |
| `STORAGE_DIR` | `/tmp/storage/private` | In-memory/ephemeral storage directory |

4. Click **Deploy Web Service**.

---

## Verification & Health Check

Once the deployment status shows **Live**:

1. **Root Status Check:**
   Open: `https://<your-service-name>.onrender.com/`
   ```json
   {
     "project": "LOANORBIT",
     "tagline": "Your Credit Journey, Clearly Guided.",
     "version": "1.0.0",
     "docs": "/docs",
     "status": "online",
     "mode": "SYNTHETIC_SANDBOX_DEMO"
   }
   ```

2. **Interactive OpenAPI Documentation:**
   Open: `https://<your-service-name>.onrender.com/docs`

3. **Uptime Health Probe:**
   Open: `https://<your-service-name>.onrender.com/api/v1/health`
   ```json
   {
     "status": "healthy",
     "service": "LOANORBIT",
     "environment": "production",
     "is_sandbox_demo": true,
     "components": {
       "api": "UP",
       "financial_engine": "UP",
       "mock_providers": "UP"
     }
   }
   ```

---

## Pre-Seeded Admin & Customer Demo Credentials

The backend automatically seeds these credentials on first run:

- **Super Admin:** `superadmin@loanorbit.demo` / `AdminPass123!`
- **Underwriter Lead:** `underwriter@loanorbit.demo` / `AdminPass123!`
- **KYC Lead:** `kyc@loanorbit.demo` / `AdminPass123!`
- **Finance Lead:** `finance@loanorbit.demo` / `AdminPass123!`
- **Support Lead:** `support@loanorbit.demo` / `AdminPass123!`
- **Customer Mobile Demo:** Mobile `9876543210` / OTP `123456`
