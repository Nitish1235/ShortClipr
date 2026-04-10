# ShortClipr — Production Deployment Guide

## Architecture

```
Frontend (Vercel)
    │ HTTPS
    ▼
API — Cloud Run (shortclipr-api)     ◄── Google OAuth / JWT
    │ Upstash Redis RPUSH
    ▼
Worker — Cloud Run (shortclipr-worker) ◄── OpenAI / FFmpeg / MediaPipe
    │
    ├── GCS (input-videos / output-clips)
    └── Firestore (jobs, users)
```

## GCP Setup (one-time)

### 1. Enable APIs
```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  firestore.googleapis.com \
  storage.googleapis.com
```

### 2. Create Artifact Registry repository
```bash
gcloud artifacts repositories create shortclipr \
  --repository-format=docker \
  --location=us-central1
```

### 3. Create GCS buckets
```bash
gsutil mb -l us-central1 gs://shortclipr-input-videos
gsutil mb -l us-central1 gs://shortclipr-output-clips

# Make output bucket objects publicly readable
gsutil iam ch allUsers:objectViewer gs://shortclipr-output-clips

# Input bucket: 7-day lifecycle to auto-delete uploaded source videos
cat > /tmp/lifecycle.json << 'EOF'
{"rule":[{"action":{"type":"Delete"},"condition":{"age":7}}]}
EOF
gsutil lifecycle set /tmp/lifecycle.json gs://shortclipr-input-videos
```

### 4. Create Firestore database
```bash
gcloud firestore databases create --location=us-central1
```

### 5. Create Service Accounts
```bash
# API service account
gcloud iam service-accounts create shortclipr-api \
  --display-name="ShortClipr API"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:shortclipr-api@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/datastore.user"
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:shortclipr-api@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:shortclipr-api@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Worker service account
gcloud iam service-accounts create shortclipr-worker \
  --display-name="ShortClipr Worker"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:shortclipr-worker@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/datastore.user"
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:shortclipr-worker@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:shortclipr-worker@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### 6. Store secrets in Secret Manager
```bash
# For each secret:
echo -n "your-value" | gcloud secrets create SECRET_NAME \
  --data-file=- --replication-policy=automatic

# Required secrets:
# GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, JWT_SECRET_KEY,
# GCP_PROJECT_ID, UPSTASH_REDIS_URL, UPSTASH_REDIS_TOKEN,
# OPENAI_API_KEY, DODO_PAYMENTS_API_KEY, DODO_WEBHOOK_SECRET,
# DODO_PRODUCT_PRO_50, DODO_PRODUCT_PRO_100, DODO_PRODUCT_PRO_200,
# DODO_PRODUCT_PRO_400, DODO_PRODUCT_PRO_500
```

### 7. Set up Cloud Build triggers
```bash
# API trigger — fires on push to main that touches backend/api/**
gcloud builds triggers create github \
  --repo-name=shortclipr \
  --repo-owner=YOUR_GITHUB_ORG \
  --branch-pattern="^main$" \
  --build-config=infra/cloudbuild-api.yaml \
  --included-files="backend/api/**" \
  --name="deploy-api"

# Worker trigger
gcloud builds triggers create github \
  --repo-name=shortclipr \
  --repo-owner=YOUR_GITHUB_ORG \
  --branch-pattern="^main$" \
  --build-config=infra/cloudbuild-worker.yaml \
  --included-files="backend/worker/**" \
  --name="deploy-worker"
```

### 8. Grant Cloud Build access to deploy
```bash
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
CB_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${CB_SA}" --role="roles/run.admin"
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${CB_SA}" --role="roles/iam.serviceAccountUser"
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${CB_SA}" --role="roles/artifactregistry.writer"
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${CB_SA}" --role="roles/secretmanager.secretAccessor"
```

## Dodo Payments Setup

1. Create products in Dodo dashboard for each tier
2. Set the product IDs as secrets (`DODO_PRODUCT_PRO_50` etc.)
3. Add webhook URL: `https://your-api-domain.run.app/payments/webhook`
4. Copy webhook secret → store as `DODO_WEBHOOK_SECRET`

## Firestore Indexes

Create these composite indexes in the Firestore console (or `firestore.indexes.json`):

```
Collection: jobs
  Fields: user_id ASC, created_at DESC
```

## Frontend Deployment (Vercel)

```bash
# Set environment variables in Vercel dashboard:
NEXT_PUBLIC_API_URL=https://shortclipr-api-xxxx-uc.a.run.app
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-google-client-id
```

## Local Development

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

## Environment Variable Reference

See `.env.example` in the project root for all variables with descriptions.
