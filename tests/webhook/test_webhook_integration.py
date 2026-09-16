import os
import json
import hmac
import hashlib
import uuid
import time
import subprocess
import pytest
import psycopg2
from fastapi.testclient import TestClient
import importlib

# Repository mapping is defined in src.ingestion.scout.AUTHORIZED_REPOSITORIES
# We'll import the FastAPI app after setting environment variables.

# Docker image and container settings
POSTGRES_IMAGE = "pgvector/pgvector:pg16"
POSTGRES_PASSWORD = "testpass"
POSTGRES_USER = "pub_neural_app"
POSTGRES_DB = "pub_neural"
POSTGRES_PORT = None  # placeholder, will be set after container start
CONTAINER_NAME = f"pub_neural_test_{uuid.uuid4().hex[:8]}"

# Environment variables required by webhook
WEBHOOK_SECRET = "test_webhook_secret"
ACTOR_ID = "webhook_observer"
MACHINE_SECRET = "machine_secret"

# Helper to compute HMAC signature header
def compute_signature(secret: str, body: bytes) -> str:
    mac = hmac.new(secret.encode(), msg=body, digestmod=hashlib.sha256)
    return f"sha256={mac.hexdigest()}"

# Fixture: start disposable PostgreSQL container
@pytest.fixture(scope="session")
def postgres_container():
    # Pull image (if not present)
    subprocess.run(["docker", "pull", POSTGRES_IMAGE], check=True, stdout=subprocess.DEVNULL)
    # Run container
    run_cmd = [
        "docker", "run", "--rm", "-d",
        "--name", CONTAINER_NAME,
        "-e", f"POSTGRES_PASSWORD={POSTGRES_PASSWORD}",
        "-e", f"POSTGRES_USER={POSTGRES_USER}",
        "-e", f"POSTGRES_DB={POSTGRES_DB}",
        "-p", "0:5432",
        POSTGRES_IMAGE,
    ]
    # Ensure no stale container with the same name exists
    subprocess.run(["docker", "rm", "-f", CONTAINER_NAME], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(run_cmd, check=True, stdout=subprocess.DEVNULL)
    # Retrieve the dynamically allocated host port
    port_output = subprocess.check_output(["docker", "port", CONTAINER_NAME, "5432"], text=True).strip()
    POSTGRES_PORT = port_output.split(":")[-1]
    # Wait for DB to become ready (simple connect loop)
    db_url = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@localhost:{POSTGRES_PORT}/{POSTGRES_DB}"
    for _ in range(30):
        try:
            conn = psycopg2.connect(db_url)
            conn.close()
            break
        except Exception:
            time.sleep(1)
    else:
        raise RuntimeError("PostgreSQL container did not become ready in time")
    # Copy migration files into the container
    migrations_path = os.path.abspath("migrations/0001_initial_v0_schema.sql")
    projector_path = os.path.abspath("src/projector_engine.sql")
    subprocess.run(["docker", "cp", migrations_path, f"{CONTAINER_NAME}:/tmp/0001_initial_v0_schema.sql"], check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["docker", "cp", projector_path, f"{CONTAINER_NAME}:/tmp/src_projector_engine.sql"], check=True, stdout=subprocess.DEVNULL)
    # Ensure a clean schema (some images may have pre‑seeded data)
    subprocess.run([
        "docker", "exec", CONTAINER_NAME,
        "psql", "-U", POSTGRES_USER, "-d", POSTGRES_DB,
        "-c", "DROP SCHEMA IF EXISTS pub_neural CASCADE;"
    ], check=True, stdout=subprocess.DEVNULL)
    # Set required PostgreSQL setting for migration
    subprocess.run([
        "docker", "exec", CONTAINER_NAME,
        "psql", "-U", POSTGRES_USER, "-d", POSTGRES_DB,
        "-c", "ALTER DATABASE \"pub_neural\" SET pub_neural.bootstrap_ceo_credential_hash = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa';"
    ], check=True, stdout=subprocess.DEVNULL)
    # Apply migrations inside the container using psql
    subprocess.run([
        "docker", "exec", CONTAINER_NAME,
        "psql", "-U", POSTGRES_USER, "-d", POSTGRES_DB,
        "-f", "/tmp/0001_initial_v0_schema.sql"
    ], check=True, stdout=subprocess.DEVNULL)
    # Create idempotency table required by tests
    # Create idempotency table required by tests
    subprocess.run([
        "docker", "exec", CONTAINER_NAME,
        "psql", "-U", POSTGRES_USER, "-d", POSTGRES_DB,
        "-c", "CREATE TABLE IF NOT EXISTS pub_neural.idempotency (idempotency_key TEXT PRIMARY KEY, resulting_event_id UUID, request_hash TEXT, response_payload JSONB);"
    ], check=True, stdout=subprocess.DEVNULL)
    subprocess.run([
        "docker", "exec", CONTAINER_NAME,
        "psql", "-U", POSTGRES_USER, "-d", POSTGRES_DB,
        "-c", "INSERT INTO pub_neural.trusted_actors (actor_id, actor_role, db_role, authorized_trust_zones, authorized_projects, credential_identity, is_active, created_at, originating_event_id) VALUES ('webhook_observer','INGESTOR','pub_neural_app', ARRAY['tz_internal_holding']::TEXT[], ARRAY['pub-ecom','pub-neural','holding-core']::TEXT[], 'b23fa4967e8e92546f16e79b1402708125e5a53e7dc55a81febe3e7c2de779cf', TRUE, CURRENT_TIMESTAMP, '0191e4f0-0000-7000-8000-000000000001');"
    ], check=True, stdout=subprocess.DEVNULL)
    subprocess.run([
        "docker", "exec", CONTAINER_NAME,
        "psql", "-U", POSTGRES_USER, "-d", POSTGRES_DB,
        "-c", "SELECT 1 FROM pub_neural.trusted_actors WHERE actor_id='webhook_observer';"
    ], check=True, stdout=subprocess.DEVNULL)
    subprocess.run([
        "docker", "exec", CONTAINER_NAME,
        "psql", "-U", POSTGRES_USER, "-d", POSTGRES_DB,
        "-f", "/tmp/src_projector_engine.sql"
    ], check=True, stdout=subprocess.DEVNULL)
    yield db_url
    # Stop container
    subprocess.run(["docker", "rm", "-f", CONTAINER_NAME], check=True, stdout=subprocess.DEVNULL)

# Fixture: FastAPI TestClient with environment set
@pytest.fixture(scope="function")
def client(postgres_container):
    os.environ["PUB_NEURAL_DB_URL"] = postgres_container
    os.environ["PUB_NEURAL_ACTOR_ID"] = ACTOR_ID
    os.environ["PUB_NEURAL_MACHINE_SECRET"] = MACHINE_SECRET
    os.environ["GITHUB_WEBHOOK_SECRET"] = WEBHOOK_SECRET
    from src.webhook import app
    return TestClient(app)

# Helper to send a webhook payload
def send_webhook(client, payload: dict, delivery_id: str, valid_sig: bool = True, extra_headers=None):
    raw_body = json.dumps(payload).encode()
    signature = compute_signature(WEBHOOK_SECRET, raw_body) if valid_sig else "sha256=invalid"
    headers = {
        "X-Hub-Signature-256": signature,
        "X-GitHub-Delivery": delivery_id,
        "Content-Type": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)
    return client.post("/github/webhook", data=raw_body, headers=headers)

class _BasePayloadDict(dict):
    def __copy__(self):
        return json.loads(json.dumps(self))
    def copy(self):
        return json.loads(json.dumps(self))

BASE_PAYLOAD = {
    "repository": {"full_name": "pubcore/pub-ecom"},
    "ref": "refs/heads/main",
    "after": "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
    "hook_id": 12345,
    "sender": {"login": "external_user"},
    "event": "push",
}

import copy
def get_payload():
    return copy.deepcopy(BASE_PAYLOAD)

@pytest.mark.parametrize("repo,project,zone", [
    ("pubcore/pub-ecom", "pub-ecom", "tz_internal_holding"),
    ("pubcore/pub-neural", "pub-neural", "tz_internal_holding"),
    ("pubcore/holding-governance", "holding-core", "tz_internal_holding"),
])
def test_valid_repository_scopes(client, postgres_container, repo, project, zone):
    payload = get_payload()
    payload["repository"]["full_name"] = repo
    delivery_id = str(uuid.uuid4())
    resp = send_webhook(client, payload, delivery_id)
    assert resp.status_code == 202
    conn = psycopg2.connect(postgres_container)
    cur = conn.cursor()
    cur.execute(
        "SELECT resulting_event_id FROM pub_neural.neural_idempotency_records WHERE idempotency_key = %s",
        (f"github_observation:{delivery_id}",)
    )
    row = cur.fetchone()
    assert row is not None, "Idempotency record missing"
    event_id = row[0]
    cur.execute("SELECT payload FROM pub_neural.neural_events WHERE id = %s", (event_id,))
    stored = cur.fetchone()[0]
    conn.close()
    assert stored["project_id"] == project
    assert stored["trust_zone"] == zone
    minimal = stored["payload"]
    assert minimal["ref"] == payload["ref"]
    assert minimal["sha"] == payload["after"]
    assert isinstance(minimal["details"], dict)

def test_unknown_repository(client, postgres_container):
    payload = get_payload()
    payload["repository"]["full_name"] = "unknown/repo"
    delivery_id = str(uuid.uuid4())
    resp = send_webhook(client, payload, delivery_id)
    assert resp.status_code == 403
    conn = psycopg2.connect(postgres_container)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pub_neural.idempotency WHERE idempotency_key = %s", (f"github_observation:{delivery_id}",))
    assert cur.fetchone() is None
    conn.close()

def test_invalid_hmac(client, postgres_container):
    payload = get_payload()
    delivery_id = str(uuid.uuid4())
    resp = send_webhook(client, payload, delivery_id, valid_sig=False)
    assert resp.status_code == 401
    conn = psycopg2.connect(postgres_container)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pub_neural.idempotency WHERE idempotency_key = %s", (f"github_observation:{delivery_id}",))
    assert cur.fetchone() is None
    conn.close()

def test_missing_delivery_id(client, postgres_container):
    payload = get_payload()
    raw_body = json.dumps(payload).encode()
    signature = compute_signature(WEBHOOK_SECRET, raw_body)
    resp = client.post("/github/webhook", data=raw_body, headers={"X-Hub-Signature-256": signature})
    assert resp.status_code == 400

def test_sequential_replay(client, postgres_container):
    payload = get_payload()
    delivery_id = str(uuid.uuid4())
    resp1 = send_webhook(client, payload, delivery_id)
    assert resp1.status_code == 202
    resp2 = send_webhook(client, payload, delivery_id)
    assert resp2.status_code == 200
    conn = psycopg2.connect(postgres_container)
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM pub_neural.neural_events WHERE payload->'provenance'->>'delivery_id' = %s",
        (delivery_id,)
    )
    count = cur.fetchone()[0]
    conn.close()
    assert count == 1

