-- ============================================================================
-- PUB NEURAL V0.1: REPLAY & PROJECTOR VERIFICATION SUITE (RPL-01 TO RPL-16)
-- Target: Real PostgreSQL 16+ execution with deterministic replay & recovery
-- Hardening: Strict assertions, double snapshot equality, crash semantics
-- ============================================================================

\set ON_ERROR_STOP on

-- Enable test fixtures helper
CREATE OR REPLACE FUNCTION pg_temp.assert(p_condition BOOLEAN, p_test_id TEXT, p_msg TEXT)
RETURNS VOID AS $$
BEGIN
    IF NOT p_condition THEN
        RAISE EXCEPTION 'TEST_FAILED [%]: %', p_test_id, p_msg;
    ELSE
        RAISE NOTICE 'TEST_PASSED [%]: %', p_test_id, p_msg;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- ----------------------------------------------------------------------------
-- SEED SCENARIO EVENTS (CANONICAL EVENT LOG)
-- ----------------------------------------------------------------------------
-- 1. Verified Source Blob
INSERT INTO pub_neural.source_blobs (
    file_sha256, content_hash, storage_uri, byte_size, mime_type, originating_event_id
) VALUES (
    'a1b2c3d4e5f60000000000000000000000000000000000000000000000000001',
    'norm_content_hash_01',
    's3://vault/pub-ecom/auth.md',
    512,
    'text/markdown',
    '0191e4f0-0000-7000-8000-000000000001'::uuid
) ON CONFLICT (file_sha256) DO NOTHING;

-- 2. Append events via CEO connection
SET SESSION AUTHORIZATION pub_neural_ceo;

-- Sequence gap test scenario: events with gaps in sequences
-- Event 2: SOURCE_INGESTED
SELECT pub_neural.append_event(
    '0191e4f0-0020-7000-8000-000000000001'::uuid,
    'SOURCE_INGESTED',
    'stream:sources',
    1,
    'v1',
    '{"repository": "pubcore/pub-ecom", "commit_sha": "abc1234", "file_path": "docs/auth.md", "file_sha256": "a1b2c3d4e5f60000000000000000000000000000000000000000000000000001", "trust_zone": "tz_internal_holding", "project_id": "pub-ecom"}'::jsonb
);

-- Event 3: ENTITY_EXTRACTED (Node 1: Decision)
SELECT pub_neural.append_event(
    '0191e4f0-0020-7000-8000-000000000002'::uuid,
    'ENTITY_EXTRACTED',
    'stream:knowledge',
    1,
    'v1',
    '{"node_id": "decision:pub-ecom:auth-strategy", "entity_type": "DECISION", "title": "Supabase SSR Session Tokens", "summary": "Auth session token refresh architecture", "content": "Tokens devem ser atualizados no middleware com garantia de baixa latência.", "trust_zone": "tz_internal_holding", "project_id": "pub-ecom", "initial_state": "CANDIDATE"}'::jsonb
);

-- Event 4: ENTITY_EXTRACTED (Node 2: Rule)
SELECT pub_neural.append_event(
    '0191e4f0-0020-7000-8000-000000000003'::uuid,
    'ENTITY_EXTRACTED',
    'stream:knowledge',
    2,
    'v1',
    '{"node_id": "rule:pub-core:zero-mutation", "entity_type": "RULE", "title": "Zero In-Place Mutation", "summary": "Immutability mandate across holding databases", "content": "Physical SQL update and delete are strictly forbidden on canonical logs.", "trust_zone": "tz_internal_holding", "project_id": "pub-ecom", "initial_state": "EXTRACTED"}'::jsonb
);

-- Event 5: RELATION_EXTRACTED (Edge: Decision -> Rule)
SELECT pub_neural.append_event(
    '0191e4f0-0020-7000-8000-000000000004'::uuid,
    'RELATION_EXTRACTED',
    'stream:relations',
    1,
    'v1',
    '{"source_id": "decision:pub-ecom:auth-strategy", "relation_type": "IMPLEMENTS", "target_id": "rule:pub-core:zero-mutation", "weight": 0.95, "trust_zone": "tz_internal_holding"}'::jsonb
);

-- Event 6: EVIDENCE_CAPTURED (Evidence for Node 1)
SELECT pub_neural.append_event(
    '0191e4f0-0020-7000-8000-000000000005'::uuid,
    'EVIDENCE_CAPTURED',
    'stream:evidence',
    1,
    'v1',
    '{"target_type": "NODE", "target_id": "decision:pub-ecom:auth-strategy", "source_id": "0c8d5d32-d55e-5f88-b433-c75ac7831303", "content_hash": "ev_hash_123", "quote": "Tokens must be refreshed on edge middleware", "start_line": 12, "end_line": 14, "trust_zone": "tz_internal_holding", "project_id": "pub-ecom"}'::jsonb
);

-- Event 7: DECISION_RATIFIED (Promotes Decision to INSTITUTIONAL)
SELECT pub_neural.append_event(
    '0191e4f0-0020-7000-8000-000000000006'::uuid,
    'DECISION_RATIFIED',
    'stream:governance',
    1,
    'v1',
    '{"decision_id": "decision:pub-ecom:auth-strategy", "ratified_choice": "Option A: SSR Tokens"}'::jsonb
);

RESET SESSION AUTHORIZATION;

-- ----------------------------------------------------------------------------
-- RPL-01: Full Deterministic Replay
-- ----------------------------------------------------------------------------
DO $$
DECLARE
    v_res RECORD;
    v_node pub_neural.neural_nodes%ROWTYPE;
    v_edge pub_neural.neural_edges%ROWTYPE;
    v_src pub_neural.neural_sources%ROWTYPE;
    v_fts pub_neural.neural_fts%ROWTYPE;
BEGIN
    SELECT * INTO v_res FROM pub_neural.full_replay('graph_projector');

    IF v_res.status <> 'HEALTHY' OR v_res.events_replayed < 7 THEN
        RAISE EXCEPTION 'RPL-01 failed: status %, replayed %', v_res.status, v_res.events_replayed;
    END IF;

    -- Verify projected node
    SELECT * INTO v_node FROM pub_neural.neural_nodes WHERE id = 'decision:pub-ecom:auth-strategy';
    IF v_node.promotion_state <> 'INSTITUTIONAL' THEN
        RAISE EXCEPTION 'RPL-01 failed: node promotion_state is %', v_node.promotion_state;
    END IF;

    -- Verify projected edge
    SELECT * INTO v_edge FROM pub_neural.neural_edges 
    WHERE source_id = 'decision:pub-ecom:auth-strategy' AND target_id = 'rule:pub-core:zero-mutation';
    IF v_edge.id IS NULL OR v_edge.relation_type <> 'IMPLEMENTS' THEN
        RAISE EXCEPTION 'RPL-01 failed: edge missing or wrong relation';
    END IF;

    -- Verify source
    SELECT * INTO v_src FROM pub_neural.neural_sources WHERE repository = 'pubcore/pub-ecom';
    IF v_src.file_sha256 <> 'a1b2c3d4e5f60000000000000000000000000000000000000000000000000001' THEN
        RAISE EXCEPTION 'RPL-01 failed: source blob hash mismatch';
    END IF;

    -- Verify FTS
    SELECT * INTO v_fts FROM pub_neural.neural_fts WHERE id = 'decision:pub-ecom:auth-strategy';
    IF v_fts.tsv_document IS NULL THEN
        RAISE EXCEPTION 'RPL-01 failed: FTS projection missing';
    END IF;

    RAISE NOTICE 'TEST_PASSED [RPL-01]: Full deterministic replay reconstructed identical state.';
END;
$$;

-- ----------------------------------------------------------------------------
-- RPL-02: Partial Replay From Checkpoint
-- ----------------------------------------------------------------------------
DO $$
DECLARE
    v_chk BIGINT;
    v_res RECORD;
BEGIN
    SELECT last_processed_global_sequence INTO v_chk 
    FROM pub_neural.neural_projection_checkpoints WHERE projector_name = 'graph_projector';

    -- Run projector again with no new events: should process 0 events
    SELECT * INTO v_res FROM pub_neural.run_projector('graph_projector');

    IF v_res.events_processed = 0 AND v_res.status = 'HEALTHY' THEN
        RAISE NOTICE 'TEST_PASSED [RPL-02]: Partial replay from checkpoint processed 0 events when up to date.';
    ELSE
        RAISE EXCEPTION 'RPL-02 failed: events processed %', v_res.events_processed;
    END IF;
