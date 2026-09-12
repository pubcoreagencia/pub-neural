#!/usr/bin/env bash
set -euo pipefail

CONTAINER_NAME="pub_neural_projector_test"
IMAGE_NAME="pgvector/pgvector:pg16"
WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "=== [1/6] Checking Docker Environment ==="
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed or not in PATH."
    exit 1
fi

echo "=== [2/6] Starting Isolated PostgreSQL 16 Container ==="
docker rm -f "${CONTAINER_NAME}" 2>/dev/null || true

docker run -d \
    --name "${CONTAINER_NAME}" \
    -e POSTGRES_PASSWORD=postgres \
    -e POSTGRES_DB=postgres \
    -v "${WORKSPACE_DIR}:/workspace" \
    "${IMAGE_NAME}"

echo "Waiting for PostgreSQL to be ready..."
sleep 2
until docker exec "${CONTAINER_NAME}" pg_isready -U postgres >/dev/null 2>&1; do
    sleep 0.5
done
echo "PostgreSQL is ready."

echo "=== [3/6] Applying Migration 0001 (Baseline Schema) ==="
VALID_CEO_HASH="0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
docker exec -i "${CONTAINER_NAME}" psql -U postgres -d postgres -v ON_ERROR_STOP=1 << EOSQL
SET pub_neural.bootstrap_ceo_credential_hash = '${VALID_CEO_HASH}';
\i /workspace/migrations/0001_initial_v0_schema.sql
EOSQL

echo "=== [4/6] Applying Hardened Projector Engine V0.1 ==="
docker exec -i "${CONTAINER_NAME}" psql -U postgres -d postgres -v ON_ERROR_STOP=1 < "${WORKSPACE_DIR}/src/projector_engine.sql"

echo "=== [5/6] Executing Test Suite RPL-01 to RPL-20 ==="
docker exec -i "${CONTAINER_NAME}" psql -U postgres -d postgres -v ON_ERROR_STOP=1 < "${WORKSPACE_DIR}/tests/projectors/test_projectors_and_replay.sql"

echo "=== [6/6] Executing Real run_projector Crash Simulation (pg_terminate_backend) ==="
# Reset checkpoint to 0 (so run_projector(1, NULL) starts cleanly from sequence 1 and hits sequence 2)
docker exec -i "${CONTAINER_NAME}" psql -U postgres -d postgres -v ON_ERROR_STOP=1 -c "
    TRUNCATE TABLE pub_neural.neural_evidence CASCADE;
    TRUNCATE TABLE pub_neural.neural_edges CASCADE;
    TRUNCATE TABLE pub_neural.neural_fts CASCADE;
    TRUNCATE TABLE pub_neural.neural_nodes CASCADE;
    TRUNCATE TABLE pub_neural.neural_sources CASCADE;
    DELETE FROM pub_neural.neural_projection_checkpoints WHERE projector_name = 'graph_projector';
"

# 1. Capture comprehensive MD5 snapshot before crash across all 5 projections and checkpoints
SNAP_BEFORE_NODES=$(docker exec -i "${CONTAINER_NAME}" psql -U postgres -d postgres -t -c "SELECT md5(string_agg(id || ':' || title || ':' || promotion_state || ':' || conflict_state || ':' || is_active || ':' || recorded_from::text || ':' || updated_at::text, ',' ORDER BY id)) FROM pub_neural.neural_nodes;")
SNAP_BEFORE_EDGES=$(docker exec -i "${CONTAINER_NAME}" psql -U postgres -d postgres -t -c "SELECT md5(string_agg(id::text || ':' || source_id || '->' || target_id || ':' || relation_type || ':' || weight::text, ',' ORDER BY id)) FROM pub_neural.neural_edges;")
SNAP_BEFORE_SOURCES=$(docker exec -i "${CONTAINER_NAME}" psql -U postgres -d postgres -t -c "SELECT md5(string_agg(id::text || ':' || repository || ':' || file_path || ':' || file_sha256, ',' ORDER BY id)) FROM pub_neural.neural_sources;")
SNAP_BEFORE_EVIDENCE=$(docker exec -i "${CONTAINER_NAME}" psql -U postgres -d postgres -t -c "SELECT md5(string_agg(id::text || ':' || source_id::text || ':' || content_hash, ',' ORDER BY id)) FROM pub_neural.neural_evidence;")
SNAP_BEFORE_FTS=$(docker exec -i "${CONTAINER_NAME}" psql -U postgres -d postgres -t -c "SELECT md5(string_agg(id || ':' || language_config::text || ':' || tsv_document::text, ',' ORDER BY id)) FROM pub_neural.neural_fts;")
BEFORE_CHK=$(docker exec -i "${CONTAINER_NAME}" psql -U postgres -d postgres -t -c "SELECT COALESCE((SELECT last_processed_global_sequence FROM pub_neural.neural_projection_checkpoints WHERE projector_name = 'graph_projector'), 0);")
BEFORE_CHK=$(echo "${BEFORE_CHK}" | tr -d '[:space:]')