def test_distinct_delivery_creates_new_event(client, postgres_container):
    payload = get_payload()
    d1 = str(uuid.uuid4())
    d2 = str(uuid.uuid4())
    resp1 = send_webhook(client, payload, d1)
    resp2 = send_webhook(client, payload, d2)
    assert resp1.status_code == 202
    assert resp2.status_code == 202
    conn = psycopg2.connect(postgres_container)
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM pub_neural.neural_events WHERE payload->'provenance'->>'delivery_id' IN (%s, %s)",
        (d1, d2)
    )
    count = cur.fetchone()[0]
    conn.close()
    assert count == 2

def test_provenance_hash(client, postgres_container):
    payload = get_payload()
    delivery_id = str(uuid.uuid4())
    raw_body = json.dumps(payload).encode()
    signature = compute_signature(WEBHOOK_SECRET, raw_body)
    resp = client.post(
        "/github/webhook",
        data=raw_body,
        headers={
            "X-Hub-Signature-256": signature,
            "X-GitHub-Delivery": delivery_id,
            "Content-Type": "application/json",
        },
    )
    assert resp.status_code == 202
    conn = psycopg2.connect(postgres_container)
    cur = conn.cursor()
    cur.execute(
        "SELECT payload FROM pub_neural.neural_events WHERE payload->'provenance'->>'delivery_id' = %s",
        (delivery_id,)
    )
    stored = cur.fetchone()[0]
    conn.close()
    expected_hash = hashlib.sha256(raw_body).hexdigest()
    assert stored["provenance"]["payload_hash"] == expected_hash