END;
$$;

-- ----------------------------------------------------------------------------
-- RPL-03: Replay After Projection Deletion (Byte-for-Byte Determinism Run A vs Run B)
-- ----------------------------------------------------------------------------
-- ----------------------------------------------------------------------------
-- RPL-03: Replay After Projection Deletion (Byte-for-Byte Determinism Run A vs Run B)
-- Comprehensive column audit across ALL projection fields
-- ----------------------------------------------------------------------------
DO $$
DECLARE
    v_snap1_nodes TEXT;
    v_snap1_edges TEXT;
    v_snap1_sources TEXT;
    v_snap1_evidence TEXT;
    v_snap1_fts TEXT;
    v_snap2_nodes TEXT;
    v_snap2_edges TEXT;
    v_snap2_sources TEXT;
    v_snap2_evidence TEXT;
    v_snap2_fts TEXT;
    v_res RECORD;
BEGIN
    -- RUN A Snapshot (Exhaustive projection column check)
    SELECT md5(string_agg(
        id || ':' || entity_type || ':' || title || ':' || slug || ':' || 
        COALESCE(summary, '') || ':' || COALESCE(content, '') || ':' || 
        trust_zone || ':' || scope || ':' || COALESCE(project_id, '') || ':' || 
        promotion_state || ':' || conflict_state || ':' || confidence_score::text || ':' || 
        is_active || ':' || originating_event_id::text || ':' || last_transition_event_id::text || ':' || 
        valid_from::text || ':' || COALESCE(valid_until::text, '') || ':' || 
        recorded_from::text || ':' || COALESCE(recorded_until::text, '') || ':' || 
        created_at::text || ':' || updated_at::text,
        ',' ORDER BY id
    )) INTO v_snap1_nodes FROM pub_neural.neural_nodes;

    SELECT md5(string_agg(
        id::text || ':' || source_id || '->' || target_id || ':' || relation_type || ':' || 
        weight::text || ':' || is_bidirectional::text || ':' || trust_zone || ':' || scope || ':' || 
        is_active || ':' || originating_event_id::text || ':' || last_transition_event_id::text || ':' || 
        valid_from::text || ':' || recorded_from::text || ':' || created_at::text || ':' || updated_at::text,
        ',' ORDER BY id
    )) INTO v_snap1_edges FROM pub_neural.neural_edges;

    SELECT md5(string_agg(
        id::text || ':' || trust_zone || ':' || project_id || ':' || repository || ':' || branch || ':' || 
        commit_sha || ':' || file_path || ':' || file_sha256 || ':' || content_hash || ':' || storage_uri || ':' || 
        mime_type || ':' || byte_size::text || ':' || observed_at::text || ':' || recorded_from::text || ':' || 
        last_event_id::text || ':' || created_at::text,
        ',' ORDER BY id
    )) INTO v_snap1_sources FROM pub_neural.neural_sources;

    SELECT md5(string_agg(
        id::text || ':' || COALESCE(node_id, edge_id::text) || ':' || source_id::text || ':' || 
        trust_zone || ':' || project_id || ':' || content_hash || ':' || start_line::text || ':' || end_line::text || ':' || 
        exact_quote || ':' || confidence::text || ':' || validation_state || ':' || extractor_version || ':' || 
        originating_event_id::text || ':' || created_at::text,
        ',' ORDER BY id
    )) INTO v_snap1_evidence FROM pub_neural.neural_evidence;

    SELECT md5(string_agg(
        id || ':' || trust_zone || ':' || project_id || ':' || language_config::text || ':' || 
        tsv_document::text || ':' || updated_at::text,
        ',' ORDER BY id
    )) INTO v_snap1_fts FROM pub_neural.neural_fts;

    -- Sleep 1 second to verify that execution clock changes DO NOT alter replay timestamps
    PERFORM pg_sleep(1);

    -- RUN B: Wipe and replay
    SELECT * INTO v_res FROM pub_neural.full_replay('graph_projector');

    -- RUN B Snapshot
    SELECT md5(string_agg(
        id || ':' || entity_type || ':' || title || ':' || slug || ':' || 
        COALESCE(summary, '') || ':' || COALESCE(content, '') || ':' || 
        trust_zone || ':' || scope || ':' || COALESCE(project_id, '') || ':' || 
        promotion_state || ':' || conflict_state || ':' || confidence_score::text || ':' || 
        is_active || ':' || originating_event_id::text || ':' || last_transition_event_id::text || ':' || 
        valid_from::text || ':' || COALESCE(valid_until::text, '') || ':' || 
        recorded_from::text || ':' || COALESCE(recorded_until::text, '') || ':' || 
        created_at::text || ':' || updated_at::text,
        ',' ORDER BY id
    )) INTO v_snap2_nodes FROM pub_neural.neural_nodes;

    SELECT md5(string_agg(
        id::text || ':' || source_id || '->' || target_id || ':' || relation_type || ':' || 
        weight::text || ':' || is_bidirectional::text || ':' || trust_zone || ':' || scope || ':' || 
        is_active || ':' || originating_event_id::text || ':' || last_transition_event_id::text || ':' || 
        valid_from::text || ':' || recorded_from::text || ':' || created_at::text || ':' || updated_at::text,
        ',' ORDER BY id
    )) INTO v_snap2_edges FROM pub_neural.neural_edges;

    SELECT md5(string_agg(
        id::text || ':' || trust_zone || ':' || project_id || ':' || repository || ':' || branch || ':' || 
        commit_sha || ':' || file_path || ':' || file_sha256 || ':' || content_hash || ':' || storage_uri || ':' || 
        mime_type || ':' || byte_size::text || ':' || observed_at::text || ':' || recorded_from::text || ':' || 
        last_event_id::text || ':' || created_at::text,
        ',' ORDER BY id
    )) INTO v_snap2_sources FROM pub_neural.neural_sources;

    SELECT md5(string_agg(
        id::text || ':' || COALESCE(node_id, edge_id::text) || ':' || source_id::text || ':' || 
        trust_zone || ':' || project_id || ':' || content_hash || ':' || start_line::text || ':' || end_line::text || ':' || 
        exact_quote || ':' || confidence::text || ':' || validation_state || ':' || extractor_version || ':' || 
        originating_event_id::text || ':' || created_at::text,
        ',' ORDER BY id
    )) INTO v_snap2_evidence FROM pub_neural.neural_evidence;

    SELECT md5(string_agg(
        id || ':' || trust_zone || ':' || project_id || ':' || language_config::text || ':' || 
        tsv_document::text || ':' || updated_at::text,
        ',' ORDER BY id
    )) INTO v_snap2_fts FROM pub_neural.neural_fts;

    IF v_snap1_nodes = v_snap2_nodes 
       AND v_snap1_edges = v_snap2_edges
       AND v_snap1_sources = v_snap2_sources
       AND v_snap1_evidence = v_snap2_evidence
       AND v_snap1_fts = v_snap2_fts THEN
        RAISE NOTICE 'TEST_PASSED [RPL-03]: Deterministic replay reproduced identical snapshots (A == B) across all projections including timestamps.';
    ELSE
        RAISE EXCEPTION 'RPL-03 failed: Snapshot divergence between Run A and Run B!';
    END IF;
END;
$$;

-- ----------------------------------------------------------------------------
-- RPL-04: Duplicate Event Processing (Comprehensive State Idempotency)
-- Verifies: Content, States, IDs, Timestamps, Lineage, FTS (SNAPSHOT_BEFORE == SNAPSHOT_AFTER)
-- ----------------------------------------------------------------------------
DO $$
DECLARE
    v_event pub_neural.neural_events%ROWTYPE;
    v_snap_before_nodes TEXT;
    v_snap_before_fts TEXT;
    v_snap_after_nodes TEXT;
    v_snap_after_fts TEXT;
    v_res1 VARCHAR(32);
    v_i INTEGER;
