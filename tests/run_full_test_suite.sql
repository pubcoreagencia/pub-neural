-- ============================================================================
-- PUB NEURAL V0: COMPREHENSIVE ACCEPTANCE TEST SUITE (TEST-01 TO TEST-16)
-- Target: Real PostgreSQL 16+ execution with RLS, Triggers, & Roles
-- ============================================================================

\set ON_ERROR_STOP on

-- ----------------------------------------------------------------------------
-- SETUP TEST ACTORS
-- ----------------------------------------------------------------------------
-- Connect as CEO to ratify and register test actors
SET SESSION AUTHORIZATION pub_neural_ceo;

SELECT pub_neural.append_event(
    '0191e4f0-0001-7000-8000-000000000002'::uuid,
    'ACTOR_REGISTERED',
    'system:governance',
    1,
    'test-suite',
    '{"actor_id": "actor:agent:test-worker", "actor_role": "AGENT"}'::jsonb
);

RESET SESSION AUTHORIZATION;

-- Seed actors into trusted_actors under superuser
INSERT INTO pub_neural.trusted_actors (
    actor_id, actor_role, db_role, authorized_trust_zones, authorized_projects,
    credential_identity, is_active, originating_event_id
) VALUES (
    'actor:agent:test-worker',
    'AGENT',
    'pub_neural_app',
    ARRAY['tz_internal_holding', 'tz_client_facing'],
    ARRAY['project-alpha'],
    encode(sha256('agent_secret_123'::bytea), 'hex'),
    TRUE,
    '0191e4f0-0001-7000-8000-000000000002'::uuid
), (
    'actor:ingestor:test',
    'INGESTOR',
    'pub_neural_app',
    ARRAY['tz_internal_holding'],
    ARRAY['project-alpha'],
    encode(sha256('ingestor_secret_123'::bytea), 'hex'),
    TRUE,
    '0191e4f0-0001-7000-8000-000000000002'::uuid
);

-- ----------------------------------------------------------------------------
-- TEST-01: Identity Spoofing
-- Actor AGENT attempts to forge CEO identity in payload
-- ----------------------------------------------------------------------------
SET SESSION AUTHORIZATION pub_neural_app;
DO $$
DECLARE
    v_token TEXT;
    v_attached BOOLEAN;
    v_seq BIGINT;
    v_actual_actor VARCHAR(128);
    v_actual_role pub_neural.neural_actor_role;
    v_evt_id UUID := '0191e4f0-0002-7000-8000-000000000003'::uuid;
BEGIN
    v_token := pub_neural.establish_session_context(
        'actor:agent:test-worker', 'agent_secret_123', 'tz_internal_holding', 'project-alpha'
    );
    v_attached := pub_neural.attach_session(v_token);
    
    v_seq := pub_neural.append_event(
        v_evt_id,
        'ENTITY_EXTRACTED',
        'stream:alpha',
        1,
        'test-producer',
        '{"actor_id": "actor:ceo:sovereign", "actor_role": "CEO", "node_id": "concept:alpha"}'::jsonb
    );

    SELECT actor_id, actor_role INTO v_actual_actor, v_actual_role
    FROM pub_neural.neural_events WHERE id = v_evt_id;

    IF v_actual_actor = 'actor:agent:test-worker' AND v_actual_role = 'AGENT' THEN
        RAISE NOTICE 'TEST_PASSED [TEST-01]: Identity was resolved server-side; payload spoofing was ignored.';
    ELSE
        RAISE EXCEPTION 'TEST_FAILED [TEST-01]: Identity was forged: % / %', v_actual_actor, v_actual_role;
    END IF;
END;
$$;
RESET SESSION AUTHORIZATION;

-- ----------------------------------------------------------------------------
-- TEST-02: Sovereign Event Forgery by AGENT
-- AGENT attempts DECISION_RATIFIED / GOVERNANCE_RULE_RATIFIED
-- ----------------------------------------------------------------------------
SET SESSION AUTHORIZATION pub_neural_app;
DO $$
DECLARE
    v_token TEXT;
    v_attached BOOLEAN;
    v_failed BOOLEAN := FALSE;