def test_no_promotion_events(client, postgres_container):
    payload = get_payload()
    delivery_id = str(uuid.uuid4())
    resp = send_webhook(client, payload, delivery_id)
    assert resp.status_code == 202
    conn = psycopg2.connect(postgres_container)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM pub_neural.neural_events WHERE event_type = 'KNOWLEDGE_CANDIDATE_CREATED'")
    count = cur.fetchone()[0]
    conn.close()
    assert count == 0

def test_authorized_internal_actor(client, postgres_container):
    payload = get_payload()
    delivery_id = str(uuid.uuid4())
    resp = send_webhook(client, payload, delivery_id)
    assert resp.status_code == 202
def test_unauthorized_internal_actor(postgres_container):
    # Set an internal actor that is not present in trusted_actors
    os.environ["PUB_NEURAL_ACTOR_ID"] = "untrusted_actor"
    os.environ["PUB_NEURAL_DB_URL"] = postgres_container
    os.environ["PUB_NEURAL_MACHINE_SECRET"] = MACHINE_SECRET
    os.environ["GITHUB_WEBHOOK_SECRET"] = WEBHOOK_SECRET
    from src.webhook import app
    client = TestClient(app)
    payload = get_payload()
    delivery_id = str(uuid.uuid4())
    resp = send_webhook(client, payload, delivery_id)
    assert resp.status_code == 403
    # Verify no canonical event was created
    conn = psycopg2.connect(postgres_container)
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM pub_neural.neural_events WHERE payload->'provenance'->>'delivery_id' = %s",
        (delivery_id,)
    )
    count = cur.fetchone()[0]
    cur.execute(
        "SELECT 1 FROM pub_neural.neural_idempotency_records WHERE idempotency_key = %s",
        (f"github_observation:{delivery_id}",)
    )
    idemp = cur.fetchone()
    conn.close()
    assert count == 0
    assert idemp is None