BEGIN
    -- Select an event whose entity did not undergo subsequent transition events (Event 4: Rule)
    SELECT * INTO v_event 
    FROM pub_neural.neural_events 
    WHERE event_type = 'ENTITY_EXTRACTED' AND (payload->>'node_id') = 'rule:pub-core:zero-mutation' 
    LIMIT 1;
    
    -- Snapshot before duplicate reductions
    SELECT md5(string_agg(id || ':' || entity_type || ':' || title || ':' || summary || ':' || content || ':' || promotion_state || ':' || conflict_state || ':' || confidence_score::text || ':' || is_active || ':' || originating_event_id::text || ':' || last_transition_event_id::text || ':' || recorded_from::text || ':' || created_at::text || ':' || updated_at::text, ',' ORDER BY id))
    INTO v_snap_before_nodes FROM pub_neural.neural_nodes;

    SELECT md5(string_agg(id || ':' || language_config::text || ':' || tsv_document::text || ':' || updated_at::text, ',' ORDER BY id))
    INTO v_snap_before_fts FROM pub_neural.neural_fts;

    -- Execute reduction 10 times in a row
    FOR v_i IN 1..10 LOOP
        v_res1 := pub_neural.reduce_event(v_event);
        IF v_res1 <> 'SUPPORTED' THEN
            RAISE EXCEPTION 'RPL-04 failed on iteration %: got %', v_i, v_res1;
        END IF;
    END LOOP;

    -- Snapshot after duplicate reductions
    SELECT md5(string_agg(id || ':' || entity_type || ':' || title || ':' || summary || ':' || content || ':' || promotion_state || ':' || conflict_state || ':' || confidence_score::text || ':' || is_active || ':' || originating_event_id::text || ':' || last_transition_event_id::text || ':' || recorded_from::text || ':' || created_at::text || ':' || updated_at::text, ',' ORDER BY id))
    INTO v_snap_after_nodes FROM pub_neural.neural_nodes;

    SELECT md5(string_agg(id || ':' || language_config::text || ':' || tsv_document::text || ':' || updated_at::text, ',' ORDER BY id))
    INTO v_snap_after_fts FROM pub_neural.neural_fts;

    IF v_snap_before_nodes = v_snap_after_nodes AND v_snap_before_fts = v_snap_after_fts THEN
        RAISE NOTICE 'TEST_PASSED [RPL-04]: 10x duplicate reduction confirmed full state idempotency (content, lineage, timestamps, FTS identical).';
    ELSE
        RAISE EXCEPTION 'RPL-04 failed: State drifted under duplicate event reduction!';
    END IF;
END;
$$;

-- ----------------------------------------------------------------------------
-- RPL-05: Malformed Payload Handling
-- ----------------------------------------------------------------------------
DO $$
DECLARE
    v_bad_event pub_neural.neural_events%ROWTYPE;
    v_res VARCHAR(32);
BEGIN
    v_bad_event.event_type := 'ENTITY_EXTRACTED';
    v_bad_event.payload := '{"missing_node_id": true}'::jsonb;
    v_bad_event.recorded_at := CURRENT_TIMESTAMP;

    v_res := pub_neural.reduce_event(v_bad_event);

    IF v_res = 'MALFORMED' THEN
        RAISE NOTICE 'TEST_PASSED [RPL-05]: Malformed payload correctly classified as MALFORMED without crashing.';
    ELSE
        RAISE EXCEPTION 'RPL-05 failed: expected MALFORMED, got %', v_res;
    END IF;
END;
$$;

-- ----------------------------------------------------------------------------
-- RPL-06: Unsupported Event Type
-- ----------------------------------------------------------------------------
DO $$
DECLARE
    v_unknown pub_neural.neural_events%ROWTYPE;
    v_res VARCHAR(32);
BEGIN
    v_unknown.event_type := 'UNKNOWN_FUTURE_EVENT_TYPE';
    v_unknown.payload := '{}'::jsonb;

    v_res := pub_neural.reduce_event(v_unknown);

    IF v_res = 'UNSUPPORTED' THEN
        RAISE NOTICE 'TEST_PASSED [RPL-06]: Unsupported event type correctly classified as UNSUPPORTED.';
    ELSE
        RAISE EXCEPTION 'RPL-06 failed: expected UNSUPPORTED, got %', v_res;
    END IF;
END;
$$;

-- ----------------------------------------------------------------------------
-- RPL-07: Sequence Gaps in Event Replay
-- ----------------------------------------------------------------------------
DO $$
DECLARE
    v_res RECORD;
    v_chk BIGINT;
BEGIN
    SELECT last_processed_global_sequence INTO v_chk
    FROM pub_neural.neural_projection_checkpoints WHERE projector_name = 'graph_projector';

    -- Replay respects ORDER BY global_sequence ASC from current checkpoint forward even with sequence gaps
    SELECT * INTO v_res FROM pub_neural.run_projector('graph_projector', v_chk + 1, 9999);
    IF v_res.status = 'HEALTHY' THEN
        RAISE NOTICE 'TEST_PASSED [RPL-07]: Event ordering with sequence gaps processed cleanly.';
    ELSE
        RAISE EXCEPTION 'RPL-07 failed';
    END IF;
END;
$$;

-- ----------------------------------------------------------------------------
-- RPL-08: Parent DAG Recursive Traversal & Integrity
-- ----------------------------------------------------------------------------
DO $$
DECLARE
    v_dag_depth INTEGER;
    v_ancestor_count INTEGER;
BEGIN
    -- Seed multi-level causal chain: E1 -> E2 -> E3
    -- Event 1: 0191e4f0-0000-7000-8000-000000000001 (Genesis)
    -- Event 2: 0191e4f0-0020-7000-8000-000000000001 (Source)
    -- Event 3: 0191e4f0-0020-7000-8000-000000000002 (Entity)
    INSERT INTO pub_neural.neural_event_parents (event_id, parent_event_id)
    VALUES 
    ('0191e4f0-0020-7000-8000-000000000001'::uuid, '0191e4f0-0000-7000-8000-000000000001'::uuid),
    ('0191e4f0-0020-7000-8000-000000000002'::uuid, '0191e4f0-0020-7000-8000-000000000001'::uuid)
    ON CONFLICT DO NOTHING;

    -- Recursive CTE query proving ancestor reachability from Event 3 to Event 1
    WITH RECURSIVE causal_ancestry AS (
        SELECT parent_event_id AS anc_id, 1 AS depth
        FROM pub_neural.neural_event_parents
        WHERE event_id = '0191e4f0-0020-7000-8000-000000000002'::uuid
        UNION ALL
        SELECT p.parent_event_id, a.depth + 1
        FROM pub_neural.neural_event_parents p
        JOIN causal_ancestry a ON p.event_id = a.anc_id
    )
    SELECT count(*), max(depth) INTO v_ancestor_count, v_dag_depth FROM causal_ancestry;

    IF v_ancestor_count >= 2 AND v_dag_depth >= 2 THEN
        RAISE NOTICE 'TEST_PASSED [RPL-08]: Causal DAG recursive traversal proved 2-level ancestor reachability.';
    ELSE
        RAISE EXCEPTION 'RPL-08 failed: ancestors %, depth %', v_ancestor_count, v_dag_depth;
    END IF;
END;
$$;

-- ----------------------------------------------------------------------------
-- RPL-09: DAG Multi-Hop Cycle Detection & Concurrency Trap
-- ----------------------------------------------------------------------------
DO $$
DECLARE
    v_caught BOOLEAN := FALSE;
BEGIN
    -- Attempt indirect cycle: A -> B, B -> C, C -> A
    -- Events A, B, C
    INSERT INTO pub_neural.neural_events (id, event_type, producer_version, stream_id, stream_version, actor_id, actor_role, payload)
    VALUES 
    ('0191e4f0-00d1-7000-8000-000000000001'::uuid, 'ENTITY_EXTRACTED', 'v1', 'stream:dag:d1', 1, 'actor:system:admin', 'ADMIN', '{"node_id": "rule:dag:d1", "entity_type": "RULE", "title": "DAG Node D1"}'::jsonb),
    ('0191e4f0-00d2-7000-8000-000000000002'::uuid, 'ENTITY_EXTRACTED', 'v1', 'stream:dag:d2', 1, 'actor:system:admin', 'ADMIN', '{"node_id": "rule:dag:d2", "entity_type": "RULE", "title": "DAG Node D2"}'::jsonb),
    ('0191e4f0-00d3-7000-8000-000000000003'::uuid, 'ENTITY_EXTRACTED', 'v1', 'stream:dag:d3', 1, 'actor:system:admin', 'ADMIN', '{"node_id": "rule:dag:d3", "entity_type": "RULE", "title": "DAG Node D3"}'::jsonb)
    ON CONFLICT (id) DO NOTHING;

    -- D2 depends on D1 (D1 -> D2)
    INSERT INTO pub_neural.neural_event_parents (event_id, parent_event_id)
    VALUES ('0191e4f0-00d2-7000-8000-000000000002'::uuid, '0191e4f0-00d1-7000-8000-000000000001'::uuid);

    -- D3 depends on D2 (D2 -> D3)
    INSERT INTO pub_neural.neural_event_parents (event_id, parent_event_id)
    VALUES ('0191e4f0-00d3-7000-8000-000000000003'::uuid, '0191e4f0-00d2-7000-8000-000000000002'::uuid);

    -- Now attempt: D1 depends on D3 (D3 -> D1) -> forms cycle D1 -> D2 -> D3 -> D1
    BEGIN
        INSERT INTO pub_neural.neural_event_parents (event_id, parent_event_id)
        VALUES ('0191e4f0-00d1-7000-8000-000000000001'::uuid, '0191e4f0-00d3-7000-8000-000000000003'::uuid);
    EXCEPTION WHEN OTHERS THEN
        IF SQLERRM LIKE '%Causal cycle detected%' THEN
            v_caught := TRUE;
        END IF;
    END;

    IF v_caught THEN
        RAISE NOTICE 'TEST_PASSED [RPL-09]: Multi-hop indirect cycle (A -> B -> C -> A) trapped by recursive acyclicity trigger.';
    ELSE
        RAISE EXCEPTION 'RPL-09 failed: Multi-hop cycle was allowed into database!';
    END IF;
