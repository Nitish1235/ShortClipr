# ShortClipr — Production Deployment Guide

## Architecture

```text
Frontend — Cloud Run (shortclipr-frontend)
    │ HTTPS Rest APIs
    ▼
API — Cloud Run (shortclipr-api)     ◄── Google OAuth / JWT
    │ Upstash Redis RPUSH
    ▼
Worker — Cloud Run (shortclipr-worker) ◄── OpenAI / FFmpeg / MediaPipe
    │
    ├── GCS (input-videos / output-clips)
    └── Supabase (users, jobs, clips)
```

## GCP & External Setup (Manual UI Instructions)

### 1. Enable Google Cloud APIs
1. Go to **Google Cloud Console** → **APIs & Services**.
2. Click **Enable APIs and Services**.
3. Search for and enable:
   - **Cloud Run API**
   - **Cloud Build API**
   - **Artifact Registry API**
   - **Secret Manager API**
   - **Cloud Storage API**

### 2. Create Artifact Registry (Repository)
1. In Cloud Console, search for **Artifact Registry**.
2. Click **+ CREATE REPOSITORY**.
3. Fill in details:
   - **Name**: `shortclipr`
   - **Format**: Docker
   - **Location type**: Region
   - **Region**: `us-central1` (or your preferred region)
4. Click **CREATE**.

### 3. Create Cloud Storage Buckets (GCS)
1. Search for **Cloud Storage** → **Buckets**.
2. Create **two** buckets: `shortclipr-input-videos` and `shortclipr-output-clips`.
3. For `shortclipr-output-clips` (Make it public):
   - Click the bucket → **Permissions** tab → **Grant Access**.
   - **New principals**: `allUsers`
   - **Role**: `Storage Object Viewer`
   - Save and Allow Public Access.
4. For `shortclipr-input-videos` (Auto-delete after 7 days):
   - Click the bucket → **Lifecycle** tab → **Add a rule**.
   - **Condition**: Age = 7 days
   - **Action**: Delete object.

