#!/usr/bin/env bash
set -euo pipefail

CONTAINER_NAME="pub_neural_runtime_e2e"
PG_PORT="$(python3 -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1]); s.close()' )"
POSTGRES_IMAGE="pgvector/pgvector:pg16"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

cleanup() { docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true; }
trap cleanup EXIT

docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
docker run -d --name "${CONTAINER_NAME}" -e POSTGRES_PASSWORD=postgres -p "${PG_PORT}:5432" -v "${WORKSPACE_DIR}:/workspace" "${POSTGRES_IMAGE}"

for i in {1..45}; do
  docker exec "${CONTAINER_NAME}" pg_isready -U postgres >/dev/null 2>&1 && break
  sleep 1
done
for i in {1..30}; do
  docker exec "${CONTAINER_NAME}" psql -U postgres -d postgres -c "SELECT 1" >/dev/null 2>&1 && break
  sleep 1
done

VALID_CEO_HASH="0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
docker exec -i "${CONTAINER_NAME}" psql -U postgres -d postgres -v ON_ERROR_STOP=1 <<'EOSQL'
SET pub_neural.bootstrap_ceo_credential_hash = '0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef';
\i /workspace/migrations/0001_initial_v0_schema.sql
\i /workspace/migrations/0002_projector_engine_v0.sql
\i /workspace/migrations/0006_project_registry_v0.sql
\i /workspace/migrations/0007_project_ontology_v0.sql
\i /workspace/migrations/0011_runtime_atomic_idempotency_fk.sql
ALTER ROLE pub_neural_app WITH LOGIN PASSWORD 'app_secret_pw';
INSERT INTO pub_neural.holding_projects (id, slug, display_name, project_type, lifecycle_status, is_active, is_archived)
VALUES ('proj:runtime-e2e', 'runtime-e2e', 'Runtime E2E', 'PRODUCT', 'ATIVO', TRUE, FALSE)
ON CONFLICT (id) DO UPDATE SET is_active=TRUE, is_archived=FALSE;
EOSQL

docker exec -i "${CONTAINER_NAME}" psql -U postgres -d postgres -v ON_ERROR_STOP=1 < "${WORKSPACE_DIR}/src/projector_engine.sql"

export PUB_NEURAL_E2E_DB_URL="postgresql://postgres:postgres@127.0.0.1:${PG_PORT}/postgres"
export PYTHONPATH="${WORKSPACE_DIR}"
python3 "${WORKSPACE_DIR}/tests/runtime/test_runtime_postgres_e2e.py"