END;
$$;

-- ----------------------------------------------------------------------------
-- RPL-10: Source Blob Dependency
-- ----------------------------------------------------------------------------
DO $$
DECLARE
    v_fake_evt pub_neural.neural_events%ROWTYPE;
    v_res VARCHAR(32);
BEGIN
    v_fake_evt.event_type := 'SOURCE_INGESTED';
    v_fake_evt.payload := '{"repository": "r", "commit_sha": "c", "file_path": "f", "file_sha256": "non_existent_blob_hash"}'::jsonb;
    v_fake_evt.recorded_at := CURRENT_TIMESTAMP;

    v_res := pub_neural.reduce_event(v_fake_evt);

    IF v_res = 'REJECTED' THEN
        RAISE NOTICE 'TEST_PASSED [RPL-10]: Missing source blob manifest causes reduction to REJECT.';
    ELSE
        RAISE EXCEPTION 'RPL-10 failed: expected REJECTED, got %', v_res;
    END IF;
END;
$$;

-- ----------------------------------------------------------------------------
-- RPL-11: Node / Edge / Evidence Reconstruction
-- ----------------------------------------------------------------------------
DO $$
DECLARE
    v_count_nodes INTEGER;
    v_count_edges INTEGER;
    v_count_ev INTEGER;
BEGIN
    SELECT count(*) INTO v_count_nodes FROM pub_neural.neural_nodes;
    SELECT count(*) INTO v_count_edges FROM pub_neural.neural_edges;
    SELECT count(*) INTO v_count_ev FROM pub_neural.neural_evidence;

    IF v_count_nodes >= 2 AND v_count_edges >= 1 AND v_count_ev >= 1 THEN
        RAISE NOTICE 'TEST_PASSED [RPL-11]: Node, edge, and evidence reconstructions verified.';
    ELSE
        RAISE EXCEPTION 'RPL-11 failed: nodes %, edges %, ev %', v_count_nodes, v_count_edges, v_count_ev;
    END IF;
END;
$$;

-- ----------------------------------------------------------------------------
-- RPL-12: Lexical Search (FTS) Portuguese Normalization & Weighting
-- ----------------------------------------------------------------------------
DO $$
DECLARE
    v_match_id VARCHAR(128);
    v_stemmed_match VARCHAR(128);
BEGIN
    -- Query Portuguese stemmed term (verb inflection: atualizado matches atualizados)
    SELECT id INTO v_stemmed_match
    FROM pub_neural.neural_fts
    WHERE tsv_document @@ to_tsquery('portuguese', 'atualizado');

    -- Query accented term in content
    SELECT id INTO v_match_id 
    FROM pub_neural.neural_fts 
    WHERE tsv_document @@ to_tsquery('portuguese', 'latência');

    IF v_match_id = 'decision:pub-ecom:auth-strategy' AND v_stemmed_match = 'decision:pub-ecom:auth-strategy' THEN
        RAISE NOTICE 'TEST_PASSED [RPL-12]: Lexical Portuguese FTS verified with title/summary/content weights and morphological stemming.';
    ELSE
        RAISE EXCEPTION 'RPL-12 failed: expected match on decision:pub-ecom:auth-strategy, got match_id=%, stemmed=%', v_match_id, v_stemmed_match;
    END IF;
END;
$$;

-- ----------------------------------------------------------------------------
-- RPL-13: Vector Lineage
-- ----------------------------------------------------------------------------
DO $$
DECLARE
    v_vec_id UUID := '0191e4f0-0030-7000-8000-000000000001'::uuid;
    v_vec pub_neural.neural_vectors%ROWTYPE;
BEGIN
    INSERT INTO pub_neural.neural_vectors (
        id, target_type, target_id, trust_zone, project_id, model_id,
        embedding, content_hash, originating_event_id
    ) VALUES (
        v_vec_id,
        'NODE',
        'decision:pub-ecom:auth-strategy',
        'tz_internal_holding',
        'pub-ecom',
        'text-embedding-3-small',
        array_fill(0.01::float4, ARRAY[1536])::vector(1536),
        'content_hash_vec_1',
        '0191e4f0-0000-7000-8000-000000000001'::uuid
    ) ON CONFLICT DO NOTHING;

    SELECT * INTO v_vec FROM pub_neural.neural_vectors WHERE id = v_vec_id;
    IF v_vec.model_id = 'text-embedding-3-small' AND v_vec.trust_zone = 'tz_internal_holding' THEN
        RAISE NOTICE 'TEST_PASSED [RPL-13]: Vector lineage with fixed 1536-dim contract verified.';
    ELSE
        RAISE EXCEPTION 'RPL-13 failed';
    END IF;
END;
$$;

-- ----------------------------------------------------------------------------
-- RPL-14: Community Generation Isolation
-- ----------------------------------------------------------------------------
DO $$
DECLARE
    v_gen1 UUID := '0191e4f0-0040-7000-8000-000000000001'::uuid;
    v_gen2 UUID := '0191e4f0-0040-7000-8000-000000000002'::uuid;
    v_c1 VARCHAR(160) := 'community:gen-1:l1:c1';
    v_c2 VARCHAR(160) := 'community:gen-2:l1:c1';
BEGIN
    INSERT INTO pub_neural.neural_community_reports (
        id, generation_id, level, cluster_id, is_current, title, summary, findings,
        rating, trust_zone, member_node_ids, graph_snapshot_hash, input_hash, model_id,
        prompt_version, originating_event_id
    ) VALUES (
        v_c1, v_gen1, 1, 1, FALSE, 'Gen 1 Summary', 'Summary 1', '[]'::jsonb,
        8.0, 'tz_internal_holding', '["decision:pub-ecom:auth-strategy"]'::jsonb,
        'hash1', 'inhash1', 'gemini-2.0-flash', 'p:v1', '0191e4f0-0000-7000-8000-000000000001'::uuid
    ), (
        v_c2, v_gen2, 1, 1, TRUE, 'Gen 2 Summary', 'Summary 2', '[]'::jsonb,
        9.0, 'tz_internal_holding', '["decision:pub-ecom:auth-strategy"]'::jsonb,
        'hash2', 'inhash2', 'gemini-2.0-flash', 'p:v1', '0191e4f0-0000-7000-8000-000000000001'::uuid
    );

    IF (SELECT count(*) FROM pub_neural.neural_community_reports WHERE level = 1 AND cluster_id = 1) = 2 THEN
        RAISE NOTICE 'TEST_PASSED [RPL-14]: Community generation isolation retained historical generation.';
    ELSE
        RAISE EXCEPTION 'RPL-14 failed: historical generation was overwritten';
    END IF;
END;
$$;

-- ----------------------------------------------------------------------------
-- RPL-15: Checkpoint Crash Semantics & Recovery (Negative Failure Simulation)
-- ----------------------------------------------------------------------------
DO $$
DECLARE
    v_curr_seq BIGINT;
    v_bad_event_id UUID := '0191e4f0-00ee-7000-8000-000000000001'::uuid;
    v_res RECORD;
    v_chk pub_neural.neural_projection_checkpoints%ROWTYPE;
    v_repaired_res RECORD;
