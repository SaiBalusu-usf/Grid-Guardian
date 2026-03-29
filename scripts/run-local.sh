#!/usr/bin/env bash
# =============================================================================
# GridGuardian - Local Development Runner
# =============================================================================
# Starts all three services (shelter-agent, backend, frontend) locally.
# Handles cleanup on Ctrl+C.
#
# Usage:
#   bash scripts/run-local.sh
# =============================================================================

set -euo pipefail

# Resolve project root (parent of scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# PIDs to track for cleanup
PIDS=()

# ---------------------------------------------------------------------------
# Cleanup handler - kill all child processes on exit
# ---------------------------------------------------------------------------
cleanup() {
  echo ""
  echo "[GridGuardian] Shutting down all services..."
  for pid in "${PIDS[@]}"; do
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
      wait "$pid" 2>/dev/null || true
    fi
  done
  echo "[GridGuardian] All services stopped."
  exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# ---------------------------------------------------------------------------
# Load environment
# ---------------------------------------------------------------------------
if [ -f "${PROJECT_ROOT}/.env" ]; then
  echo "[GridGuardian] Loading .env file..."
  set -a
  source "${PROJECT_ROOT}/.env"
  set +a
else
  echo "[GridGuardian] No .env file found, using defaults (USE_MOCK=true)."
  export USE_MOCK=true
fi

# ---------------------------------------------------------------------------
# 1. Start Shelter Agent (port 8001)
# ---------------------------------------------------------------------------
echo "[GridGuardian] Starting Shelter Agent on port 8001..."
cd "${PROJECT_ROOT}/backend/a2a_shelter_agent"
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload &
PIDS+=($!)
cd "${PROJECT_ROOT}"

# ---------------------------------------------------------------------------
# 2. Start Backend (port 8000)
# ---------------------------------------------------------------------------
echo "[GridGuardian] Starting Backend on port 8000..."
cd "${PROJECT_ROOT}"
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
PIDS+=($!)

# ---------------------------------------------------------------------------
# 3. Start Frontend (port 3000)
# ---------------------------------------------------------------------------
echo "[GridGuardian] Starting Frontend on port 3000..."
cd "${PROJECT_ROOT}/frontend"
npm run dev &
PIDS+=($!)
cd "${PROJECT_ROOT}"

# ---------------------------------------------------------------------------
# 4. Wait for services to be ready
# ---------------------------------------------------------------------------
echo ""
echo "[GridGuardian] Waiting for services to start..."

wait_for_port() {
  local port=$1
  local name=$2
  local retries=30
  while ! curl -s "http://localhost:${port}" > /dev/null 2>&1; do
    retries=$((retries - 1))
    if [ $retries -le 0 ]; then
      echo "  [WARNING] ${name} on port ${port} did not start in time."
      return 1
    fi
    sleep 1
  done
  echo "  [OK] ${name} is ready on port ${port}"
  return 0
}

wait_for_port 8001 "Shelter Agent"
wait_for_port 8000 "Backend"
wait_for_port 3000 "Frontend"

# ---------------------------------------------------------------------------
# 5. Open browser
# ---------------------------------------------------------------------------
echo ""
echo "============================================="
echo "  GridGuardian is running!"
echo "============================================="
echo ""
echo "  Frontend:      http://localhost:3000"
echo "  Backend API:   http://localhost:8000"
echo "  API Docs:      http://localhost:8000/docs"
echo "  Shelter Agent: http://localhost:8001"
echo ""
echo "  Press Ctrl+C to stop all services."
echo "============================================="
echo ""

# Attempt to open browser (works on macOS, Linux, and Windows/WSL)
if command -v open &>/dev/null; then
  open "http://localhost:3000"
elif command -v xdg-open &>/dev/null; then
  xdg-open "http://localhost:3000"
elif command -v start &>/dev/null; then
  start "http://localhost:3000"
fi

# ---------------------------------------------------------------------------
# 6. Wait for all background processes
# ---------------------------------------------------------------------------
wait
