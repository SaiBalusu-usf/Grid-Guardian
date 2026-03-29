#!/usr/bin/env bash
# =============================================================================
# GridGuardian - Firestore Seed Script
# =============================================================================
# Reads infra/firestore-seed.json and writes seed data to Firestore.
# If no Google Cloud credentials are available, prints what it would write.
#
# Usage:
#   bash scripts/seed-firestore.sh
#
# Environment:
#   GOOGLE_CLOUD_PROJECT - Target project (default: gridguardian-demo)
#   FIRESTORE_EMULATOR_HOST - If set, writes to emulator instead
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SEED_FILE="${PROJECT_ROOT}/infra/firestore-seed.json"

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-gridguardian-demo}"

# ---------------------------------------------------------------------------
# Check prerequisites
# ---------------------------------------------------------------------------
if [ ! -f "${SEED_FILE}" ]; then
  echo "ERROR: Seed file not found at ${SEED_FILE}"
  exit 1
fi

if ! command -v python3 &>/dev/null && ! command -v python &>/dev/null; then
  echo "ERROR: Python is required but not found in PATH."
  exit 1
fi

PYTHON_CMD="python3"
if ! command -v python3 &>/dev/null; then
  PYTHON_CMD="python"
fi

# ---------------------------------------------------------------------------
# Check if we can actually write to Firestore
# ---------------------------------------------------------------------------
DRY_RUN=false

if [ -n "${FIRESTORE_EMULATOR_HOST:-}" ]; then
  echo "[Seed] Using Firestore emulator at ${FIRESTORE_EMULATOR_HOST}"
elif gcloud auth application-default print-access-token &>/dev/null 2>&1; then
  echo "[Seed] Using application default credentials for project: ${PROJECT_ID}"
else
  echo "[Seed] No Firestore credentials detected. Running in DRY-RUN mode."
  echo "[Seed] To seed for real, run: gcloud auth application-default login"
  echo ""
  DRY_RUN=true
fi

# ---------------------------------------------------------------------------
# Seed script (Python)
# ---------------------------------------------------------------------------
${PYTHON_CMD} - "${SEED_FILE}" "${PROJECT_ID}" "${DRY_RUN}" <<'PYTHON_SCRIPT'
import json
import sys
import os
from datetime import datetime

seed_file = sys.argv[1]
project_id = sys.argv[2]
dry_run = sys.argv[3].lower() == "true"

with open(seed_file, "r") as f:
    data = json.load(f)

if dry_run:
    print("=" * 60)
    print("  DRY RUN - showing what would be written to Firestore")
    print("=" * 60)
    print()

    for collection, documents in data.items():
        print(f"Collection: {collection}")
        print(f"  Documents to write: {len(documents)}")
        for doc in documents:
            doc_id = doc.get("doc_id") or doc.get("shelter_id") or doc.get("resource_id") or "auto-id"
            print(f"    - {doc_id}")
            for key, value in doc.items():
                val_str = str(value)
                if len(val_str) > 60:
                    val_str = val_str[:57] + "..."
                print(f"        {key}: {val_str}")
        print()

    print("=" * 60)
    print("  To write for real, set up credentials:")
    print("    gcloud auth application-default login")
    print("    export GOOGLE_CLOUD_PROJECT=your-project-id")
    print("    bash scripts/seed-firestore.sh")
    print("=" * 60)
    sys.exit(0)

# Real Firestore write
try:
    from google.cloud import firestore
except ImportError:
    print("ERROR: google-cloud-firestore not installed.")
    print("  pip install google-cloud-firestore")
    sys.exit(1)

db = firestore.Client(project=project_id)

total = 0
for collection_name, documents in data.items():
    print(f"\n[Seed] Writing to collection: {collection_name}")
    for doc in documents:
        doc_id = doc.get("doc_id") or doc.get("shelter_id") or doc.get("resource_id")
        doc["_seeded_at"] = datetime.utcnow().isoformat() + "Z"

        if doc_id:
            db.collection(collection_name).document(doc_id).set(doc)
            print(f"  Written: {collection_name}/{doc_id}")
        else:
            ref = db.collection(collection_name).add(doc)
            print(f"  Written: {collection_name}/{ref[1].id}")
        total += 1

print(f"\n[Seed] Done! Wrote {total} documents to Firestore.")
PYTHON_SCRIPT

echo ""
echo "[Seed] Script finished."