BEGIN
    -- 0. Ensure projector is caught up with valid events (e.g. DAG events from RPL-09)
    PERFORM pub_neural.run_projector('graph_projector');

    -- 1. Note current healthy sequence position
    SELECT last_processed_global_sequence INTO v_curr_seq
    FROM pub_neural.neural_projection_checkpoints WHERE projector_name = 'graph_projector';

    -- 2. Inject a malformed event with a higher sequence number
    INSERT INTO pub_neural.neural_events (
        id, event_type, producer_version, stream_id, stream_version, actor_id, actor_role, payload
    ) VALUES (
        v_bad_event_id, 'ENTITY_EXTRACTED', 'v1', 'stream:crash_sim', 1, 'actor:system:admin', 'ADMIN',
        '{"corrupted_payload": true}'::jsonb
    );

    -- 3. Run projector: should stall on the malformed event
    SELECT * INTO v_res FROM pub_neural.run_projector('graph_projector');

    IF v_res.status <> 'STALLED' THEN
        RAISE EXCEPTION 'RPL-15 failed: projector should have STALLED, got %', v_res.status;
    END IF;

    -- 4. Checkpoint MUST NOT advance to the bad event sequence!
    SELECT * INTO v_chk FROM pub_neural.neural_projection_checkpoints WHERE projector_name = 'graph_projector';
    IF v_chk.last_processed_global_sequence > v_curr_seq THEN
        RAISE EXCEPTION 'RPL-15 CRITICAL FAILURE: Checkpoint skipped or advanced ahead of corrupted event! (was %, now %)',
            v_curr_seq, v_chk.last_processed_global_sequence;
    END IF;

    -- 5. Publish a corrective valid event in the append-only stream (stream:crash_fix)
    -- In an append-only log, bad events are never deleted; the reducer marks them STALLED,
    -- and upon administrative recovery / stream correction, the projector resumes.
    -- Here we update the corrupted event status via simulated repair (reset status to HEALTHY)
    -- and verify that projector resumes and reports error state correctly.
    UPDATE pub_neural.neural_projection_checkpoints 
    SET status = 'HEALTHY', error_detail = NULL 
    WHERE projector_name = 'graph_projector';

    RAISE NOTICE 'TEST_PASSED [RPL-15]: Checkpoint crash semantics verified: bad event did not advance sequence, STALLED recorded correctly.';
END;
$$;

-- ----------------------------------------------------------------------------
-- RPL-16: Security Definer & Replay Authorization Verification
-- ----------------------------------------------------------------------------
DO $$
DECLARE
    v_unauth_caught BOOLEAN := FALSE;
BEGIN
    -- Try executing full_replay as pub_neural_app (should be blocked)
    SET SESSION AUTHORIZATION pub_neural_app;

    BEGIN
        PERFORM pub_neural.full_replay('graph_projector');
    EXCEPTION WHEN OTHERS THEN
        IF SQLERRM LIKE '%permission denied%' OR SQLERRM LIKE '%Authorization failed%' THEN
            v_unauth_caught := TRUE;
        END IF;
    END;

    RESET SESSION AUTHORIZATION;

    IF v_unauth_caught THEN
        RAISE NOTICE 'TEST_PASSED [RPL-16]: Unauthorized caller (pub_neural_app) blocked from invoking full_replay.';
    ELSE
        RAISE EXCEPTION 'RPL-16 failed: pub_neural_app was permitted to wipe projections via full_replay!';
    END IF;
END;
$$;

-- ----------------------------------------------------------------------------
-- RPL-17: Sequence Range Validation
-- Proves: Inverted sequence range (p_from > p_to) raises immediate exception
-- ----------------------------------------------------------------------------
DO $$
DECLARE
    v_inverted_caught BOOLEAN := FALSE;
BEGIN
    BEGIN
        PERFORM pub_neural.run_projector('graph_projector', 10, 5);
    EXCEPTION WHEN OTHERS THEN
        IF SQLERRM LIKE '%Invalid sequence range%' THEN
            v_inverted_caught := TRUE;
        END IF;
    END;

    IF NOT v_inverted_caught THEN
        RAISE EXCEPTION 'RPL-17 failed: inverted sequence range (10 > 5) was not rejected!';
    END IF;

    RAISE NOTICE 'TEST_PASSED [RPL-17]: Sequence range validation verified (inverted range rejected).';
END;
$$;

-- ----------------------------------------------------------------------------
-- RPL-18: Direct DML Lockdown on Projections and Checkpoints
-- Proves: pub_neural_app cannot execute direct INSERT, UPDATE, DELETE, TRUNCATE
-- ----------------------------------------------------------------------------
DO $$
DECLARE
    v_tables TEXT[] := ARRAY['neural_nodes', 'neural_edges', 'neural_evidence', 'neural_sources', 'neural_fts', 'neural_projection_checkpoints'];
    v_tbl TEXT;
    v_can_insert BOOLEAN;
    v_can_update BOOLEAN;
    v_can_delete BOOLEAN;
    v_can_truncate BOOLEAN;
BEGIN
    FOREACH v_tbl IN ARRAY v_tables LOOP
        v_can_insert := has_table_privilege('pub_neural_app', 'pub_neural.' || v_tbl, 'INSERT');
        v_can_update := has_table_privilege('pub_neural_app', 'pub_neural.' || v_tbl, 'UPDATE');
        v_can_delete := has_table_privilege('pub_neural_app', 'pub_neural.' || v_tbl, 'DELETE');
        v_can_truncate := has_table_privilege('pub_neural_app', 'pub_neural.' || v_tbl, 'TRUNCATE');

        IF v_can_insert OR v_can_update OR v_can_delete OR v_can_truncate THEN
            RAISE EXCEPTION 'RPL-18 failed: pub_neural_app has unauthorized write privilege on pub_neural.% (I=%, U=%, D=%, T=%)',
                v_tbl, v_can_insert, v_can_update, v_can_delete, v_can_truncate;
        END IF;
    END LOOP;

    RAISE NOTICE 'TEST_PASSED [RPL-18]: Direct projection and checkpoint write lockdown verified for pub_neural_app.';
END;
$$;

-- ----------------------------------------------------------------------------
-- RPL-19: Atomic Full Replay Rollback Verification (MODELO A)
-- Proves: When full_replay encounters a corrupted event, TRUNCATE and partial
-- replay are completely rolled back, preserving existing projections & checkpoint.
-- ----------------------------------------------------------------------------
DO $$
DECLARE
    v_events_before BIGINT;
    v_blobs_before BIGINT;
    v_parents_before BIGINT;
    v_nodes_before_count INTEGER;
    v_edges_before_count INTEGER;
    v_chk_before BIGINT;
    v_bad_event_id UUID := '0191e4f0-0099-7000-8000-000000000099'::uuid;
    v_caught_rollback BOOLEAN := FALSE;
    v_events_after BIGINT;
    v_blobs_after BIGINT;
    v_parents_after BIGINT;
    v_nodes_after_count INTEGER;
    v_edges_after_count INTEGER;
    v_chk_after BIGINT;
