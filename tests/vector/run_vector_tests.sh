#!/usr/bin/env bash
# ==============================================================================
# PUB NEURAL / PDL — HYBRID RETRIEVAL & VECTOR INDEXING TEST HARNESS (V0.1)
# Executes VECTOR-01 to VECTOR-17 in an isolated, fresh PostgreSQL 16 container.
# Runs twice consecutively from scratch to guarantee zero residual dependencies.
# ==============================================================================

set -euo pipefail

CONTAINER_NAME="pub_neural_vector_test"
PG_PORT="54388"
POSTGRES_IMAGE="pgvector/pgvector:pg16"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

echo "=== [1/6] Checking Docker Environment ==="
if ! command -v docker >/dev/null 2>&1; then
    echo "FATAL: Docker is required but not installed or not in PATH."
    exit 1
fi

run_test_pass() {
    local pass_num="$1"
    echo "--------------------------------------------------"
    echo "=== EXECUTING COMPLETE RUN PASS #${pass_num} FROM SCRATCH ==="
    echo "--------------------------------------------------"

    docker rm -f "${CONTAINER_NAME}" 2>/dev/null || true

    echo "=== [2/6] Starting Isolated PostgreSQL 16 Container (Pass #${pass_num}) ==="
    docker run -d \
        --name "${CONTAINER_NAME}" \
        -e POSTGRES_PASSWORD=postgres \
        -p "${PG_PORT}:5432" \
        -v "${WORKSPACE_DIR}:/workspace" \
        "${POSTGRES_IMAGE}"

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

    echo "=== [4/6] Applying Embedding Provenance V0 Migration ==="
    docker exec -i "${CONTAINER_NAME}" psql -U postgres -d postgres -v ON_ERROR_STOP=1 < "${WORKSPACE_DIR}/migrations/0002_embedding_provenance_v0.sql"

    echo "=== [5/6] Applying Frozen Projector Engine V0.1 ==="
    docker exec -i "${CONTAINER_NAME}" psql -U postgres -d postgres -v ON_ERROR_STOP=1 < "${WORKSPACE_DIR}/src/projector_engine.sql"

    echo "=== [6/7] Executing Hybrid Retrieval & Vector Test Suite (VECTOR-01 to VECTOR-17) ==="
    export DB_HOST="127.0.0.1"
    export DB_PORT="${PG_PORT}"
    export DB_NAME="postgres"
    export DB_USER="pub_neural_app"
    export DB_PASS="app_secret_pw"
    export ADMIN_USER="postgres"
    export ADMIN_PASS="postgres"
    export PYTHONPATH="${WORKSPACE_DIR}"

    echo "--- Running Engineering & Adversarial Test Suite ---"
    python3 "${WORKSPACE_DIR}/tests/vector/test_hybrid_retrieval_and_vectors.py"

    echo "--- Running Real Semantic Retrieval Quality & Metrics Suite ---"
    python3 "${WORKSPACE_DIR}/tests/vector/test_semantic_quality.py"

    echo "=== [7/7] Cleanup Test Container (Pass #${pass_num}) ==="
    docker rm -f "${CONTAINER_NAME}" 2>/dev/null || true
}

# Run Pass 1
run_test_pass 1

# Run Pass 2 (guarantee complete repeatability from scratch)
run_test_pass 2

echo "=================================================="
echo "ALL HYBRID RETRIEVAL & VECTOR TESTS PASSED IN BOTH PASSES!"
echo "=================================================="
