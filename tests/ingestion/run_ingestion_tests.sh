#!/usr/bin/env bash
# ==============================================================================
# PUB NEURAL / PDL — INGESTION & EXTRACTION PIPELINE TEST HARNESS (V0.1)
# Verifies ING-01 to ING-15 in an isolated, fresh PostgreSQL 16 container.
# ==============================================================================

set -euo pipefail

CONTAINER_NAME="pub_neural_ingestion_test"
PG_PORT="54399"
POSTGRES_IMAGE="pgvector/pgvector:pg16"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

echo "=== [1/6] Checking Docker Environment ==="
if ! command -v docker >/dev/null 2>&1; then
    echo "FATAL: Docker is required but not installed or not in PATH."
    exit 1
fi

# Cleanup existing container if running
docker rm -f "${CONTAINER_NAME}" 2>/dev/null || true
rm -rf /tmp/pub_neural_vault

echo "=== [2/6] Starting Isolated PostgreSQL 16 Container ==="
docker run -d \
    --name "${CONTAINER_NAME}" \
    -e POSTGRES_PASSWORD=postgres \
    -p "${PG_PORT}:5432" \
    -v "${WORKSPACE_DIR}:/workspace" \
    "${POSTGRES_IMAGE}"

# Wait for PostgreSQL to become ready
echo "Waiting for PostgreSQL to be ready on port ${PG_PORT}..."
for i in {1..30}; do
    if docker exec -i "${CONTAINER_NAME}" pg_isready -U postgres >/dev/null 2>&1; then
        echo "PostgreSQL is ready."
        break
    fi
    sleep 1
    if [ "$i" -eq 30 ]; then
        echo "FATAL: Timed out waiting for PostgreSQL container to start."
        exit 1
    fi
done

echo "=== [3/6] Applying Baseline Schema Migration (0001) ==="
VALID_CEO_HASH="0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
docker exec -i "${CONTAINER_NAME}" psql -U postgres -d postgres -v ON_ERROR_STOP=1 << EOSQL
SET pub_neural.bootstrap_ceo_credential_hash = '${VALID_CEO_HASH}';
\i /workspace/migrations/0001_initial_v0_schema.sql
ALTER ROLE pub_neural_app WITH LOGIN PASSWORD 'app_secret_pw';
EOSQL

echo "=== [4/6] Applying Frozen Projector Engine V0.1 ==="
docker exec -i "${CONTAINER_NAME}" psql -U postgres -d postgres -v ON_ERROR_STOP=1 < "${WORKSPACE_DIR}/src/projector_engine.sql"

echo "=== [5/6] Executing Ingestion & Graph Extraction Test Suite (ING-01 to ING-22) ==="
export DB_HOST="127.0.0.1"
export DB_PORT="${PG_PORT}"
export DB_NAME="postgres"
export DB_USER="pub_neural_app"
export DB_PASS="app_secret_pw"
export ADMIN_PASS="postgres"
export PYTHONPATH="${WORKSPACE_DIR}"

python3 "${WORKSPACE_DIR}/tests/ingestion/test_ingestion_and_extraction.py"

echo "=== [6/6] Cleanup Test Container ==="
docker rm -f "${CONTAINER_NAME}" 2>/dev/null || true

echo "=================================================="
echo "ALL INGESTION & GRAPH EXTRACTION TESTS PASSED!"
echo "=================================================="