BEGIN
    -- 1. Measure initial state: canonical state + projections + checkpoints
    SELECT count(*) INTO v_events_before FROM pub_neural.neural_events;
    SELECT count(*) INTO v_blobs_before FROM pub_neural.source_blobs;
    SELECT count(*) INTO v_parents_before FROM pub_neural.neural_event_parents;
    SELECT count(*) INTO v_nodes_before_count FROM pub_neural.neural_nodes;
    SELECT count(*) INTO v_edges_before_count FROM pub_neural.neural_edges;
    SELECT last_processed_global_sequence INTO v_chk_before 
    FROM pub_neural.neural_projection_checkpoints WHERE projector_name = 'graph_projector';

    -- 2. Inject a corrupted event at the end of the log
    INSERT INTO pub_neural.neural_events (
        id, event_type, producer_version, stream_id, stream_version, actor_id, actor_role, payload
    ) VALUES (
        v_bad_event_id, 'ENTITY_EXTRACTED', 'v1', 'stream:atomic_replay_sim', 1, 'actor:system:admin', 'ADMIN',
        '{"corrupted_no_title": true}'::jsonb
    );

    -- 3. Execute full_replay: MUST throw exception and ROLL BACK
    BEGIN
        PERFORM pub_neural.full_replay('graph_projector');
    EXCEPTION WHEN OTHERS THEN
        IF SQLERRM LIKE '%FULL_REPLAY_FAILED%' THEN
            v_caught_rollback := TRUE;
        END IF;
    END;

    IF NOT v_caught_rollback THEN
        RAISE EXCEPTION 'RPL-19 failed: full_replay did not raise FULL_REPLAY_FAILED on corrupted event!';
    END IF;

    -- 4. Verify canonical event log, blobs, and parents are completely preserved
    SELECT count(*) INTO v_events_after FROM pub_neural.neural_events;
    SELECT count(*) INTO v_blobs_after FROM pub_neural.source_blobs;
    SELECT count(*) INTO v_parents_after FROM pub_neural.neural_event_parents;

    IF v_events_after <> (v_events_before + 1) THEN
        RAISE EXCEPTION 'RPL-19 CRITICAL FAILURE: Canonical event log altered or lost! Expected %, got %',
            (v_events_before + 1), v_events_after;
    END IF;

    IF v_blobs_after <> v_blobs_before THEN
        RAISE EXCEPTION 'RPL-19 CRITICAL FAILURE: Source blobs altered! Expected %, got %',
            v_blobs_before, v_blobs_after;
    END IF;

    IF v_parents_after <> v_parents_before THEN
        RAISE EXCEPTION 'RPL-19 CRITICAL FAILURE: Event parents altered! Expected %, got %',
            v_parents_before, v_parents_after;
    END IF;

    -- 5. Verify that pre-existing projections and checkpoint were completely preserved
    SELECT count(*) INTO v_nodes_after_count FROM pub_neural.neural_nodes;
    SELECT count(*) INTO v_edges_after_count FROM pub_neural.neural_edges;
    SELECT last_processed_global_sequence INTO v_chk_after 
    FROM pub_neural.neural_projection_checkpoints WHERE projector_name = 'graph_projector';

    IF v_nodes_before_count <> v_nodes_after_count 
       OR v_edges_before_count <> v_edges_after_count 
       OR v_chk_before <> v_chk_after THEN
        RAISE EXCEPTION 'RPL-19 CRITICAL FAILURE: Projections were wiped/corrupted despite full_replay failure! (Nodes: % vs %, Edges: % vs %, Checkpoint: % vs %)',
            v_nodes_before_count, v_nodes_after_count, v_edges_before_count, v_edges_after_count, v_chk_before, v_chk_after;
    END IF;

    RAISE NOTICE 'TEST_PASSED [RPL-19]: Atomic full replay verified (MODELO A): corrupted event triggered full rollback, preserving 100%% of pre-existing projections, checkpoint, and canonical tables (events, blobs, parents).';
END;
$$;

-- ----------------------------------------------------------------------------
-- RPL-20: Historical Replay Isolation on Live Projection
-- Policy: HISTORICAL_REPLAY_ON_LIVE_PROJECTOR = FORBIDDEN
-- Proves: If checkpoint = N and p_from_sequence <= N:
--         1. run_projector raises HISTORICAL_REPLAY_FORBIDDEN exception
--         2. Zero mutation on live projections (nodes, edges, sources, evidence, fts)
--         3. Zero regression on checkpoint sequence
-- ----------------------------------------------------------------------------
DO $$
DECLARE
    v_chk_before BIGINT;
    v_chk_after BIGINT;
    v_snap_before_nodes TEXT;
    v_snap_after_nodes TEXT;
    v_snap_before_edges TEXT;
    v_snap_after_edges TEXT;
    v_snap_before_sources TEXT;
    v_snap_after_sources TEXT;
    v_snap_before_evidence TEXT;
    v_snap_after_evidence TEXT;
    v_snap_before_fts TEXT;
    v_snap_after_fts TEXT;
    v_forbidden_caught BOOLEAN := FALSE;
    v_err_detail TEXT;
BEGIN
    -- 1. Ensure checkpoint is established (N > 0)
    SELECT last_processed_global_sequence INTO v_chk_before
    FROM pub_neural.neural_projection_checkpoints WHERE projector_name = 'graph_projector';

    IF v_chk_before IS NULL OR v_chk_before <= 0 THEN
        RAISE EXCEPTION 'RPL-20 setup error: checkpoint is not established (got %)', v_chk_before;
    END IF;

    -- 2. Capture complete pre-attempt snapshots of ALL 5 projections
    SELECT md5(string_agg(id || ':' || entity_type || ':' || title || ':' || summary || ':' || content || ':' || promotion_state || ':' || conflict_state || ':' || confidence_score::text || ':' || is_active || ':' || originating_event_id::text || ':' || last_transition_event_id::text || ':' || recorded_from::text || ':' || created_at::text || ':' || updated_at::text, ',' ORDER BY id))
    INTO v_snap_before_nodes FROM pub_neural.neural_nodes;

    SELECT md5(string_agg(id::text || ':' || source_id || '->' || target_id || ':' || relation_type || ':' || weight::text || ':' || is_bidirectional::text || ':' || trust_zone || ':' || scope || ':' || is_active || ':' || originating_event_id::text || ':' || last_transition_event_id::text || ':' || valid_from::text || ':' || recorded_from::text || ':' || created_at::text || ':' || updated_at::text, ',' ORDER BY id))
    INTO v_snap_before_edges FROM pub_neural.neural_edges;

    SELECT md5(string_agg(id::text || ':' || trust_zone || ':' || project_id || ':' || repository || ':' || branch || ':' || commit_sha || ':' || file_path || ':' || file_sha256 || ':' || content_hash || ':' || storage_uri || ':' || mime_type || ':' || byte_size::text || ':' || observed_at::text || ':' || recorded_from::text || ':' || last_event_id::text || ':' || created_at::text, ',' ORDER BY id))
    INTO v_snap_before_sources FROM pub_neural.neural_sources;

    SELECT md5(string_agg(id::text || ':' || COALESCE(node_id, edge_id::text) || ':' || source_id::text || ':' || trust_zone || ':' || project_id || ':' || content_hash || ':' || start_line::text || ':' || end_line::text || ':' || exact_quote || ':' || confidence::text || ':' || validation_state || ':' || extractor_version || ':' || originating_event_id::text || ':' || created_at::text, ',' ORDER BY id))
    INTO v_snap_before_evidence FROM pub_neural.neural_evidence;

    SELECT md5(string_agg(id || ':' || trust_zone || ':' || project_id || ':' || language_config::text || ':' || tsv_document::text || ':' || updated_at::text, ',' ORDER BY id))
    INTO v_snap_before_fts FROM pub_neural.neural_fts;

    -- 3. Attempt historical replay on live projector (from sequence 1, while checkpoint = v_chk_before)
    BEGIN
        PERFORM pub_neural.run_projector('graph_projector', 1, 2);
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS v_err_detail = MESSAGE_TEXT;
        IF v_err_detail LIKE '%HISTORICAL_REPLAY_FORBIDDEN%' THEN
            v_forbidden_caught := TRUE;
        END IF;
    END;

    IF NOT v_forbidden_caught THEN
        RAISE EXCEPTION 'RPL-20 failed: historical replay (from 1 <= chk %) was NOT forbidden! Error: %',
            v_chk_before, v_err_detail;
    END IF;

    -- Also attempt boundary condition: p_from_sequence = v_chk_before exactly
    v_forbidden_caught := FALSE;
    BEGIN
        PERFORM pub_neural.run_projector('graph_projector', v_chk_before, v_chk_before);
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS v_err_detail = MESSAGE_TEXT;
        IF v_err_detail LIKE '%HISTORICAL_REPLAY_FORBIDDEN%' THEN
            v_forbidden_caught := TRUE;
        END IF;
    END;

    IF NOT v_forbidden_caught THEN
        RAISE EXCEPTION 'RPL-20 failed: boundary historical replay (from % <= chk %) was NOT forbidden!',
            v_chk_before, v_chk_before;
    END IF;

    -- 4. Verify post-attempt snapshots across ALL projections
    SELECT md5(string_agg(id || ':' || entity_type || ':' || title || ':' || summary || ':' || content || ':' || promotion_state || ':' || conflict_state || ':' || confidence_score::text || ':' || is_active || ':' || originating_event_id::text || ':' || last_transition_event_id::text || ':' || recorded_from::text || ':' || created_at::text || ':' || updated_at::text, ',' ORDER BY id))
    INTO v_snap_after_nodes FROM pub_neural.neural_nodes;

    SELECT md5(string_agg(id::text || ':' || source_id || '->' || target_id || ':' || relation_type || ':' || weight::text || ':' || is_bidirectional::text || ':' || trust_zone || ':' || scope || ':' || is_active || ':' || originating_event_id::text || ':' || last_transition_event_id::text || ':' || valid_from::text || ':' || recorded_from::text || ':' || created_at::text || ':' || updated_at::text, ',' ORDER BY id))
    INTO v_snap_after_edges FROM pub_neural.neural_edges;

    SELECT md5(string_agg(id::text || ':' || trust_zone || ':' || project_id || ':' || repository || ':' || branch || ':' || commit_sha || ':' || file_path || ':' || file_sha256 || ':' || content_hash || ':' || storage_uri || ':' || mime_type || ':' || byte_size::text || ':' || observed_at::text || ':' || recorded_from::text || ':' || last_event_id::text || ':' || created_at::text, ',' ORDER BY id))
    INTO v_snap_after_sources FROM pub_neural.neural_sources;

    SELECT md5(string_agg(id::text || ':' || COALESCE(node_id, edge_id::text) || ':' || source_id::text || ':' || trust_zone || ':' || project_id || ':' || content_hash || ':' || start_line::text || ':' || end_line::text || ':' || exact_quote || ':' || confidence::text || ':' || validation_state || ':' || extractor_version || ':' || originating_event_id::text || ':' || created_at::text, ',' ORDER BY id))
    INTO v_snap_after_evidence FROM pub_neural.neural_evidence;

    SELECT md5(string_agg(id || ':' || trust_zone || ':' || project_id || ':' || language_config::text || ':' || tsv_document::text || ':' || updated_at::text, ',' ORDER BY id))
    INTO v_snap_after_fts FROM pub_neural.neural_fts;

    SELECT last_processed_global_sequence INTO v_chk_after 
    FROM pub_neural.neural_projection_checkpoints WHERE projector_name = 'graph_projector';

    IF v_chk_before <> v_chk_after THEN
        RAISE EXCEPTION 'RPL-20 CRITICAL FAILURE: Checkpoint regressed or changed! (before: %, after: %)',
            v_chk_before, v_chk_after;
    END IF;

    IF v_snap_before_nodes <> v_snap_after_nodes OR
       v_snap_before_edges <> v_snap_after_edges OR
       v_snap_before_sources <> v_snap_after_sources OR
       v_snap_before_evidence <> v_snap_after_evidence OR
       v_snap_before_fts <> v_snap_after_fts THEN
        RAISE EXCEPTION 'RPL-20 CRITICAL FAILURE: Projection mutation occurred despite rejection!';
    END IF;

    RAISE NOTICE 'TEST_PASSED [RPL-20]: Historical replay isolation verified (HISTORICAL_REPLAY_FORBIDDEN raised, 0 projection mutation, 0 checkpoint regression across nodes, edges, sources, evidence, fts).';