# =============================================================================
# V0.2 TESTS: REPOSITORY OBSERVATION REDUCER & SOURCE LINKAGE
# =============================================================================

def test_repository_observed_reduction_and_durable_projection(client, postgres_container):
    """
    V0.2-01: Proves:
      1. Webhook persists REPOSITORY_OBSERVED canonical event.
      2. reduce_event(event_id) returns 'SUPPORTED'.
      3. pub_neural.neural_repository_observations stores durable projection.
      4. Preserves: repository, project_id, trust_zone, observation_id, delivery_id, payload_hash, observed_at.
      5. NO neural_nodes are created (observation != knowledge).
      6. NO promotion events (KNOWLEDGE_CANDIDATE_CREATED, etc.) are emitted.
    """
    payload = get_payload()
    payload["repository"]["full_name"] = "pubcore/pub-ecom"
    payload["head_commit"] = {
        "id": "11223344556677889900aabbccddeeff00112233",
        "message": "feat: test durable observation linkage",
        "author": {"name": "Test Engineer"}
    }
    delivery_id = str(uuid.uuid4())
    resp = send_webhook(client, payload, delivery_id)
    assert resp.status_code == 202

    conn = psycopg2.connect(postgres_container)
    cur = conn.cursor()

    # Retrieve event ID
    cur.execute(
        "SELECT resulting_event_id FROM pub_neural.neural_idempotency_records WHERE idempotency_key = %s",
        (f"github_observation:{delivery_id}",)
    )
    event_id = cur.fetchone()[0]

    # Count neural_nodes before reduction
    cur.execute("SELECT COUNT(*) FROM pub_neural.neural_nodes;")
    nodes_count_before = cur.fetchone()[0]

    # 1. Reduction test
    cur.execute("SELECT pub_neural.reduce_event(%s::uuid);", (str(event_id),))
    reduction_result = cur.fetchone()[0]
    assert reduction_result == "SUPPORTED", f"Expected SUPPORTED, got {reduction_result}"
    conn.commit()

    # 2. Durable projection verification
    cur.execute(
        """
        SELECT observation_id, event_id, repository, source, project_id, trust_zone,
               delivery_id, payload_hash, observed_at, ref, sha, details
        FROM pub_neural.neural_repository_observations
        WHERE delivery_id = %s;
        """,
        (delivery_id,)
    )
    obs = cur.fetchone()
    assert obs is not None, "Observation projection missing in neural_repository_observations"

    obs_id, obs_ev_id, repo, source, proj_id, zone, d_id, p_hash, obs_at, ref, sha, details = obs
    assert str(obs_ev_id) == str(event_id)
    assert repo == "pubcore/pub-ecom"
    assert source == "github"
    assert proj_id == "pub-ecom"
    assert zone == "tz_internal_holding"
    assert d_id == delivery_id
    assert p_hash is not None and len(p_hash) == 64
    assert obs_at is not None
    assert ref == payload["ref"]
    assert sha == payload["after"]
    assert details.get("commit_message") == "feat: test durable observation linkage"

    # 3. Invariant check: NO knowledge node created
    cur.execute("SELECT COUNT(*) FROM pub_neural.neural_nodes;")
    nodes_count_after = cur.fetchone()[0]
    assert nodes_count_after == nodes_count_before, "Observation created unauthorized neural_nodes!"

    # 4. Invariant check: NO promotion events created
    cur.execute(
        """
        SELECT COUNT(*) FROM pub_neural.neural_events
        WHERE event_type IN (
            'KNOWLEDGE_CANDIDATE_CREATED',
            'KNOWLEDGE_VALIDATED',
            'PROMOTION_PROPOSED',
            'DECISION_RATIFIED',
            'GOVERNANCE_RULE_RATIFIED'
        );
        """
    )
    promotion_events_count = cur.fetchone()[0]
    assert promotion_events_count == 0, "Observation triggered unauthorized promotion events!"

    conn.close()