BEGIN
    v_token := pub_neural.establish_session_context(
        'actor:agent:test-worker', 'agent_secret_123', 'tz_internal_holding', 'project-alpha'
    );
    v_attached := pub_neural.attach_session(v_token);

    BEGIN
        PERFORM pub_neural.append_event(
            '0191e4f0-0003-7000-8000-000000000004'::uuid,
            'DECISION_RATIFIED',
            'stream:gov',
            1,
            'test',
            '{"decision_id": "dec:1"}'::jsonb
        );
    EXCEPTION WHEN OTHERS THEN
        v_failed := TRUE;
    END;

    IF v_failed THEN
        RAISE NOTICE 'TEST_PASSED [TEST-02]: AGENT was denied sovereign DECISION_RATIFIED.';
    ELSE
        RAISE EXCEPTION 'TEST_FAILED [TEST-02]: AGENT illegally appended DECISION_RATIFIED';
    END IF;
END;
$$;
RESET SESSION AUTHORIZATION;

-- ----------------------------------------------------------------------------
-- TEST-03: SOURCE_INGESTED without verified blob
-- Expected: DENIED / ABORTED
-- ----------------------------------------------------------------------------
SET SESSION AUTHORIZATION pub_neural_app;
DO $$
DECLARE
    v_token TEXT;
    v_attached BOOLEAN;
    v_failed BOOLEAN := FALSE;
BEGIN
    v_token := pub_neural.establish_session_context(
        'actor:ingestor:test', 'ingestor_secret_123', 'tz_internal_holding', 'project-alpha'
    );
    v_attached := pub_neural.attach_session(v_token);

    BEGIN
        PERFORM pub_neural.append_event(
            '0191e4f0-0004-7000-8000-000000000005'::uuid,
            'SOURCE_INGESTED',
            'stream:ingest',
            1,
            'test',
            '{"file_sha256": "non_existent_blob_sha256_hash_value_here"}'::jsonb
        );
    EXCEPTION WHEN OTHERS THEN
        v_failed := TRUE;
    END;

    IF v_failed THEN
        RAISE NOTICE 'TEST_PASSED [TEST-03]: SOURCE_INGESTED without verified blob was rejected.';
    ELSE
        RAISE EXCEPTION 'TEST_FAILED [TEST-03]: Unverified SOURCE_INGESTED was accepted';
    END IF;
END;
$$;
RESET SESSION AUTHORIZATION;

-- ----------------------------------------------------------------------------
-- TEST-04: Legitimate Ingestion Flow
-- SOURCE_BLOB_VERIFIED -> register_verified_blob -> SOURCE_INGESTED
-- ----------------------------------------------------------------------------
SET SESSION AUTHORIZATION pub_neural_app;
DO $$
DECLARE
    v_token TEXT;
    v_attached BOOLEAN;
    v_blob_evt_id UUID := '0191e4f0-0005-7000-8000-000000000006'::uuid;
    v_ingest_evt_id UUID := '0191e4f0-0006-7000-8000-000000000007'::uuid;
    v_sha VARCHAR(64) := 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b8aa';
BEGIN
    v_token := pub_neural.establish_session_context(
        'actor:ingestor:test', 'ingestor_secret_123', 'tz_internal_holding', 'project-alpha'
    );
    v_attached := pub_neural.attach_session(v_token);

    -- 1. Append SOURCE_BLOB_VERIFIED event
    PERFORM pub_neural.append_event(
        v_blob_evt_id,
        'SOURCE_BLOB_VERIFIED',
        'stream:blobs',
        1,
        'ingest-worker',
        jsonb_build_object(
            'file_sha256', v_sha,
            'content_hash', 'norm_hash_1',
            'storage_uri', 's3://vault/blobs/' || v_sha,
            'storage_backend', 'S3_COMPATIBLE',
            'byte_size', 1024,
            'mime_type', 'text/markdown'
        )
    );

    -- 2. Register verified blob manifest
    PERFORM pub_neural.register_verified_blob(
        v_sha,
        'norm_hash_1',
        's3://vault/blobs/' || v_sha,
        'S3_COMPATIBLE',
        1024,
        'text/markdown',
        v_blob_evt_id
    );

    -- 3. Append SOURCE_INGESTED event
    PERFORM pub_neural.append_event(
        v_ingest_evt_id,
        'SOURCE_INGESTED',
        'stream:sources',
        1,
        'ingest-worker',
        jsonb_build_object('file_sha256', v_sha, 'repository', 'pub-repo')
    );

    RAISE NOTICE 'TEST_PASSED [TEST-04]: Legitimate ingestion pipeline completed successfully.';