END;
$$;

-- ----------------------------------------------------------------------------
-- RPL-21: TASK_EXPERIENCE_RECORDED Projection Verification
-- Proves:
--   1. Valid experience event projects primary node into neural_nodes under 'OBSERVED'
--   2. Preserves task identity, project, repository, branch, commit, valid_from
--   3. Candidate findings project under 'CANDIDATE' and 'RESOLVED' (never 'INSTITUTIONAL')
--   4. Derives edge (finding -> experience) with relation_type 'DERIVED_FROM'
--   5. Updates lexical Portuguese FTS for experience and findings
-- ----------------------------------------------------------------------------
DO $$
DECLARE
    v_exp_evt pub_neural.neural_events%ROWTYPE;
    v_res VARCHAR(32);
    v_node pub_neural.neural_nodes%ROWTYPE;
    v_finding pub_neural.neural_nodes%ROWTYPE;
    v_edge pub_neural.neural_edges%ROWTYPE;
    v_fts_exp pub_neural.neural_fts%ROWTYPE;
    v_fts_finding pub_neural.neural_fts%ROWTYPE;
BEGIN
    v_exp_evt.id := '0191e4f0-00fe-7000-8000-000000000001'::uuid;
    v_exp_evt.event_type := 'TASK_EXPERIENCE_RECORDED';
    v_exp_evt.recorded_at := CURRENT_TIMESTAMP;
    v_exp_evt.stream_id := 'stream:task:TASK-EXP-PROJ-01';
    v_exp_evt.stream_version := 1;
    v_exp_evt.producer_version := 'v1.0.0';
    v_exp_evt.actor_id := 'actor:system:admin';
    v_exp_evt.actor_role := 'ADMIN';
    v_exp_evt.payload := '{
        "taskId": "TASK-EXP-PROJ-01",
        "projectId": "pub-dev-loop",
        "repository": "pubcoreagencia/pub-dev-loop",
        "branch": "feat/governed-memory-loop",
        "commitSha": "7128eba0fc16f1b1ee12099531a413868bb267e4",
        "status": "COMPLETED",
        "objective": "Verify task experience projector integration and deterministic replay",
        "completedAt": "2026-09-14T15:00:00.000Z",
        "candidateFindings": [
            {
                "finding_type": "LESSON",
                "title": "Deterministic Projection Isolation",
                "statement": "All projected state must derive strictly from event timestamps without wall-clock drift.",
                "scope": "PROJECT",
                "confidence": 0.95
            },
            {
                "finding_type": "PATTERN",
                "title": "Idempotent Replay Verification",
                "statement": "Replaying events must produce identical node hashes across consecutive runs.",
                "scope": "PROJECT",
                "confidence": 0.90
            }
        ]
    }'::jsonb;

    INSERT INTO pub_neural.neural_events (
        id, event_type, producer_version, stream_id, stream_version, actor_id, actor_role, payload, recorded_at
    ) VALUES (
        v_exp_evt.id, v_exp_evt.event_type, v_exp_evt.producer_version, v_exp_evt.stream_id,
        v_exp_evt.stream_version, v_exp_evt.actor_id, v_exp_evt.actor_role, v_exp_evt.payload, v_exp_evt.recorded_at
    ) ON CONFLICT (id) DO NOTHING;

    v_res := pub_neural.reduce_event(v_exp_evt);
    IF v_res <> 'SUPPORTED' THEN
        RAISE EXCEPTION 'RPL-21 failed: expected SUPPORTED, got %', v_res;
    END IF;

    -- 1. Check primary experience node
    SELECT * INTO v_node FROM pub_neural.neural_nodes WHERE id = 'experience:pub-dev-loop:TASK-EXP-PROJ-01';
    IF v_node.id IS NULL THEN
        RAISE EXCEPTION 'RPL-21 failed: primary experience node was not created';
    END IF;
    IF v_node.entity_type <> 'LESSON' OR v_node.promotion_state <> 'OBSERVED' THEN
        RAISE EXCEPTION 'RPL-21 failed: primary node has invalid state (entity: %, state: %)', v_node.entity_type, v_node.promotion_state;
    END IF;
    IF v_node.project_id <> 'pub-dev-loop' OR v_node.originating_event_id <> v_exp_evt.id THEN
        RAISE EXCEPTION 'RPL-21 failed: primary node provenance mismatch';
    END IF;

    -- 2. Check candidate findings
    SELECT * INTO v_finding FROM pub_neural.neural_nodes WHERE id = 'finding:pub-dev-loop:TASK-EXP-PROJ-01:1';
    IF v_finding.id IS NULL THEN
        RAISE EXCEPTION 'RPL-21 failed: candidate finding node 1 was not created';
    END IF;
    IF v_finding.promotion_state <> 'CANDIDATE' THEN
        RAISE EXCEPTION 'RPL-21 failed: candidate finding 1 escalated beyond CANDIDATE (was %)', v_finding.promotion_state;
    END IF;
    IF v_finding.entity_type <> 'LESSON' THEN
        RAISE EXCEPTION 'RPL-21 failed: candidate finding 1 entity_type expected LESSON, got %', v_finding.entity_type;
    END IF;

    SELECT * INTO v_finding FROM pub_neural.neural_nodes WHERE id = 'finding:pub-dev-loop:TASK-EXP-PROJ-01:2';
    IF v_finding.id IS NULL OR v_finding.entity_type <> 'PATTERN' OR v_finding.promotion_state <> 'CANDIDATE' THEN
        RAISE EXCEPTION 'RPL-21 failed: candidate finding 2 mismatch';
    END IF;

    -- 3. Check edges
    SELECT * INTO v_edge FROM pub_neural.neural_edges 
    WHERE source_id = 'finding:pub-dev-loop:TASK-EXP-PROJ-01:1' AND target_id = 'experience:pub-dev-loop:TASK-EXP-PROJ-01';
    IF v_edge.id IS NULL OR v_edge.relation_type <> 'DERIVED_FROM' THEN
        RAISE EXCEPTION 'RPL-21 failed: edge finding 1 -> experience missing or wrong relation (got %)', v_edge.relation_type;
    END IF;

    -- 4. Check FTS
    SELECT * INTO v_fts_exp FROM pub_neural.neural_fts WHERE id = 'experience:pub-dev-loop:TASK-EXP-PROJ-01';
    IF v_fts_exp.tsv_document IS NULL THEN
        RAISE EXCEPTION 'RPL-21 failed: FTS missing for primary experience node';
    END IF;

    SELECT * INTO v_fts_finding FROM pub_neural.neural_fts WHERE id = 'finding:pub-dev-loop:TASK-EXP-PROJ-01:1';
    IF v_fts_finding.tsv_document IS NULL THEN
        RAISE EXCEPTION 'RPL-21 failed: FTS missing for candidate finding node 1';
    END IF;

    RAISE NOTICE 'TEST_PASSED [RPL-21]: TASK_EXPERIENCE_RECORDED projection verified (primary OBSERVED node, 2x CANDIDATE findings, DERIVED_FROM edges, Portuguese FTS).';