def test_repository_observed_replay_idempotency(client, postgres_container):
    """
    V0.2-02: Proves:
      1. Reducing the exact same REPOSITORY_OBSERVED event twice returns 'SUPPORTED'.
      2. No duplicate row created in neural_repository_observations (unique on delivery_id).
    """
    payload = get_payload()
    payload["repository"]["full_name"] = "pubcore/pub-neural"
    delivery_id = str(uuid.uuid4())
    resp = send_webhook(client, payload, delivery_id)
    assert resp.status_code == 202

    conn = psycopg2.connect(postgres_container)
    cur = conn.cursor()

    cur.execute(
        "SELECT resulting_event_id FROM pub_neural.neural_idempotency_records WHERE idempotency_key = %s",
        (f"github_observation:{delivery_id}",)
    )
    event_id = cur.fetchone()[0]

    # First reduction
    cur.execute("SELECT pub_neural.reduce_event(%s::uuid);", (str(event_id),))
    res1 = cur.fetchone()[0]
    assert res1 == "SUPPORTED"
    conn.commit()

    # Second reduction (replay)
    cur.execute("SELECT pub_neural.reduce_event(%s::uuid);", (str(event_id),))
    res2 = cur.fetchone()[0]
    assert res2 == "SUPPORTED"
    conn.commit()

    # Verify exactly 1 observation row exists
    cur.execute(
        "SELECT COUNT(*) FROM pub_neural.neural_repository_observations WHERE delivery_id = %s;",
        (delivery_id,)
    )
    count = cur.fetchone()[0]
    assert count == 1, f"Expected exactly 1 projection row on replay, found {count}"

    conn.close()


def test_repository_observed_malformed_guard(postgres_container):
    """
    V0.2-03: Proves:
      Missing repository or delivery_id produces MALFORMED without crashing.
    """
    conn = psycopg2.connect(postgres_container)
    cur = conn.cursor()

    # Missing repository
    cur.execute(
        """
        SELECT pub_neural.reduce_event((
            '0191e4f0-0099-7000-8000-000000000001'::uuid,
            99999,
            'REPOSITORY_OBSERVED',
            1, 1, 'v1', 'stream:test', 1, 'webhook_observer', 'INGESTOR'::pub_neural.neural_actor_role,
            '{"project_id": "pub-ecom", "provenance": {"delivery_id": "d-1", "payload_hash": "abc"}}'::jsonb,
            NULL, CURRENT_TIMESTAMP
        )::pub_neural.neural_events);
        """
    )
    res = cur.fetchone()[0]
    assert res == "MALFORMED"

    # Missing delivery_id in provenance
    cur.execute(
        """
        SELECT pub_neural.reduce_event((
            '0191e4f0-0099-7000-8000-000000000002'::uuid,
            99998,
            'REPOSITORY_OBSERVED',
            1, 1, 'v1', 'stream:test', 2, 'webhook_observer', 'INGESTOR'::pub_neural.neural_actor_role,
            '{"repository": "pubcore/pub-ecom", "project_id": "pub-ecom", "provenance": {"payload_hash": "abc"}}'::jsonb,
            NULL, CURRENT_TIMESTAMP
        )::pub_neural.neural_events);
        """
    )
    res = cur.fetchone()[0]
    assert res == "MALFORMED"

    conn.close()
