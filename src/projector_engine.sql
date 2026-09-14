-- ============================================================================
-- PUB NEURAL V0.1: HARDENED DETERMINISTIC PROJECTOR & REPLAY ENGINE (PL/pgSQL)
-- File: src/projector_engine.sql
-- Classification: OPERATIONAL PROJECTOR / REDUCER ENGINE (V0.1 BASELINE)
-- Target: PostgreSQL 16+
-- ============================================================================

\set ON_ERROR_STOP on

-- Namespace for UUIDv5 generation
-- Standard DNS namespace: 6ba7b810-9dad-11d1-80b4-00c04fd430c8
CREATE OR REPLACE FUNCTION pub_neural.uuid_generate_v5(
    p_namespace UUID,
    p_name TEXT
) RETURNS UUID
LANGUAGE plpgsql
IMMUTABLE
SET search_path = pg_catalog, pub_neural, public
AS $$
DECLARE
    v_hash bytea;
    v_bytes bytea;
BEGIN
    -- SHA-1 of namespace bytes concatenated with name bytes
    v_hash := digest(decode(replace(p_namespace::text, '-', ''), 'hex') || convert_to(p_name, 'UTF8'), 'sha1');
    v_bytes := substring(v_hash from 1 for 16);
    
    -- Set version to 5 (0101) in byte 7: (b & 0x0f) | 0x50
    v_bytes := set_byte(v_bytes, 6, (get_byte(v_bytes, 6) & 15) | 80);
    -- Set variant to RFC 4122 (10xx) in byte 9: (b & 0x3f) | 0x80
    v_bytes := set_byte(v_bytes, 8, (get_byte(v_bytes, 8) & 63) | 128);
    
    RETURN encode(v_bytes, 'hex')::uuid;
END;
$$;

CREATE OR REPLACE FUNCTION pub_neural.reduce_event(
    p_event_id UUID
) RETURNS VARCHAR(32)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, pub_neural, public
AS $$
DECLARE
    v_event pub_neural.neural_events%ROWTYPE;
BEGIN
    SELECT * INTO v_event FROM pub_neural.neural_events WHERE id = p_event_id;
    IF NOT FOUND THEN
        RETURN 'REJECTED';
    END IF;
    RETURN pub_neural.reduce_event(v_event);
END;
$$;

-- ----------------------------------------------------------------------------
-- REDUCER DISPATCHER: Processes a single canonical event deterministically
-- All projection timestamps are strictly derived from event.recorded_at
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION pub_neural.reduce_event(
    p_event pub_neural.neural_events
) RETURNS VARCHAR(32) -- 'SUPPORTED', 'UNSUPPORTED', 'MALFORMED', 'REJECTED'
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, pub_neural, public
AS $$
DECLARE
    v_ns UUID := '6ba7b810-9dad-11d1-80b4-00c04fd430c8'::uuid;
    v_src_id UUID;
    v_edge_id UUID;
    v_ev_id UUID;
    v_valid_from TIMESTAMPTZ;
    v_target_type VARCHAR(32);
    v_target_id VARCHAR(128);
    v_source_blob pub_neural.source_blobs%ROWTYPE;
    v_exp_node_id VARCHAR(128);
    v_finding_elem JSONB;
    v_finding_node_id VARCHAR(128);
    v_finding_idx INT;
    v_finding_type VARCHAR(64);
    v_finding_class pub_neural.neural_entity_type;
    v_finding_edge_id UUID;