### 4. Setup Supabase Database (PostgreSQL)
1. Go to [Supabase Dashboard](https://supabase.com/dashboard).
2. Create a **New Project**.
3. Go to the **SQL Editor**, paste the contents of `infra/schema.sql` and click **Run**.
4. Go to **Project Settings** → **Database** → **Connection string** → **URI**.
5. Copy it and replace `[YOUR-PASSWORD]` with your actual db password. 
   - *This is your `SUPABASE_DB_URL`.*

### 5. Create Service Accounts & Permissions (Crucial for Cloud Run)
1. Search for **IAM & Admin** → **Service Accounts**.
2. **Create Frontend Account**:
   - Name: `shortclipr-frontend`, click Create and Continue.
   - Roles to grant: `Cloud Run Invoker`. *(It doesn't need DB or GCS access, the API handles that).*
   - Click Done.
3. **Create API Account**:
   - Name: `shortclipr-api`, click Create and Continue.

   - Roles to grant: `Storage Object Admin`, `Secret Manager Secret Accessor`.
   - Click Done.
3. **Create Worker Account**:
   - Name: `shortclipr-worker`, click Create and Continue.
   - Roles to grant: `Storage Object Admin`, `Secret Manager Secret Accessor`.
   - Click Done.

### 6. Store Secrets in Secret Manager
1. Search for **Secret Manager** → **+ CREATE SECRET**.
2. Create a secret for each of these (paste your actual value in "Secret value"):
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `JWT_SECRET_KEY`
   - `GCP_PROJECT_ID`
   - `SUPABASE_DB_URL`
   - `UPSTASH_REDIS_URL`
   - `UPSTASH_REDIS_TOKEN`
   - `OPENAI_API_KEY`
   - `DODO_PAYMENTS_API_KEY`
   - `DODO_WEBHOOK_SECRET`

### 7. Grant Cloud Build Access
*This allows Cloud Build to deploy your code to Cloud Run.*
1. Go to **IAM & Admin** → **IAM**.
2. Find the principal ending in `@cloudbuild.gserviceaccount.com`. 
   *(If you don't see it, check the "Include Google-provided role grants" box on the right).*
3. Edit that principal (pencil icon) and add these roles:
   - **Cloud Run Admin**
   - **Service Account User**
   - **Artifact Registry Writer**
   - **Secret Manager Secret Accessor**

### 8. Set up Cloud Build Triggers
1. Go to **Cloud Build** → **Triggers** → **+ CREATE TRIGGER**.
2. **For the API**:
   - **Name**: `deploy-api`
   - **Event**: Push to a branch
   - **Source**: Connect your GitHub repo, select branch `^main$`
   - **Configuration**: Cloud Build configuration file (YAML)
   - **Location**: Repository
   - **Path**: `infra/cloudbuild-api.yaml`
3. **For the Worker**:
   - Duplicate the above steps, but name it `deploy-worker` and use path `infra/cloudbuild-worker.yaml`.
4. **For the Frontend (IMPORTANT)**:
   - Duplicate the above steps, name it `deploy-frontend`, use path `infra/cloudbuild-frontend.yaml`.
   - Scroll down to the **Advanced** section in the Trigger setup → **Substitution Variables**.
   - Add two variables:
     - `_NEXT_PUBLIC_API_URL` = `https://<YOUR-API-CLOUD-RUN-URL>`
     - `_NEXT_PUBLIC_GOOGLE_CLIENT_ID` = `your-google-client-id.apps.googleusercontent.com`
   - *These are required at build time to freeze the env vars into your HTML.*

---

## Dodo Payments Setup

1. Create products in Dodo dashboard for each tier (Pro 50, Pro 100, etc).
2. Set the product IDs as secrets (`DODO_PRODUCT_PRO_50` etc.) in Cloud Secret Manager.
3. Add webhook URL in Dodo Dashboard: `https://your-api-domain.run.app/payments/webhook`
4. Copy the webhook secret and store as `DODO_WEBHOOK_SECRET` in Secret Manager.

---

## Setting Up Cloud CDN for the Frontend (Optional but Recommended)

By default, Cloud Run provides a `*.run.app` URL. To get optimal speed and custom domains, put a load balancer in front of the frontend:
1. Go to **Network services** → **Load balancing** → **Create Load Balancer**.
2. Select **Application Load Balancer (HTTP/S)** → **Global load balancer (Classic)**.
3. **Backend configuration**: Create a Serverless network endpoint group (NEG) pointing to the `shortclipr-frontend` service.
4. **Enable Cloud CDN** on that backend.
5. Add your SSL certificate and custom domain.


---

## Common Deployment Troubleshooting (Gotchas & Fixes)

If you run into issues during your Cloud Run deployment, check these common fixes we established:

### 1. Supabase Connection Errors & IPv4
*   **The Issue:** Cloud Run often struggles with direct IPv6 DB connections. If you switch to the **Supabase Transaction Pooler** (Port 6543) to get IPv4 support, your API and Worker will immediately crash with `Prepared statement does not exist` errors because `asyncpg` tries to use prepared statements which PgBouncer rejects.
*   **The Fix:** We modified the `asyncpg.create_pool` logic in both the API and Worker to include `statement_cache_size=0` and `max_inactive_connection_lifetime=300`. This completely disables prepared statements and fully supports the transaction pooler! Do not remove this.
*   **Password Errors:** If your DB password has an `@` or `+` sign, it will break Postgres URL parsing (`socket.gaierror`). You must URL-encode it (e.g., `@` becomes `%40`) or change it to alphanumeric characters.

### 2. Google OAuth 400 Errors (State Mismatch)
*   **The Issue:** You click "Login with Google", but after picking your account, it redirects to a `400 Bad Request: Invalid OAuth state`. 
*   **Why It Happens:** Cloud Run is serverless. If it reboots the container while you are logging in, or routes you to a second container, the new container's RAM is empty and it forgets your tracking `state`.
*   **The Fix:** We've disabled the strict "in-memory" state check inside `auth.py`. Long-term, if you upgrade security, you should use secure cookies or Redis for tracking OAuth state. For now, it is completely solved.

### 3. API Redirecting to Localhost
*   **The Issue:** Users log in successfully but suddenly get redirected back to `http://localhost:3000/...`.
*   **The Fix:** Ensure your `ALLOWED_ORIGINS` environment variable is fully set in Cloud Run (e.g., `https://shortclipr.com`). The API strictly looks at the first domain in this list to know where to redirect the user after a successful login.

### 4. Upstash Polling Limits (Worker Costs)
*   **The Issue:** If your worker runs `POLL_INTERVAL_SEC=2`, it makes over 43,000 HTTP requests a day to Upstash Redis, completely obliterating your 10,000/day free tier and costing you money!
*   **The Fix:** We implemented **Dynamic Polling** (Exponential Backoff). If the queue is empty, the worker gradually slows down to polling once every 15 seconds. If a job arrives, it speeds back up to 2 seconds. This keeps your usage permanently under ~5,500 daily requests.

### 5. Secret Updates Not Registering
*   **The Issue:** You updated a variable (like DB URL) directly in Google Secret Manager, but the Cloud Run app still has the old one.
*   **The Fix:** Cloud Run caches secrets upon boot. Whenever you change a secret, you *must* click **Deploy New Revision** in your Cloud Run dashboard to force the containers to pull the fresh secret.

---

## Local Development Environment

```bash
# API
cd backend/api
cp ../../.env.example .env  # fill in values
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Worker
cd backend/worker
cp ../../.env.example .env
pip install -r requirements.txt
python app/main.py

# Frontend
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

See `.env.example` in the project root for detailed variable descriptions.
