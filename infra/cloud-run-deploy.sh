#!/usr/bin/env bash
# =============================================================================
# GridGuardian - Google Cloud Run Deployment Script
# =============================================================================
# Deploys all three services (backend, shelter-agent, frontend) to Cloud Run.
#
# Prerequisites:
#   - gcloud CLI installed and authenticated
#   - Docker installed (for local builds) or Cloud Build enabled
#   - Artifact Registry repository created
#
# Usage:
#   export GOOGLE_CLOUD_PROJECT=your-project-id
#   export GEMINI_API_KEY=your-key
#   bash infra/cloud-run-deploy.sh
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# 1. Project variables
# ---------------------------------------------------------------------------
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:?Set GOOGLE_CLOUD_PROJECT environment variable}"
REGION="${CLOUD_RUN_REGION:-us-central1}"
REPO_NAME="gridguardian"
REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}"

echo "============================================="
echo "  GridGuardian Cloud Run Deployment"
echo "  Project:  ${PROJECT_ID}"
echo "  Region:   ${REGION}"
echo "  Registry: ${REGISTRY}"
echo "============================================="

# ---------------------------------------------------------------------------
# 2. Set the active project
# ---------------------------------------------------------------------------
echo ""
echo "[1/7] Setting active project to ${PROJECT_ID}..."
gcloud config set project "${PROJECT_ID}"

# ---------------------------------------------------------------------------
# 3. Enable required APIs
# ---------------------------------------------------------------------------
echo ""
echo "[2/7] Enabling required APIs..."
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  firestore.googleapis.com \
  --quiet

# ---------------------------------------------------------------------------
# 4. Create Artifact Registry repository (if it doesn't exist)
# ---------------------------------------------------------------------------
echo ""
echo "[3/7] Ensuring Artifact Registry repository exists..."
gcloud artifacts repositories describe "${REPO_NAME}" \
  --location="${REGION}" --format="value(name)" 2>/dev/null || \
gcloud artifacts repositories create "${REPO_NAME}" \
  --repository-format=docker \
  --location="${REGION}" \
  --description="GridGuardian container images"

# Configure Docker authentication for the registry
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

# ---------------------------------------------------------------------------
# 5. Build and push Docker images
# ---------------------------------------------------------------------------
echo ""
echo "[4/7] Building and pushing Docker images..."

# Backend image
echo "  -> Building backend..."
docker build -t "${REGISTRY}/backend:latest" ./backend
docker push "${REGISTRY}/backend:latest"

# Shelter agent image
echo "  -> Building shelter-agent..."
docker build -t "${REGISTRY}/shelter-agent:latest" ./backend/a2a_shelter_agent
docker push "${REGISTRY}/shelter-agent:latest"

# Frontend image
echo "  -> Building frontend..."
docker build -t "${REGISTRY}/frontend:latest" ./frontend
docker push "${REGISTRY}/frontend:latest"

# ---------------------------------------------------------------------------
# 6. Deploy services to Cloud Run
# ---------------------------------------------------------------------------
echo ""
echo "[5/7] Deploying shelter-agent service..."
gcloud run deploy shelter-agent \
  --image="${REGISTRY}/shelter-agent:latest" \
  --region="${REGION}" \
  --platform=managed \
  --port=8001 \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=3 \
  --allow-unauthenticated \
  --quiet

# Retrieve the shelter agent URL for the backend to use
SHELTER_AGENT_URL=$(gcloud run services describe shelter-agent \
  --region="${REGION}" --format="value(status.url)")
echo "  Shelter Agent URL: ${SHELTER_AGENT_URL}"

echo ""
echo "[6/7] Deploying backend service..."
gcloud run deploy backend \
  --image="${REGISTRY}/backend:latest" \
  --region="${REGION}" \
  --platform=managed \
  --port=8000 \
  --memory=1Gi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=5 \
  --allow-unauthenticated \
  --set-env-vars="USE_MOCK=false,SHELTER_AGENT_URL=${SHELTER_AGENT_URL},GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GEMINI_API_KEY=${GEMINI_API_KEY:-}" \
  --quiet

BACKEND_URL=$(gcloud run services describe backend \
  --region="${REGION}" --format="value(status.url)")
echo "  Backend URL: ${BACKEND_URL}"

echo ""
echo "[7/7] Deploying frontend service..."
gcloud run deploy frontend \
  --image="${REGISTRY}/frontend:latest" \
  --region="${REGION}" \
  --platform=managed \
  --port=3000 \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=3 \
  --allow-unauthenticated \
  --set-env-vars="NEXT_PUBLIC_API_URL=${BACKEND_URL}" \
  --quiet

FRONTEND_URL=$(gcloud run services describe frontend \
  --region="${REGION}" --format="value(status.url)")
echo "  Frontend URL: ${FRONTEND_URL}"

# ---------------------------------------------------------------------------
# 7. Output summary
# ---------------------------------------------------------------------------
echo ""
echo "============================================="
echo "  Deployment Complete!"
echo "============================================="
echo ""
echo "  Frontend:      ${FRONTEND_URL}"
echo "  Backend API:   ${BACKEND_URL}"
echo "  Shelter Agent: ${SHELTER_AGENT_URL}"
echo ""
echo "  API Docs:      ${BACKEND_URL}/docs"
echo "  Health Check:  ${BACKEND_URL}/health"
echo ""
echo "============================================="