BEGIN
    -- ------------------------------------------------------------------------
    -- 1. SOURCE_INGESTED -> neural_sources
    -- ------------------------------------------------------------------------
    IF p_event.event_type = 'SOURCE_INGESTED' THEN
        IF p_event.payload->>'file_sha256' IS NULL 
           OR p_event.payload->>'repository' IS NULL 
           OR p_event.payload->>'commit_sha' IS NULL 
           OR p_event.payload->>'file_path' IS NULL THEN
            RETURN 'MALFORMED';
        END IF;

        -- Lookup preserved blob metadata
        SELECT * INTO v_source_blob 
        FROM pub_neural.source_blobs 
        WHERE file_sha256 = (p_event.payload->>'file_sha256');

        IF NOT FOUND THEN
            RETURN 'REJECTED'; -- Invariant violation: blob manifest must exist
        END IF;

        -- Derive deterministic UUIDv5
        v_src_id := pub_neural.uuid_generate_v5(
            v_ns,
            (p_event.payload->>'repository') || ':' || 
            (p_event.payload->>'commit_sha') || ':' || 
            (p_event.payload->>'file_path')
        );

        INSERT INTO pub_neural.neural_sources (
            id, trust_zone, project_id, repository, branch, commit_sha, file_path,
            file_sha256, content_hash, storage_uri, mime_type, byte_size,
            observed_at, recorded_from, last_event_id, created_at
        ) VALUES (
            v_src_id,
            COALESCE(p_event.payload->>'trust_zone', 'tz_internal_holding'),
            COALESCE(p_event.payload->>'project_id', 'holding-core'),
            p_event.payload->>'repository',
            COALESCE(p_event.payload->>'branch', 'main'),
            p_event.payload->>'commit_sha',
            p_event.payload->>'file_path',
            v_source_blob.file_sha256,
            v_source_blob.content_hash,
            v_source_blob.storage_uri,
            v_source_blob.mime_type,
            v_source_blob.byte_size::INTEGER,
            COALESCE((p_event.payload->>'observed_at')::timestamptz, p_event.recorded_at),
            p_event.recorded_at,
            p_event.id,
            p_event.recorded_at
        )
        ON CONFLICT (repository, commit_sha, file_path) DO UPDATE SET
            file_sha256 = EXCLUDED.file_sha256,
            content_hash = EXCLUDED.content_hash,
            storage_uri = EXCLUDED.storage_uri,
            byte_size = EXCLUDED.byte_size,
            last_event_id = EXCLUDED.last_event_id,
            recorded_from = EXCLUDED.recorded_from;

        RETURN 'SUPPORTED';

    -- ------------------------------------------------------------------------
    -- 2. ENTITY_EXTRACTED -> neural_nodes & neural_fts
    -- ------------------------------------------------------------------------
    ELSIF p_event.event_type = 'ENTITY_EXTRACTED' THEN
        IF p_event.payload->>'node_id' IS NULL 
           OR p_event.payload->>'title' IS NULL 
           OR p_event.payload->>'entity_type' IS NULL THEN
            RETURN 'MALFORMED';
        END IF;

        v_valid_from := COALESCE((p_event.payload->>'valid_from')::timestamptz, p_event.recorded_at);

        INSERT INTO pub_neural.neural_nodes (
            id, entity_type, title, slug, summary, content, trust_zone, scope, project_id,
            promotion_state, conflict_state, confidence_score, valid_from, recorded_from,
            is_active, originating_event_id, last_transition_event_id, created_at, updated_at
        ) VALUES (
            p_event.payload->>'node_id',
            (p_event.payload->>'entity_type')::pub_neural.neural_entity_type,
            p_event.payload->>'title',
            COALESCE(p_event.payload->>'slug', lower(replace(p_event.payload->>'node_id', ':', '-'))),
            p_event.payload->>'summary',
            p_event.payload->>'content',
            COALESCE(p_event.payload->>'trust_zone', 'tz_internal_holding'),
            COALESCE(p_event.payload->>'scope', 'GLOBAL'),
            p_event.payload->>'project_id',
            COALESCE((p_event.payload->>'initial_state')::pub_neural.neural_promotion_state, 'EXTRACTED'),
            'RESOLVED',
            COALESCE((p_event.payload->>'confidence_score')::float, 1.0),
            v_valid_from,
            p_event.recorded_at,
            TRUE,
            p_event.id,
            p_event.id,
            p_event.recorded_at,
            p_event.recorded_at
        )
        ON CONFLICT (id) DO UPDATE SET
            title = EXCLUDED.title,
            summary = COALESCE(EXCLUDED.summary, neural_nodes.summary),
            content = COALESCE(EXCLUDED.content, neural_nodes.content),
            confidence_score = EXCLUDED.confidence_score,
            last_transition_event_id = EXCLUDED.last_transition_event_id,
            updated_at = p_event.recorded_at;

        -- FTS Projection Update (Deterministic Portuguese lexical indexing)
        INSERT INTO pub_neural.neural_fts (
            id, trust_zone, project_id, language_config, tsv_document, updated_at
        ) VALUES (
            p_event.payload->>'node_id',
            COALESCE(p_event.payload->>'trust_zone', 'tz_internal_holding'),
            p_event.payload->>'project_id',
            'portuguese',
            setweight(to_tsvector('portuguese', COALESCE(p_event.payload->>'title', '')), 'A') ||
            setweight(to_tsvector('portuguese', COALESCE(p_event.payload->>'summary', '')), 'B') ||
            setweight(to_tsvector('portuguese', COALESCE(p_event.payload->>'content', '')), 'C'),
            p_event.recorded_at
        )
        ON CONFLICT (id) DO UPDATE SET
            trust_zone = EXCLUDED.trust_zone,
            project_id = EXCLUDED.project_id,
            tsv_document = EXCLUDED.tsv_document,
            updated_at = p_event.recorded_at;

        RETURN 'SUPPORTED';

    -- ------------------------------------------------------------------------
    -- 3. KNOWLEDGE_CANDIDATE_CREATED -> promotion_state = 'CANDIDATE'
    -- ------------------------------------------------------------------------
    ELSIF p_event.event_type = 'KNOWLEDGE_CANDIDATE_CREATED' THEN
        IF p_event.payload->>'node_id' IS NULL THEN
            RETURN 'MALFORMED';
        END IF;

        UPDATE pub_neural.neural_nodes
        SET promotion_state = 'CANDIDATE',
            promotion_reason = p_event.payload->>'reason',
            last_transition_event_id = p_event.id,
            updated_at = p_event.recorded_at
        WHERE id = p_event.payload->>'node_id';

        RETURN 'SUPPORTED';

    -- ------------------------------------------------------------------------
    -- 4. KNOWLEDGE_VALIDATED -> promotion_state = 'VALIDATED'
    -- ------------------------------------------------------------------------
    ELSIF p_event.event_type = 'KNOWLEDGE_VALIDATED' THEN
        IF p_event.payload->>'target_id' IS NULL THEN
            RETURN 'MALFORMED';
        END IF;

        UPDATE pub_neural.neural_nodes
        SET promotion_state = 'VALIDATED',
            promotion_reason = 'Validated via ' || COALESCE(p_event.payload->>'verification_method', 'automated check'),
            last_transition_event_id = p_event.id,
            updated_at = p_event.recorded_at
        WHERE id = p_event.payload->>'target_id';

        RETURN 'SUPPORTED';

    -- ------------------------------------------------------------------------
    -- 5. KNOWLEDGE_SUPERSEDED -> supersedes previous node or edge
    -- ------------------------------------------------------------------------
    ELSIF p_event.event_type = 'KNOWLEDGE_SUPERSEDED' THEN
        IF p_event.payload->>'old_id' IS NULL OR p_event.payload->>'new_id' IS NULL THEN
            RETURN 'MALFORMED';
        END IF;

        -- Check if it's a node
        IF EXISTS (SELECT 1 FROM pub_neural.neural_nodes WHERE id = p_event.payload->>'old_id') THEN
            UPDATE pub_neural.neural_nodes
            SET is_active = FALSE,
                conflict_state = 'SUPERSEDED',
                superseded_by = p_event.payload->>'new_id',
                valid_until = COALESCE((p_event.payload->>'valid_from')::timestamptz, p_event.recorded_at),
                recorded_until = p_event.recorded_at,
                last_transition_event_id = p_event.id,
                updated_at = p_event.recorded_at
            WHERE id = p_event.payload->>'old_id';

            RETURN 'SUPPORTED';
        ELSE
            RETURN 'REJECTED';
        END IF;

    -- ------------------------------------------------------------------------
    -- 6. KNOWLEDGE_REJECTED -> conflict_state = 'REJECTED'
    -- ------------------------------------------------------------------------
    ELSIF p_event.event_type = 'KNOWLEDGE_REJECTED' THEN
        IF p_event.payload->>'target_id' IS NULL THEN
            RETURN 'MALFORMED';
        END IF;

        UPDATE pub_neural.neural_nodes
        SET conflict_state = 'REJECTED',
            is_active = FALSE,
            promotion_reason = p_event.payload->>'rejection_reason',
            last_transition_event_id = p_event.id,
            updated_at = p_event.recorded_at
        WHERE id = p_event.payload->>'target_id';

        RETURN 'SUPPORTED';

    -- ------------------------------------------------------------------------
    -- 7. PROMOTION_PROPOSED -> promotion_state = 'INSTITUTIONAL_CANDIDATE'
    -- ------------------------------------------------------------------------
    ELSIF p_event.event_type = 'PROMOTION_PROPOSED' THEN
        IF p_event.payload->>'target_id' IS NULL THEN
            RETURN 'MALFORMED';
        END IF;

        UPDATE pub_neural.neural_nodes
        SET promotion_state = 'INSTITUTIONAL_CANDIDATE',
            promotion_reason = p_event.payload->>'justifications',
            last_transition_event_id = p_event.id,
            updated_at = p_event.recorded_at
        WHERE id = p_event.payload->>'target_id';

        RETURN 'SUPPORTED';

    -- ------------------------------------------------------------------------
    -- 8. DECISION_RATIFIED -> promotion_state = 'INSTITUTIONAL'
    -- ------------------------------------------------------------------------
    ELSIF p_event.event_type = 'DECISION_RATIFIED' THEN
        IF p_event.payload->>'decision_id' IS NULL THEN
            RETURN 'MALFORMED';
        END IF;

        UPDATE pub_neural.neural_nodes
        SET promotion_state = 'INSTITUTIONAL',
            conflict_state = 'RESOLVED',
            is_active = TRUE,
            promotion_reason = 'Ratified by CEO: ' || COALESCE(p_event.payload->>'ratified_choice', ''),
            last_transition_event_id = p_event.id,
            updated_at = p_event.recorded_at
        WHERE id = p_event.payload->>'decision_id';

        RETURN 'SUPPORTED';

    -- ------------------------------------------------------------------------
    -- 9. GOVERNANCE_RULE_RATIFIED -> Rule active & institutional
    -- ------------------------------------------------------------------------
    ELSIF p_event.event_type = 'GOVERNANCE_RULE_RATIFIED' THEN
        IF p_event.payload->>'rule_id' IS NULL THEN
            RETURN 'MALFORMED';
        END IF;

        UPDATE pub_neural.neural_nodes
        SET promotion_state = 'INSTITUTIONAL',
            conflict_state = 'RESOLVED',
            is_active = TRUE,
            promotion_reason = 'Ratified by CEO governance mandate: ' || COALESCE(p_event.payload->>'compliance_mandate', ''),
            last_transition_event_id = p_event.id,
            updated_at = p_event.recorded_at
        WHERE id = p_event.payload->>'rule_id';

        RETURN 'SUPPORTED';

    -- ------------------------------------------------------------------------
    -- 10. RELATION_EXTRACTED -> neural_edges
    -- ------------------------------------------------------------------------
    ELSIF p_event.event_type = 'RELATION_EXTRACTED' THEN
        IF p_event.payload->>'source_id' IS NULL 
           OR p_event.payload->>'target_id' IS NULL 
           OR p_event.payload->>'relation_type' IS NULL THEN
            RETURN 'MALFORMED';
        END IF;

        -- Verify both endpoints exist in neural_nodes
        IF NOT EXISTS (SELECT 1 FROM pub_neural.neural_nodes WHERE id = p_event.payload->>'source_id')
           OR NOT EXISTS (SELECT 1 FROM pub_neural.neural_nodes WHERE id = p_event.payload->>'target_id') THEN
            RETURN 'REJECTED'; -- Cannot project edge if endpoints are missing
        END IF;

        v_valid_from := COALESCE((p_event.payload->>'valid_from')::timestamptz, p_event.recorded_at);

        -- Deterministic UUIDv5 for edge
        v_edge_id := pub_neural.uuid_generate_v5(
            v_ns,
            (p_event.payload->>'source_id') || ':' || 
            (p_event.payload->>'relation_type') || ':' || 
            (p_event.payload->>'target_id') || ':' || 
            v_valid_from::text
        );

        INSERT INTO pub_neural.neural_edges (
            id, source_id, target_id, relation_type, weight, is_bidirectional,
            trust_zone, scope, valid_from, recorded_from, is_active,
            originating_event_id, last_transition_event_id, created_at, updated_at
        ) VALUES (
            v_edge_id,
            p_event.payload->>'source_id',
            p_event.payload->>'target_id',
            (p_event.payload->>'relation_type')::pub_neural.neural_relation_type,
            COALESCE((p_event.payload->>'weight')::float, 1.0),
            COALESCE((p_event.payload->>'is_bidirectional')::boolean, FALSE),
            COALESCE(p_event.payload->>'trust_zone', 'tz_internal_holding'),
            COALESCE(p_event.payload->>'scope', 'GLOBAL'),
            v_valid_from,
            p_event.recorded_at,
            TRUE,
            p_event.id,
            p_event.id,
            p_event.recorded_at,
            p_event.recorded_at
        )
        ON CONFLICT (source_id, relation_type, target_id, valid_from, recorded_from) DO UPDATE SET
            weight = EXCLUDED.weight,
            last_transition_event_id = EXCLUDED.last_transition_event_id,
            updated_at = p_event.recorded_at;

        RETURN 'SUPPORTED';

    -- ------------------------------------------------------------------------
    -- 11. EVIDENCE_CAPTURED -> neural_evidence
    -- ------------------------------------------------------------------------
    ELSIF p_event.event_type = 'EVIDENCE_CAPTURED' THEN
        IF p_event.payload->>'target_type' IS NULL 
           OR p_event.payload->>'target_id' IS NULL 
           OR p_event.payload->>'source_id' IS NULL 
           OR p_event.payload->>'content_hash' IS NULL THEN
            RETURN 'MALFORMED';
        END IF;

        v_target_type := p_event.payload->>'target_type';
        v_target_id := p_event.payload->>'target_id';

        -- Deterministic UUIDv5
        v_ev_id := pub_neural.uuid_generate_v5(
            v_ns,
            v_target_type || ':' || v_target_id || ':' || 
            (p_event.payload->>'source_id') || ':' || 
            (p_event.payload->>'content_hash')
        );

        -- Verify source_id exists in neural_sources
        IF NOT EXISTS (SELECT 1 FROM pub_neural.neural_sources WHERE id = (p_event.payload->>'source_id')::uuid) THEN
            RETURN 'REJECTED';
        END IF;

        IF v_target_type = 'NODE' THEN
            IF NOT EXISTS (SELECT 1 FROM pub_neural.neural_nodes WHERE id = v_target_id) THEN
                RETURN 'REJECTED';
            END IF;

            INSERT INTO pub_neural.neural_evidence (
                id, node_id, edge_id, source_id, trust_zone, project_id,
                content_hash, start_line, end_line, exact_quote, context_before, context_after,
                confidence, validation_state, extractor_version, originating_event_id, created_at
            ) VALUES (
                v_ev_id,
                v_target_id,
                NULL,
                (p_event.payload->>'source_id')::uuid,
                COALESCE(p_event.payload->>'trust_zone', 'tz_internal_holding'),
                p_event.payload->>'project_id',
                p_event.payload->>'content_hash',
                COALESCE((p_event.payload->>'start_line')::integer, 1),
                COALESCE((p_event.payload->>'end_line')::integer, 1),
                COALESCE(p_event.payload->>'quote', ''),
                p_event.payload->>'context_before',
                p_event.payload->>'context_after',
                COALESCE((p_event.payload->>'confidence')::float, 1.0),
                COALESCE(p_event.payload->>'validation_state', 'UNVERIFIED'),
                COALESCE(p_event.payload->>'extractor_version', 'v1.0'),
                p_event.id,
                p_event.recorded_at
            )
            ON CONFLICT (id) DO NOTHING;

            RETURN 'SUPPORTED';

        ELSIF v_target_type = 'EDGE' THEN
            IF NOT EXISTS (SELECT 1 FROM pub_neural.neural_edges WHERE id = v_target_id::uuid) THEN
                RETURN 'REJECTED';
            END IF;

            INSERT INTO pub_neural.neural_evidence (
                id, node_id, edge_id, source_id, trust_zone, project_id,
                content_hash, start_line, end_line, exact_quote, context_before, context_after,
                confidence, validation_state, extractor_version, originating_event_id, created_at
            ) VALUES (
                v_ev_id,
                NULL,
                v_target_id::uuid,
                (p_event.payload->>'source_id')::uuid,
                COALESCE(p_event.payload->>'trust_zone', 'tz_internal_holding'),
                p_event.payload->>'project_id',
                p_event.payload->>'content_hash',
                COALESCE((p_event.payload->>'start_line')::integer, 1),
                COALESCE((p_event.payload->>'end_line')::integer, 1),
                COALESCE(p_event.payload->>'quote', ''),
                p_event.payload->>'context_before',
                p_event.payload->>'context_after',
                COALESCE((p_event.payload->>'confidence')::float, 1.0),
                COALESCE(p_event.payload->>'validation_state', 'UNVERIFIED'),
                COALESCE(p_event.payload->>'extractor_version', 'v1.0'),
                p_event.id,
                p_event.recorded_at
            )
            ON CONFLICT (id) DO NOTHING;

            RETURN 'SUPPORTED';
        ELSE
            RETURN 'MALFORMED';
        END IF;

    -- ------------------------------------------------------------------------
    -- 12. TASK_EXPERIENCE_RECORDED -> neural_nodes, neural_edges, neural_fts
    -- Governed Observational/Candidate Projection (V0.1)
    -- Preserves task identity, commit, repository, validation, and candidate findings.
    -- Never escalates authority beyond CANDIDATE/OBSERVED.
    -- ------------------------------------------------------------------------
    ELSIF p_event.event_type = 'TASK_EXPERIENCE_RECORDED' THEN
        IF (p_event.payload->>'taskId' IS NULL AND p_event.payload->>'task_id' IS NULL)
           OR (p_event.payload->>'projectId' IS NULL AND p_event.payload->>'project_id' IS NULL)
           OR p_event.payload->>'repository' IS NULL THEN
            RETURN 'MALFORMED';
        END IF;

        v_exp_node_id := 'experience:' || COALESCE(p_event.payload->>'projectId', p_event.payload->>'project_id') || ':' || COALESCE(p_event.payload->>'taskId', p_event.payload->>'task_id');
        v_valid_from := COALESCE((p_event.payload->>'completedAt')::timestamptz, (p_event.payload->>'completed_at')::timestamptz, p_event.recorded_at);

        -- 12.1 Project primary task experience node
        INSERT INTO pub_neural.neural_nodes (
            id, entity_type, title, slug, summary, content, trust_zone, scope, project_id,
            promotion_state, promotion_reason, conflict_state, confidence_score, valid_from, recorded_from,
            is_active, originating_event_id, last_transition_event_id, created_at, updated_at
        ) VALUES (
            v_exp_node_id,
            'LESSON',
            'Task Experience: ' || COALESCE(p_event.payload->>'taskId', p_event.payload->>'task_id'),
            lower(replace(v_exp_node_id, ':', '-')),
            COALESCE(p_event.payload->>'objective', 'Task execution recorded'),
            'Task ' || COALESCE(p_event.payload->>'taskId', p_event.payload->>'task_id') ||
            ' completed with status ' || COALESCE(p_event.payload->>'status', 'UNKNOWN') ||
            ' in repository ' || (p_event.payload->>'repository') ||
            ' on branch ' || COALESCE(p_event.payload->>'branch', 'main') ||
            CASE WHEN p_event.payload->>'commitSha' IS NOT NULL OR p_event.payload->>'commit_sha' IS NOT NULL
                 THEN ' at commit ' || COALESCE(p_event.payload->>'commitSha', p_event.payload->>'commit_sha')
                 ELSE '' END || '.',
            COALESCE(p_event.payload->>'trust_zone', 'tz_internal_holding'),
            'PROJECT',
            COALESCE(p_event.payload->>'projectId', p_event.payload->>'project_id'),
            'OBSERVED',
            'Recorded via PDL experience gate',
            'RESOLVED',
            1.0,
            v_valid_from,
            p_event.recorded_at,
            TRUE,
            p_event.id,
            p_event.id,
            p_event.recorded_at,
            p_event.recorded_at
        )
        ON CONFLICT (id) DO UPDATE SET
            summary = EXCLUDED.summary,
            content = EXCLUDED.content,
            last_transition_event_id = EXCLUDED.last_transition_event_id,
            updated_at = p_event.recorded_at
        WHERE pub_neural.neural_nodes.promotion_state IN ('CAPTURED', 'OBSERVED', 'EXTRACTED', 'CANDIDATE');

        -- 12.2 Update FTS index for primary experience node
        INSERT INTO pub_neural.neural_fts (
            id, trust_zone, project_id, language_config, tsv_document, updated_at
        ) VALUES (
            v_exp_node_id,
            COALESCE(p_event.payload->>'trust_zone', 'tz_internal_holding'),
            COALESCE(p_event.payload->>'projectId', p_event.payload->>'project_id'),
            'portuguese',
            setweight(to_tsvector('portuguese', 'Task Experience: ' || COALESCE(p_event.payload->>'taskId', p_event.payload->>'task_id')), 'A') ||
            setweight(to_tsvector('portuguese', COALESCE(p_event.payload->>'objective', '')), 'B') ||
            setweight(to_tsvector('portuguese', (p_event.payload->>'repository') || ' ' || COALESCE(p_event.payload->>'branch', '') || ' ' || COALESCE(p_event.payload->>'commitSha', p_event.payload->>'commit_sha', '')), 'C'),
            p_event.recorded_at
        )
        ON CONFLICT (id) DO UPDATE SET
            trust_zone = EXCLUDED.trust_zone,
            project_id = EXCLUDED.project_id,
            tsv_document = EXCLUDED.tsv_document,
            updated_at = p_event.recorded_at;

        -- 12.2b Enqueue durable vector indexing job for primary experience node (asynchronous)
        INSERT INTO pub_neural.neural_vector_index_jobs (
            node_id, target_type, status, available_at, updated_at
        ) VALUES (
            v_exp_node_id, 'NODE', 'PENDING', p_event.recorded_at, p_event.recorded_at
        )
        ON CONFLICT (node_id) DO UPDATE SET
            status = CASE
                WHEN pub_neural.neural_vector_index_jobs.status IN ('COMPLETED', 'PROCESSING')
                     THEN pub_neural.neural_vector_index_jobs.status
                ELSE 'PENDING'
            END,
            available_at = CASE
                WHEN pub_neural.neural_vector_index_jobs.status IN ('COMPLETED', 'PROCESSING')
                     THEN pub_neural.neural_vector_index_jobs.available_at
                ELSE p_event.recorded_at
            END,
            updated_at = p_event.recorded_at;

        -- 12.3 Project candidate findings if present in payload
        IF (p_event.payload ? 'candidateFindings' AND jsonb_typeof(p_event.payload->'candidateFindings') = 'array')
           OR (p_event.payload ? 'candidate_findings' AND jsonb_typeof(p_event.payload->'candidate_findings') = 'array') THEN
            v_finding_idx := 0;
            FOR v_finding_elem IN SELECT * FROM jsonb_array_elements(COALESCE(p_event.payload->'candidateFindings', p_event.payload->'candidate_findings'))
            LOOP
                v_finding_idx := v_finding_idx + 1;
                v_finding_node_id := 'finding:' || COALESCE(p_event.payload->>'projectId', p_event.payload->>'project_id') || ':' || COALESCE(p_event.payload->>'taskId', p_event.payload->>'task_id') || ':' || v_finding_idx::text;
                
                v_finding_type := COALESCE(v_finding_elem->>'finding_type', v_finding_elem->>'findingType', 'LESSON');
                IF v_finding_type = 'PATTERN' THEN
                    v_finding_class := 'PATTERN'::pub_neural.neural_entity_type;
                ELSE
                    v_finding_class := 'LESSON'::pub_neural.neural_entity_type;
                END IF;

                INSERT INTO pub_neural.neural_nodes (
                    id, entity_type, title, slug, summary, content, trust_zone, scope, project_id,
                    promotion_state, promotion_reason, conflict_state, confidence_score, valid_from, recorded_from,
                    is_active, originating_event_id, last_transition_event_id, created_at, updated_at
                ) VALUES (
                    v_finding_node_id,
                    v_finding_class,
                    COALESCE(v_finding_elem->>'title', 'Candidate Finding ' || v_finding_idx::text),
                    lower(replace(v_finding_node_id, ':', '-')),
                    COALESCE(v_finding_elem->>'statement', v_finding_elem->>'title', ''),
                    COALESCE(v_finding_elem->>'statement', ''),
                    COALESCE(p_event.payload->>'trust_zone', 'tz_internal_holding'),
                    COALESCE(v_finding_elem->>'scope', 'PROJECT'),
                    COALESCE(p_event.payload->>'projectId', p_event.payload->>'project_id'),
                    'CANDIDATE',
                    'Discovered during task ' || COALESCE(p_event.payload->>'taskId', p_event.payload->>'task_id'),
                    'RESOLVED',
                    COALESCE((v_finding_elem->>'confidence')::float, 1.0),
                    v_valid_from,
                    p_event.recorded_at,
                    TRUE,
                    p_event.id,
                    p_event.id,
                    p_event.recorded_at,
                    p_event.recorded_at
                )
                ON CONFLICT (id) DO UPDATE SET
                    title = EXCLUDED.title,
                    summary = EXCLUDED.summary,
                    content = EXCLUDED.content,
                    confidence_score = EXCLUDED.confidence_score,
                    last_transition_event_id = EXCLUDED.last_transition_event_id,
                    updated_at = p_event.recorded_at
                WHERE pub_neural.neural_nodes.promotion_state IN ('CAPTURED', 'OBSERVED', 'EXTRACTED', 'CANDIDATE');

                -- FTS for candidate finding
                INSERT INTO pub_neural.neural_fts (
                    id, trust_zone, project_id, language_config, tsv_document, updated_at
                ) VALUES (
                    v_finding_node_id,
                    COALESCE(p_event.payload->>'trust_zone', 'tz_internal_holding'),
                    COALESCE(p_event.payload->>'projectId', p_event.payload->>'project_id'),
                    'portuguese',
                    setweight(to_tsvector('portuguese', COALESCE(v_finding_elem->>'title', '')), 'A') ||
                    setweight(to_tsvector('portuguese', COALESCE(v_finding_elem->>'statement', '')), 'B'),
                    p_event.recorded_at
                )
                ON CONFLICT (id) DO UPDATE SET
                    trust_zone = EXCLUDED.trust_zone,
                    project_id = EXCLUDED.project_id,
                    tsv_document = EXCLUDED.tsv_document,
                    updated_at = p_event.recorded_at;

                -- Enqueue durable vector indexing job for candidate finding (asynchronous)
                INSERT INTO pub_neural.neural_vector_index_jobs (
                    node_id, target_type, status, available_at, updated_at
                ) VALUES (
                    v_finding_node_id, 'NODE', 'PENDING', p_event.recorded_at, p_event.recorded_at
                )
                ON CONFLICT (node_id) DO UPDATE SET
                    status = CASE
                        WHEN pub_neural.neural_vector_index_jobs.status IN ('COMPLETED', 'PROCESSING')
                             THEN pub_neural.neural_vector_index_jobs.status
                        ELSE 'PENDING'
                    END,
                    available_at = CASE
                        WHEN pub_neural.neural_vector_index_jobs.status IN ('COMPLETED', 'PROCESSING')
                             THEN pub_neural.neural_vector_index_jobs.available_at
                        ELSE p_event.recorded_at
                    END,
                    updated_at = p_event.recorded_at;

                -- Edge: finding DERIVED_FROM experience node
                v_finding_edge_id := pub_neural.uuid_generate_v5(
                    v_ns,
                    v_finding_node_id || ':DERIVED_FROM:' || v_exp_node_id
                );

                INSERT INTO pub_neural.neural_edges (
                    id, source_id, target_id, relation_type, weight, is_bidirectional,
                    trust_zone, scope, valid_from, recorded_from, is_active,
                    originating_event_id, last_transition_event_id, created_at, updated_at
                ) VALUES (
                    v_finding_edge_id,
                    v_finding_node_id,
                    v_exp_node_id,
                    'DERIVED_FROM',
                    COALESCE((v_finding_elem->>'confidence')::float, 1.0),
                    FALSE,
                    COALESCE(p_event.payload->>'trust_zone', 'tz_internal_holding'),
                    COALESCE(v_finding_elem->>'scope', 'PROJECT'),
                    v_valid_from,
                    p_event.recorded_at,
                    TRUE,
                    p_event.id,
                    p_event.id,
                    p_event.recorded_at,
                    p_event.recorded_at
                )
                ON CONFLICT (id) DO NOTHING;
            END LOOP;
        END IF;

        RETURN 'SUPPORTED';

    -- ------------------------------------------------------------------------
    -- Passthrough supported canonical events (manifest/bootstrap/governance)
    -- ------------------------------------------------------------------------
    ELSIF p_event.event_type IN (
        'GENESIS_BOOTSTRAP',
        'SOURCE_BLOB_VERIFIED',
        'SOURCE_DISCOVERED',
        'DOCUMENT_CAPTURED',
        'DOCUMENT_PARSED',
        'DECISION_PROPOSED',
        'GOVERNANCE_RULE_PROPOSED',
        'ACTOR_REGISTERED',
        'ACTOR_REVOKED'
    ) THEN
        RETURN 'SUPPORTED'; -- Recorded in canonical log, no direct projection modification required

    ELSE
        RETURN 'UNSUPPORTED';
    END IF;