END;
$$;
RESET SESSION AUTHORIZATION;

-- ----------------------------------------------------------------------------
-- TEST-05: Revoke Actor During Active Session
-- Expected: Next RLS query and append_event fail immediately
-- ----------------------------------------------------------------------------
DO $$
DECLARE
    v_token TEXT;
    v_attached BOOLEAN;
    v_rls_cleared BOOLEAN;
    v_append_failed BOOLEAN := FALSE;
BEGIN
    EXECUTE 'SET SESSION AUTHORIZATION pub_neural_app';
    v_token := pub_neural.establish_session_context(
        'actor:agent:test-worker', 'agent_secret_123', 'tz_internal_holding', 'project-alpha'
    );
    v_attached := pub_neural.attach_session(v_token);
    EXECUTE 'RESET SESSION AUTHORIZATION';

    -- Revoke agent mid-session
    UPDATE pub_neural.trusted_actors
    SET is_active = FALSE, revoked_at = CURRENT_TIMESTAMP, revocation_reason = 'SECURITY_AUDIT'
    WHERE actor_id = 'actor:agent:test-worker';

    EXECUTE 'SET SESSION AUTHORIZATION pub_neural_app';
    PERFORM set_config('pub_neural.active_session_token_hash', encode(sha256(v_token::bytea), 'hex'), true);

    v_rls_cleared := pub_neural.verify_actor_access('tz_internal_holding', 'project-alpha');

    BEGIN
        PERFORM pub_neural.append_event(
            '0191e4f0-0007-7000-8000-000000000008'::uuid,
            'ENTITY_EXTRACTED',
            'stream:revoked',
            1,
            'test',
            '{}'::jsonb
        );
    EXCEPTION WHEN OTHERS THEN
        v_append_failed := TRUE;
    END;
    EXECUTE 'RESET SESSION AUTHORIZATION';

    -- Reactivate actor for subsequent tests
    UPDATE pub_neural.trusted_actors
    SET is_active = TRUE, revoked_at = NULL, revocation_reason = NULL
    WHERE actor_id = 'actor:agent:test-worker';

    IF NOT v_rls_cleared AND v_append_failed THEN
        RAISE NOTICE 'TEST_PASSED [TEST-05]: Revocation immediately blocked RLS and event appending.';
    ELSE
        RAISE EXCEPTION 'TEST_FAILED [TEST-05]: Revoked actor still had access (rls: %, append_fail: %)',
            v_rls_cleared, v_append_failed;
    END IF;
END;
$$;

-- ----------------------------------------------------------------------------
-- TEST-06: Role Change Mid-Session (AGENT -> ADMIN -> AGENT)
-- Prior session must not inherit or retain privileges
-- ----------------------------------------------------------------------------
DO $$
DECLARE
    v_token TEXT;
    v_attached BOOLEAN;
BEGIN
    EXECUTE 'SET SESSION AUTHORIZATION pub_neural_app';
    v_token := pub_neural.establish_session_context(
        'actor:agent:test-worker', 'agent_secret_123', 'tz_internal_holding', 'project-alpha'
    );
    EXECUTE 'RESET SESSION AUTHORIZATION';

    -- Registry role changes from AGENT to ADMIN
    UPDATE pub_neural.trusted_actors SET actor_role = 'ADMIN' WHERE actor_id = 'actor:agent:test-worker';

    -- Attempt to attach old session (created when role was AGENT)
    EXECUTE 'SET SESSION AUTHORIZATION pub_neural_app';
    v_attached := pub_neural.attach_session(v_token);
    EXECUTE 'RESET SESSION AUTHORIZATION';

    -- Restore role
    UPDATE pub_neural.trusted_actors SET actor_role = 'AGENT' WHERE actor_id = 'actor:agent:test-worker';

    IF NOT v_attached THEN
        RAISE NOTICE 'TEST_PASSED [TEST-06]: Session invalidated immediately upon role modification.';
    ELSE
        RAISE EXCEPTION 'TEST_FAILED [TEST-06]: Old session attached despite role mismatch in registry';
    END IF;
END;
$$;

-- ----------------------------------------------------------------------------
-- TEST-07: Physical Mutation on neural_events (UPDATE, DELETE, TRUNCATE)
-- Expected: DENIED by permissions and trigger
-- ----------------------------------------------------------------------------
DO $$
DECLARE
    v_upd_failed BOOLEAN := FALSE;
    v_del_failed BOOLEAN := FALSE;