# 2. Launch run_projector('graph_projector') with controlled pause GUC active on sequence 2
docker exec -i "${CONTAINER_NAME}" psql -U postgres -d postgres -c "
SET pub_neural.test_pause_at_sequence = '2';
SET pub_neural.test_pause_duration = '10.0';
SELECT * FROM pub_neural.run_projector('graph_projector', 1, NULL);
" &
CRASH_CLIENT_PID=$!

# 3. Detect and inspect the exact PostgreSQL backend process executing run_projector
echo "Waiting for run_projector to enter controlled pause and identifying target backend PID..."
TARGET_BACKEND_PID=""
for i in {1..30}; do
    TARGET_BACKEND_PID=$(docker exec -i "${CONTAINER_NAME}" psql -U postgres -d postgres -t -c "
        SELECT pid FROM pg_stat_activity 
        WHERE query LIKE '%pub_neural.run_projector%' 
          AND query LIKE '%test_pause%' 
          AND state = 'active' 
          AND pid <> pg_backend_pid();
    " | tr -d '[:space:]')

    if [ -n "$TARGET_BACKEND_PID" ]; then
        break
    fi
    sleep 0.2
done

if [ -z "$TARGET_BACKEND_PID" ]; then
    echo "FATAL: Could not identify backend PID executing run_projector!"
    exit 1
fi

echo "--- TARGET BACKEND IDENTIFIED FOR CRASH TERMINATION ---"
docker exec -i "${CONTAINER_NAME}" psql -U postgres -d postgres -x -c "
    SELECT pid, usename, application_name, query, state, wait_event_type, wait_event, backend_start, query_start
    FROM pg_stat_activity 
    WHERE pid = ${TARGET_BACKEND_PID};
"

# 4. Abruptly kill the exact identified backend executing run_projector
echo "Executing pg_terminate_backend on target PID ${TARGET_BACKEND_PID}..."
KILL_RESULT=$(docker exec -i "${CONTAINER_NAME}" psql -U postgres -d postgres -t -c "
    SELECT pg_terminate_backend(${TARGET_BACKEND_PID});
" | tr -d '[:space:]')

if [ "$KILL_RESULT" != "t" ]; then
    echo "FATAL: pg_terminate_backend(${TARGET_BACKEND_PID}) returned '${KILL_RESULT}', expected 't'!"
    exit 1
fi

# Wait for process to exit and confirm PID is dead
wait $CRASH_CLIENT_PID 2>/dev/null || true

PID_STILL_ALIVE=$(docker exec -i "${CONTAINER_NAME}" psql -U postgres -d postgres -t -c "
    SELECT count(*) FROM pg_stat_activity WHERE pid = ${TARGET_BACKEND_PID};
" | tr -d '[:space:]')

if [ "$PID_STILL_ALIVE" != "0" ]; then
    echo "FATAL: Target backend PID ${TARGET_BACKEND_PID} is still alive after termination!"
    exit 1
fi
echo "Confirmed: Target backend PID ${TARGET_BACKEND_PID} was abruptly terminated and is dead."

# 5. Connect again and verify all 5 projection tables and checkpoint: EXACT snapshot rollback equality!
SNAP_AFTER_NODES=$(docker exec -i "${CONTAINER_NAME}" psql -U postgres -d postgres -t -c "SELECT md5(string_agg(id || ':' || title || ':' || promotion_state || ':' || conflict_state || ':' || is_active || ':' || recorded_from::text || ':' || updated_at::text, ',' ORDER BY id)) FROM pub_neural.neural_nodes;")
SNAP_AFTER_EDGES=$(docker exec -i "${CONTAINER_NAME}" psql -U postgres -d postgres -t -c "SELECT md5(string_agg(id::text || ':' || source_id || '->' || target_id || ':' || relation_type || ':' || weight::text, ',' ORDER BY id)) FROM pub_neural.neural_edges;")
SNAP_AFTER_SOURCES=$(docker exec -i "${CONTAINER_NAME}" psql -U postgres -d postgres -t -c "SELECT md5(string_agg(id::text || ':' || repository || ':' || file_path || ':' || file_sha256, ',' ORDER BY id)) FROM pub_neural.neural_sources;")
SNAP_AFTER_EVIDENCE=$(docker exec -i "${CONTAINER_NAME}" psql -U postgres -d postgres -t -c "SELECT md5(string_agg(id::text || ':' || source_id::text || ':' || content_hash, ',' ORDER BY id)) FROM pub_neural.neural_evidence;")
SNAP_AFTER_FTS=$(docker exec -i "${CONTAINER_NAME}" psql -U postgres -d postgres -t -c "SELECT md5(string_agg(id || ':' || language_config::text || ':' || tsv_document::text, ',' ORDER BY id)) FROM pub_neural.neural_fts;")
AFTER_CHK=$(docker exec -i "${CONTAINER_NAME}" psql -U postgres -d postgres -t -c "SELECT COALESCE((SELECT last_processed_global_sequence FROM pub_neural.neural_projection_checkpoints WHERE projector_name = 'graph_projector'), 0);")
AFTER_CHK=$(echo "${AFTER_CHK}" | tr -d '[:space:]')

if [ "$SNAP_BEFORE_NODES" != "$SNAP_AFTER_NODES" ] || [ "$SNAP_BEFORE_EDGES" != "$SNAP_AFTER_EDGES" ] || \
   [ "$SNAP_BEFORE_SOURCES" != "$SNAP_AFTER_SOURCES" ] || [ "$SNAP_BEFORE_EVIDENCE" != "$SNAP_AFTER_EVIDENCE" ] || \
   [ "$SNAP_BEFORE_FTS" != "$SNAP_AFTER_FTS" ] || [ "$BEFORE_CHK" != "$AFTER_CHK" ]; then
    echo "FATAL: Inconsistent / partially-committed state found after crash!"
    echo "SNAP_NODES: before=$SNAP_BEFORE_NODES after=$SNAP_AFTER_NODES"
    echo "SNAP_EDGES: before=$SNAP_BEFORE_EDGES after=$SNAP_AFTER_EDGES"
    echo "Checkpoint: before=$BEFORE_CHK after=$AFTER_CHK"
    exit 1
fi
echo "Verified: SNAPSHOT_BEFORE_CRASH == SNAPSHOT_AFTER_ROLLBACK across all projections and checkpoints."

# 6. Re-execute run_projector without test pause and prove clean convergence to sequence 2
RECONVERGE_RES=$(docker exec -i "${CONTAINER_NAME}" psql -U postgres -d postgres -t -c "
SELECT status FROM pub_neural.run_projector('graph_projector', 1, 2);
")

if [ "$(echo "${RECONVERGE_RES}" | tr -d '[:space:]')" != "HEALTHY" ]; then
    echo "FATAL: run_projector failed to cleanly reconverge after crash!"
    exit 1
fi
echo "Verified: run_projector cleanly reconverged to HEALTHY after crash recovery."

echo "=== [VERIFICATION] Negative Test Runner Check ==="
# Verify that psql aborts with non-zero exit code on syntax/assertion error
if docker exec -i "${CONTAINER_NAME}" psql -U postgres -d postgres -v ON_ERROR_STOP=1 -c "DO \$\$ BEGIN RAISE EXCEPTION 'TEST_INTENTIONAL_FAILURE'; END \$\$;" >/dev/null 2>&1; then
    echo "FATAL: Test runner failed to catch error (zero exit code on failure)!"
    exit 1
else
    echo "Negative test runner check passed (non-zero exit on error verified)."
fi

echo "=================================================="
echo "ALL PROJECTOR V0.1 ADVERSARIAL TESTS PASSED!"
echo "=================================================="