END;
$$;

-- ----------------------------------------------------------------------------
-- RUN PROJECTOR / REPLAY ENGINE FUNCTION (V0.1 HARDENED)
-- Concurrency: Transactional advisory lock per projector_name
-- Checkpoint semantics: Safe advance only upon successful event reduction
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION pub_neural.run_projector(
    p_projector_name VARCHAR(64) DEFAULT 'graph_projector',
    p_from_sequence BIGINT DEFAULT NULL,
    p_to_sequence BIGINT DEFAULT NULL
) RETURNS TABLE (
    events_processed BIGINT,
    events_failed BIGINT,
    last_sequence BIGINT,
    status VARCHAR(32)
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, pub_neural, public
AS $$
DECLARE
    v_last_checkpoint BIGINT := 0;
    v_last_event_id UUID;
    v_start_seq BIGINT;
    v_event pub_neural.neural_events%ROWTYPE;
    v_res VARCHAR(32);
    v_count BIGINT := 0;
    v_fail_count BIGINT := 0;
    v_current_seq BIGINT := 0;
    v_current_event_id UUID;
    v_error_msg TEXT;
BEGIN
    -- 1. Enforce single-worker execution per projector via advisory lock
    PERFORM pg_advisory_xact_lock(hashtext('projector_lock:' || p_projector_name));

    -- Input validation on sequence range
    IF p_from_sequence IS NOT NULL AND p_to_sequence IS NOT NULL AND p_from_sequence > p_to_sequence THEN
        RAISE EXCEPTION 'Invalid sequence range: p_from_sequence (%) cannot exceed p_to_sequence (%)',
            p_from_sequence, p_to_sequence;
    END IF;

    -- 2. Determine start sequence from checkpoint if not explicitly provided
    SELECT last_processed_global_sequence, last_processed_event_id 
    INTO v_last_checkpoint, v_last_event_id
    FROM pub_neural.neural_projection_checkpoints
    WHERE projector_name = p_projector_name;

    IF v_last_checkpoint IS NOT NULL AND v_last_checkpoint > 0 THEN
        IF p_from_sequence IS NOT NULL AND p_from_sequence <= v_last_checkpoint THEN
            RAISE EXCEPTION 'HISTORICAL_REPLAY_FORBIDDEN: requested range (from %) precedes current projector checkpoint (%) on live projection. Use full_replay() for historical recomputation.',
                p_from_sequence, v_last_checkpoint;
        END IF;
    END IF;

    IF p_from_sequence IS NOT NULL THEN
        v_start_seq := p_from_sequence;
    ELSE
        v_start_seq := COALESCE(v_last_checkpoint + 1, 1);
    END IF;

    -- Track current committed sequence position (anchored to stored checkpoint)
    v_current_seq := COALESCE(v_last_checkpoint, 0);

    -- 3. Iterate ordered strictly by global_sequence ASC (Canonical replay order)
    FOR v_event IN 
        SELECT * FROM pub_neural.neural_events
        WHERE global_sequence >= v_start_seq
          AND (p_to_sequence IS NULL OR global_sequence <= p_to_sequence)
        ORDER BY global_sequence ASC
    LOOP
        BEGIN
            -- Test-only controlled interception point: if GUC pub_neural.test_pause_at_sequence matches
            IF current_setting('pub_neural.test_pause_at_sequence', true) IS NOT NULL 
               AND current_setting('pub_neural.test_pause_at_sequence', true) = v_event.global_sequence::text THEN
                PERFORM pg_sleep(COALESCE(current_setting('pub_neural.test_pause_duration', true)::numeric, 10.0));
            END IF;

            v_res := pub_neural.reduce_event(v_event);

            IF v_res IN ('MALFORMED', 'UNSUPPORTED', 'REJECTED') THEN
                v_fail_count := v_fail_count + 1;
                -- Record checkpoint error state WITHOUT advancing last_processed_global_sequence
                INSERT INTO pub_neural.neural_projection_checkpoints (
                    projector_name, last_processed_global_sequence, last_processed_event_id,
                    last_checkpoint_at, status, error_detail
                ) VALUES (
                    p_projector_name, v_current_seq, v_last_event_id,
                    CURRENT_TIMESTAMP, 'STALLED', 'Event ' || v_event.id || ' sequence ' || v_event.global_sequence || ' status: ' || v_res
                )
                ON CONFLICT (projector_name) DO UPDATE SET
                    last_checkpoint_at = CURRENT_TIMESTAMP,
                    status = 'STALLED',
                    error_detail = EXCLUDED.error_detail;

                RETURN QUERY SELECT v_count, v_fail_count, v_current_seq, 'STALLED'::VARCHAR(32);
                RETURN;
            END IF;

            -- Successful reduction: Advance checkpoint strictly monotonically
            v_count := v_count + 1;
            v_current_seq := v_event.global_sequence;
            v_last_event_id := v_event.id;

            INSERT INTO pub_neural.neural_projection_checkpoints (
                projector_name, last_processed_global_sequence, last_processed_event_id,
                last_checkpoint_at, status, error_detail
            ) VALUES (
                p_projector_name, v_current_seq, v_last_event_id,
                CURRENT_TIMESTAMP, 'HEALTHY', NULL
            )
            ON CONFLICT (projector_name) DO UPDATE SET
                last_processed_global_sequence = EXCLUDED.last_processed_global_sequence,
                last_processed_event_id = EXCLUDED.last_processed_event_id,
                last_checkpoint_at = CURRENT_TIMESTAMP,
                status = 'HEALTHY',
                error_detail = NULL;

        EXCEPTION WHEN OTHERS THEN
            GET STACKED DIAGNOSTICS v_error_msg = MESSAGE_TEXT;
            v_fail_count := v_fail_count + 1;

            -- On exception, checkpoint retains previous valid v_current_seq
            INSERT INTO pub_neural.neural_projection_checkpoints (
                projector_name, last_processed_global_sequence, last_processed_event_id,
                last_checkpoint_at, status, error_detail
            ) VALUES (
                p_projector_name, v_current_seq, v_last_event_id,
                CURRENT_TIMESTAMP, 'ERROR', v_error_msg
            )
            ON CONFLICT (projector_name) DO UPDATE SET
                last_checkpoint_at = CURRENT_TIMESTAMP,
                status = 'ERROR',
                error_detail = v_error_msg;

            RETURN QUERY SELECT v_count, v_fail_count, v_current_seq, 'ERROR'::VARCHAR(32);
            RETURN;
        END;
    END LOOP;

    RETURN QUERY SELECT v_count, v_fail_count, v_current_seq, 'HEALTHY'::VARCHAR(32);
END;
$$;

-- ----------------------------------------------------------------------------
-- FULL REPLAY ENGINE: Drops projections and reconstructs from scratch
-- Restores deterministic state by replaying canonical event stream
-- Authorized roles: pub_neural_admin, pub_neural_ceo
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION pub_neural.full_replay(
    p_projector_name VARCHAR(64) DEFAULT 'graph_projector'
) RETURNS TABLE (
    events_replayed BIGINT,
    last_sequence BIGINT,
    status VARCHAR(32)
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, pub_neural, public
AS $$
DECLARE
    v_res RECORD;
BEGIN
    -- Explicit security authorization: only admin or ceo may execute destructive full replay
    IF SESSION_USER NOT IN ('pub_neural_admin', 'pub_neural_ceo', 'postgres') THEN
        RAISE EXCEPTION 'Authorization failed: full_replay requires pub_neural_admin or pub_neural_ceo role';
    END IF;

    -- 1. Truncate/wipe derived projections
    TRUNCATE TABLE pub_neural.neural_evidence CASCADE;
    TRUNCATE TABLE pub_neural.neural_edges CASCADE;
    TRUNCATE TABLE pub_neural.neural_fts CASCADE;
    TRUNCATE TABLE pub_neural.neural_nodes CASCADE;
    TRUNCATE TABLE pub_neural.neural_sources CASCADE;

    -- Reset projector checkpoint
    DELETE FROM pub_neural.neural_projection_checkpoints WHERE projector_name = p_projector_name;

    -- 2. Replay all events from sequence 1
    SELECT * INTO v_res FROM pub_neural.run_projector(p_projector_name, 1, NULL);

    -- MODELO A — ATOMIC FULL REPLAY ENFORCEMENT:
    -- If replay did not complete with HEALTHY status (e.g. stalled or error on bad event),
    -- abort transaction so TRUNCATE and partial changes are completely rolled back!
    IF v_res.status <> 'HEALTHY' THEN
        RAISE EXCEPTION 'FULL_REPLAY_FAILED: Replay of projector % halted with status % at sequence % (events processed: %, failed: %). Full replay rolled back atomically.',
            p_projector_name, v_res.status, v_res.last_sequence, v_res.events_processed, v_res.events_failed;
    END IF;

    RETURN QUERY SELECT v_res.events_processed, v_res.last_sequence, v_res.status;
END;
$$;

-- Explicit privilege lockdown on projector engine functions
REVOKE ALL ON FUNCTION pub_neural.uuid_generate_v5(UUID, TEXT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION pub_neural.uuid_generate_v5(UUID, TEXT) TO pub_neural_app, pub_neural_projector, pub_neural_admin, pub_neural_ceo;

REVOKE ALL ON FUNCTION pub_neural.reduce_event(pub_neural.neural_events) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION pub_neural.reduce_event(pub_neural.neural_events) TO pub_neural_projector, pub_neural_admin, pub_neural_ceo;

REVOKE ALL ON FUNCTION pub_neural.reduce_event(UUID) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION pub_neural.reduce_event(UUID) TO pub_neural_projector, pub_neural_admin, pub_neural_ceo;

REVOKE ALL ON FUNCTION pub_neural.run_projector(VARCHAR, BIGINT, BIGINT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION pub_neural.run_projector(VARCHAR, BIGINT, BIGINT) TO pub_neural_projector, pub_neural_admin, pub_neural_ceo;

REVOKE ALL ON FUNCTION pub_neural.full_replay(VARCHAR) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION pub_neural.full_replay(VARCHAR) TO pub_neural_admin, pub_neural_ceo;