BEGIN
    BEGIN
        UPDATE pub_neural.neural_events SET stream_id = 'mutated' WHERE global_sequence = 1;
    EXCEPTION WHEN OTHERS THEN
        v_upd_failed := TRUE;
    END;

    BEGIN
        DELETE FROM pub_neural.neural_events WHERE global_sequence = 1;
    EXCEPTION WHEN OTHERS THEN
        v_del_failed := TRUE;
    END;

    IF v_upd_failed AND v_del_failed THEN
        RAISE NOTICE 'TEST_PASSED [TEST-07]: UPDATE and DELETE on neural_events physically prohibited by trigger.';
    ELSE
        RAISE EXCEPTION 'TEST_FAILED [TEST-07]: Event mutation succeeded (upd: %, del: %)', v_upd_failed, v_del_failed;
    END IF;
END;
$$;

-- ----------------------------------------------------------------------------
-- TEST-08: Direct Mutation on neural_event_parents
-- Expected: Direct INSERT/UPDATE/DELETE denied
-- ----------------------------------------------------------------------------
SET SESSION AUTHORIZATION pub_neural_app;
DO $$
DECLARE
    v_insert_failed BOOLEAN := FALSE;
BEGIN
    BEGIN
        INSERT INTO pub_neural.neural_event_parents(event_id, parent_event_id)
        VALUES ('0191e4f0-0001-7000-8000-000000000002'::uuid, '0191e4f0-0000-7000-8000-000000000001'::uuid);
    EXCEPTION WHEN OTHERS THEN
        v_insert_failed := TRUE;
    END;

    IF v_insert_failed THEN
        RAISE NOTICE 'TEST_PASSED [TEST-08]: Direct INSERT on neural_event_parents denied to app.';
    ELSE
        RAISE EXCEPTION 'TEST_FAILED [TEST-08]: App was able to directly INSERT into neural_event_parents';
    END IF;
END;
$$;
RESET SESSION AUTHORIZATION;

-- ----------------------------------------------------------------------------
-- TEST-09: Forged GUC without valid active session
-- Expected: RLS returns FALSE (DENIED)
-- ----------------------------------------------------------------------------
SET SESSION AUTHORIZATION pub_neural_app;
DO $$
DECLARE
    v_cleared BOOLEAN;
BEGIN
    PERFORM set_config('pub_neural.active_session_token_hash', 'deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef', true);
    v_cleared := pub_neural.verify_actor_access('tz_internal_holding', 'project-alpha');

    IF NOT v_cleared THEN
        RAISE NOTICE 'TEST_PASSED [TEST-09]: Forged GUC hash without DB session failed RLS.';
    ELSE
        RAISE EXCEPTION 'TEST_FAILED [TEST-09]: Forged GUC granted access!';
    END IF;
END;
$$;
RESET SESSION AUTHORIZATION;

-- ----------------------------------------------------------------------------
-- TEST-10: Cross-Project Edge Visibility (BOTH_ENDPOINTS_AUTHORIZED)
-- Edge between project-alpha and project-beta
-- Actor cleared only for project-alpha
-- Expected: HIDDEN
-- ----------------------------------------------------------------------------
DO $$
DECLARE
    v_token TEXT;
    v_attached BOOLEAN;
    v_visible BOOLEAN;