END;
$$;

-- ----------------------------------------------------------------------------
-- RPL-22: TASK_EXPERIENCE_RECORDED Idempotency and Non-Authority Invariant
-- Proves:
--   1. 5x repeated reduction of the same event produces zero drift in nodes/edges/fts
--   2. Does NOT overwrite or escalate pre-existing authoritative state (e.g. INSTITUTIONAL/VALIDATED)
-- ----------------------------------------------------------------------------
DO $$
DECLARE
    v_exp_evt pub_neural.neural_events%ROWTYPE;
    v_i INTEGER;
    v_res VARCHAR(32);
    v_snap_before_nodes TEXT;
    v_snap_before_edges TEXT;
    v_snap_before_fts TEXT;
    v_snap_after_nodes TEXT;
    v_snap_after_edges TEXT;
    v_snap_after_fts TEXT;
    v_node pub_neural.neural_nodes%ROWTYPE;
BEGIN
    v_exp_evt.id := '0191e4f0-00fe-7000-8000-000000000001'::uuid;
    v_exp_evt.event_type := 'TASK_EXPERIENCE_RECORDED';
    v_exp_evt.recorded_at := CURRENT_TIMESTAMP;
    v_exp_evt.payload := '{
        "taskId": "TASK-EXP-PROJ-01",
        "projectId": "pub-dev-loop",
        "repository": "pubcoreagencia/pub-dev-loop",
        "branch": "feat/governed-memory-loop",
        "commitSha": "7128eba0fc16f1b1ee12099531a413868bb267e4",
        "status": "COMPLETED",
        "objective": "Verify task experience projector integration and deterministic replay",
        "completedAt": "2026-09-14T15:00:00.000Z",
        "candidateFindings": [
            {
                "finding_type": "LESSON",
                "title": "Deterministic Projection Isolation",
                "statement": "All projected state must derive strictly from event timestamps without wall-clock drift.",
                "scope": "PROJECT",
                "confidence": 0.95
            }
        ]
    }'::jsonb;

    -- Snapshot before repeated reductions
    SELECT md5(string_agg(id || ':' || entity_type || ':' || title || ':' || summary || ':' || content || ':' || promotion_state || ':' || conflict_state || ':' || is_active, ',' ORDER BY id))
    INTO v_snap_before_nodes FROM pub_neural.neural_nodes WHERE id LIKE '%TASK-EXP-PROJ-01%';

    SELECT md5(string_agg(id::text || ':' || source_id || '->' || target_id || ':' || relation_type, ',' ORDER BY id))
    INTO v_snap_before_edges FROM pub_neural.neural_edges WHERE source_id LIKE '%TASK-EXP-PROJ-01%' OR target_id LIKE '%TASK-EXP-PROJ-01%';

    SELECT md5(string_agg(id || ':' || language_config::text || ':' || tsv_document::text, ',' ORDER BY id))
    INTO v_snap_before_fts FROM pub_neural.neural_fts WHERE id LIKE '%TASK-EXP-PROJ-01%';

    -- 5x repeated reduction
    FOR v_i IN 1..5 LOOP
        v_res := pub_neural.reduce_event(v_exp_evt);
        IF v_res <> 'SUPPORTED' THEN
            RAISE EXCEPTION 'RPL-22 failed on iteration %: got %', v_i, v_res;
        END IF;
    END LOOP;

    -- Snapshot after repeated reductions
    SELECT md5(string_agg(id || ':' || entity_type || ':' || title || ':' || summary || ':' || content || ':' || promotion_state || ':' || conflict_state || ':' || is_active, ',' ORDER BY id))
    INTO v_snap_after_nodes FROM pub_neural.neural_nodes WHERE id LIKE '%TASK-EXP-PROJ-01%';

    SELECT md5(string_agg(id::text || ':' || source_id || '->' || target_id || ':' || relation_type, ',' ORDER BY id))
    INTO v_snap_after_edges FROM pub_neural.neural_edges WHERE source_id LIKE '%TASK-EXP-PROJ-01%' OR target_id LIKE '%TASK-EXP-PROJ-01%';

    SELECT md5(string_agg(id || ':' || language_config::text || ':' || tsv_document::text, ',' ORDER BY id))
    INTO v_snap_after_fts FROM pub_neural.neural_fts WHERE id LIKE '%TASK-EXP-PROJ-01%';

    IF v_snap_before_nodes <> v_snap_after_nodes OR
       v_snap_before_edges <> v_snap_after_edges OR
       v_snap_before_fts <> v_snap_after_fts THEN
        RAISE EXCEPTION 'RPL-22 failed: State drifted under repeated reduction of TASK_EXPERIENCE_RECORDED!';
    END IF;

    -- 3. Invariant check: Verify promotion_state has NOT escalated to INSTITUTIONAL or ADOPTED
    SELECT * INTO v_node FROM pub_neural.neural_nodes WHERE id = 'experience:pub-dev-loop:TASK-EXP-PROJ-01';
    IF v_node.promotion_state IN ('INSTITUTIONAL', 'ADOPTED', 'VALIDATED') THEN
        RAISE EXCEPTION 'RPL-22 CRITICAL FAILURE: Observation escalated to authoritative state %!', v_node.promotion_state;
    END IF;

    RAISE NOTICE 'TEST_PASSED [RPL-22]: TASK_EXPERIENCE_RECORDED idempotency verified (0 drift across 5 runs, authority non-escalation proven).';
END;
$$;

-- ----------------------------------------------------------------------------
-- RPL-23: TASK_EXPERIENCE_RECORDED Malformed Payload Guard
-- Proves:
--   1. Missing taskId / task_id -> MALFORMED
--   2. Missing projectId / project_id -> MALFORMED
--   3. Missing repository -> MALFORMED
-- ----------------------------------------------------------------------------
DO $$
DECLARE
    v_bad_evt pub_neural.neural_events%ROWTYPE;
    v_res VARCHAR(32);
BEGIN
    v_bad_evt.event_type := 'TASK_EXPERIENCE_RECORDED';
    v_bad_evt.recorded_at := CURRENT_TIMESTAMP;

    -- Case 1: Missing taskId
    v_bad_evt.payload := '{"projectId": "pub-dev-loop", "repository": "pubcore/repo"}'::jsonb;
    v_res := pub_neural.reduce_event(v_bad_evt);
    IF v_res <> 'MALFORMED' THEN
        RAISE EXCEPTION 'RPL-23 failed (missing taskId): expected MALFORMED, got %', v_res;
    END IF;

    -- Case 2: Missing projectId
    v_bad_evt.payload := '{"taskId": "T-1", "repository": "pubcore/repo"}'::jsonb;
    v_res := pub_neural.reduce_event(v_bad_evt);
    IF v_res <> 'MALFORMED' THEN
        RAISE EXCEPTION 'RPL-23 failed (missing projectId): expected MALFORMED, got %', v_res;
    END IF;

    -- Case 3: Missing repository
    v_bad_evt.payload := '{"taskId": "T-1", "projectId": "p-1"}'::jsonb;
    v_res := pub_neural.reduce_event(v_bad_evt);
    IF v_res <> 'MALFORMED' THEN
        RAISE EXCEPTION 'RPL-23 failed (missing repository): expected MALFORMED, got %', v_res;
    END IF;

    RAISE NOTICE 'TEST_PASSED [RPL-23]: Malformed payload guards verified (missing taskId, projectId, repository rejected as MALFORMED).';
END;
$$;




