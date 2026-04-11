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