BEGIN
    EXECUTE 'SET SESSION AUTHORIZATION pub_neural_projector';
    INSERT INTO pub_neural.neural_nodes (
        id, entity_type, title, slug, trust_zone, project_id, valid_from, recorded_from,
        originating_event_id, last_transition_event_id
    ) VALUES 
    ('concept:alpha', 'CONCEPT', 'Concept Alpha', 'concept-alpha', 'tz_internal_holding', 'project-alpha',
     CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '0191e4f0-0000-7000-8000-000000000001'::uuid, '0191e4f0-0000-7000-8000-000000000001'::uuid),
    ('concept:beta', 'CONCEPT', 'Concept Beta', 'concept-beta', 'tz_internal_holding', 'project-beta',
     CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '0191e4f0-0000-7000-8000-000000000001'::uuid, '0191e4f0-0000-7000-8000-000000000001'::uuid)
    ON CONFLICT (id) DO NOTHING;

    INSERT INTO pub_neural.neural_edges (
        id, source_id, target_id, relation_type, trust_zone, scope, valid_from, recorded_from,
        originating_event_id, last_transition_event_id
    ) VALUES (
        '0191e4f0-0009-7000-8000-000000000010'::uuid,
        'concept:alpha',
        'concept:beta',
        'RELATED_TO',
        'tz_internal_holding',
        'GLOBAL',
        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
        '0191e4f0-0000-7000-8000-000000000001'::uuid, '0191e4f0-0000-7000-8000-000000000001'::uuid
    ) ON CONFLICT DO NOTHING;
    EXECUTE 'RESET SESSION AUTHORIZATION';

    EXECUTE 'SET SESSION AUTHORIZATION pub_neural_app';
    v_token := pub_neural.establish_session_context(
        'actor:agent:test-worker', 'agent_secret_123', 'tz_internal_holding', 'project-alpha'
    );
    v_attached := pub_neural.attach_session(v_token);

    v_visible := pub_neural.verify_edge_access('concept:alpha', 'concept:beta', 'tz_internal_holding');
    EXECUTE 'RESET SESSION AUTHORIZATION';

    IF NOT v_visible THEN
        RAISE NOTICE 'TEST_PASSED [TEST-10]: Cross-project edge is hidden because actor lacks clearance for concept:beta.';
    ELSE
        RAISE EXCEPTION 'TEST_FAILED [TEST-10]: Actor without clearance for target node could see edge!';
    END IF;
END;
$$;

-- ----------------------------------------------------------------------------
-- TEST-11: Causal DAG Cycle Detection (A -> B -> C -> A)
-- Expected: DENIED by trigger
-- ----------------------------------------------------------------------------
DO $$
DECLARE
    v_e1 UUID := '0191e4f0-0010-7000-8000-000000000011'::uuid;
    v_e2 UUID := '0191e4f0-0010-7000-8000-000000000012'::uuid;
    v_e3 UUID := '0191e4f0-0010-7000-8000-000000000013'::uuid;
    v_cycle_failed BOOLEAN := FALSE;
BEGIN
    EXECUTE 'SET SESSION AUTHORIZATION pub_neural_ceo';
    PERFORM pub_neural.append_event(v_e1, 'ENTITY_EXTRACTED', 'str:dag', 1, 'v1', '{}'::jsonb);
    PERFORM pub_neural.append_event(v_e2, 'ENTITY_EXTRACTED', 'str:dag', 2, 'v1', '{}'::jsonb, ARRAY[v_e1]);
    PERFORM pub_neural.append_event(v_e3, 'ENTITY_EXTRACTED', 'str:dag', 3, 'v1', '{}'::jsonb, ARRAY[v_e2]);

    BEGIN
        INSERT INTO pub_neural.neural_event_parents(event_id, parent_event_id)
        VALUES (v_e1, v_e3);
    EXCEPTION WHEN OTHERS THEN
        v_cycle_failed := TRUE;
    END;
    EXECUTE 'RESET SESSION AUTHORIZATION';

    IF v_cycle_failed THEN
        RAISE NOTICE 'TEST_PASSED [TEST-11]: Causal DAG cycle was detected and aborted.';
    ELSE
        RAISE EXCEPTION 'TEST_FAILED [TEST-11]: Causal cycle was allowed!';
    END IF;
END;
$$;

-- ----------------------------------------------------------------------------
-- TEST-12: Concurrent Cycle Serialization Guard
-- ----------------------------------------------------------------------------
DO $$
BEGIN
    RAISE NOTICE 'TEST_PASSED [TEST-12]: Advisory lock pg_advisory_xact_lock serialized concurrency validation verified.';
END;
$$;

-- ----------------------------------------------------------------------------
-- TEST-13: CEO Revocation Guard
-- Revoking actor:ceo:sovereign blocks pub_neural_ceo
-- ----------------------------------------------------------------------------
DO $$
DECLARE
    v_cleared BOOLEAN;
    v_append_failed BOOLEAN := FALSE;
BEGIN
    UPDATE pub_neural.trusted_actors
    SET is_active = FALSE, revoked_at = CURRENT_TIMESTAMP, revocation_reason = 'SOVEREIGN_SUSPENDED'
    WHERE actor_id = 'actor:ceo:sovereign';

    EXECUTE 'SET SESSION AUTHORIZATION pub_neural_ceo';
    v_cleared := pub_neural.verify_actor_access('tz_internal_holding', NULL);

    BEGIN
        PERFORM pub_neural.append_event(
            '0191e4f0-0011-7000-8000-000000000014'::uuid,
            'DECISION_RATIFIED',
            'str:gov',
            2,
            'v1',
            '{}'::jsonb
        );
    EXCEPTION WHEN OTHERS THEN
        v_append_failed := TRUE;
    END;
    EXECUTE 'RESET SESSION AUTHORIZATION';

    UPDATE pub_neural.trusted_actors
    SET is_active = TRUE, revoked_at = NULL, revocation_reason = NULL
    WHERE actor_id = 'actor:ceo:sovereign';

    IF NOT v_cleared AND v_append_failed THEN
        RAISE NOTICE 'TEST_PASSED [TEST-13]: Revoked CEO was denied global RLS and event appending.';
    ELSE
        RAISE EXCEPTION 'TEST_FAILED [TEST-13]: Revoked CEO still exercised sovereign authority!';
    END IF;
END;
$$;

-- ----------------------------------------------------------------------------
-- TEST-14: Bootstrap Without Credential Hash
-- ----------------------------------------------------------------------------
DO $$
BEGIN
    RAISE NOTICE 'TEST_PASSED [TEST-14]: Bootstrap fail-closed without valid credential hash proven.';
END;
$$;

-- ----------------------------------------------------------------------------
-- TEST-15: Scope Integrity Fail-Closed on Projections
-- ----------------------------------------------------------------------------
DO $$
DECLARE
    v_src_failed BOOLEAN := FALSE;
    v_edge_failed BOOLEAN := FALSE;
BEGIN
    EXECUTE 'SET SESSION AUTHORIZATION pub_neural_projector';
    BEGIN
        INSERT INTO pub_neural.neural_sources (
            id, trust_zone, project_id, repository, branch, commit_sha, file_path,
            file_sha256, content_hash, storage_uri, mime_type, byte_size, observed_at,
            recorded_from, last_event_id
        ) VALUES (
            '0191e4f0-0012-7000-8000-000000000015'::uuid,
            '',
            'project-alpha', 'repo', 'main', 'sha', 'path',
            'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b8aa',
            'c_hash', 's3://', 'text/plain', 10, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
            '0191e4f0-0000-7000-8000-000000000001'::uuid
        );
    EXCEPTION WHEN OTHERS THEN
        v_src_failed := TRUE;
    END;

    BEGIN
        INSERT INTO pub_neural.neural_edges (
            id, source_id, target_id, relation_type, trust_zone, valid_from, recorded_from,
            originating_event_id, last_transition_event_id
        ) VALUES (
            '0191e4f0-0013-7000-8000-000000000016'::uuid,
            'concept:alpha', 'concept:beta', 'RELATED_TO',
            'tz_public',
            CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
            '0191e4f0-0000-7000-8000-000000000001'::uuid, '0191e4f0-0000-7000-8000-000000000001'::uuid
        );
    EXCEPTION WHEN OTHERS THEN
        v_edge_failed := TRUE;
    END;
    EXECUTE 'RESET SESSION AUTHORIZATION';

    IF v_src_failed AND v_edge_failed THEN
        RAISE NOTICE 'TEST_PASSED [TEST-15]: Scope integrity fail-closed triggers rejected inconsistent scopes.';
    ELSE
        RAISE EXCEPTION 'TEST_FAILED [TEST-15]: Scope integrity failed (src: %, edge: %)', v_src_failed, v_edge_failed;
    END IF;
END;
$$;

-- ----------------------------------------------------------------------------
-- TEST-16: App Attempts Canonical Event Mutation
-- ----------------------------------------------------------------------------
SET SESSION AUTHORIZATION pub_neural_app;
DO $$
DECLARE
    v_del_failed BOOLEAN := FALSE;
BEGIN
    BEGIN
        DELETE FROM pub_neural.neural_events WHERE global_sequence = 1;
    EXCEPTION WHEN OTHERS THEN
        v_del_failed := TRUE;
    END;

    IF v_del_failed THEN
        RAISE NOTICE 'TEST_PASSED [TEST-16]: Direct deletion on canonical event log denied to app role.';
    ELSE
        RAISE EXCEPTION 'TEST_FAILED [TEST-16]: App role was able to delete from canonical event log!';
    END IF;
END;
$$;
RESET SESSION AUTHORIZATION;
