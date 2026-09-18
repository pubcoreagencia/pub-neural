-- PUB Neural V0.3 compatibility repair
-- Purpose: normalize legacy REPOSITORY_OBSERVED payloads at the reducer boundary.
-- Canonical event log remains immutable. No legacy event rows are rewritten.

CREATE OR REPLACE FUNCTION pub_neural.normalize_repository_observation_payload(p_payload JSONB)
RETURNS JSONB
LANGUAGE plpgsql
IMMUTABLE
SET search_path TO 'pg_catalog', 'pub_neural', 'public', 'extensions'
AS $fn$
DECLARE
    v_payload JSONB := p_payload;
    v_payload_hash TEXT;
BEGIN
    IF jsonb_typeof(v_payload) <> 'object' THEN
        RETURN v_payload;
    END IF;

    IF v_payload ? 'provenance'
       AND jsonb_typeof(v_payload->'provenance') = 'object'
       AND v_payload->'provenance'->>'delivery_id' IS NOT NULL
       AND v_payload->'provenance'->>'payload_hash' IS NOT NULL
       AND v_payload ? 'payload'
       AND jsonb_typeof(v_payload->'payload') = 'object'
    THEN
        RETURN v_payload;
    END IF;

    IF v_payload->>'delivery_id' IS NULL
       OR v_payload->>'repository' IS NULL
       OR v_payload->>'project_id' IS NULL
    THEN
        RETURN v_payload;
    END IF;

    v_payload_hash := COALESCE(
        v_payload->>'payload_hash',
        encode(digest(convert_to(v_payload::TEXT, 'UTF8'), 'sha256'), 'hex')
    );

    RETURN v_payload
        || jsonb_build_object(
            'payload',
            jsonb_build_object(
                'ref', v_payload->'ref',
                'sha', v_payload->'sha',
                'details', COALESCE(v_payload->'details', '{}'::jsonb)
            ),
            'provenance',
            jsonb_build_object(
                'delivery_id', v_payload->>'delivery_id',
                'received_at', COALESCE(v_payload->>'received_at', v_payload->>'observed_at'),
                'payload_hash', v_payload_hash
            )
        );
END;
$fn$;

DO $migration$
DECLARE
    v_def TEXT;
    v_start INTEGER;
    v_end INTEGER;
    v_branch TEXT;
BEGIN
    SELECT pg_get_functiondef(p.oid)
      INTO v_def
      FROM pg_proc p
      JOIN pg_namespace n ON n.oid = p.pronamespace
     WHERE n.nspname = 'pub_neural'
       AND p.proname = 'reduce_event'
       AND pg_get_function_identity_arguments(p.oid) = 'p_event pub_neural.neural_events';

    IF v_def IS NULL THEN
        RAISE EXCEPTION 'REPAIR_ABORTED: canonical reduce_event(p_event) function not found';
    END IF;

    v_start := strpos(v_def, '    -- 13. REPOSITORY_OBSERVED -> neural_repository_observations');
    v_end := v_start - 1
           + strpos(
               substr(v_def, v_start),
               '    -- Passthrough supported canonical events'
             );

    IF v_start = 0 OR v_end <= v_start THEN
        RAISE EXCEPTION 'REPAIR_ABORTED: expected REPOSITORY_OBSERVED reducer boundary not found';
    END IF;

    v_branch := $branch$
    -- 13. REPOSITORY_OBSERVED -> neural_repository_observations
    -- Compatibility boundary:
    -- legacy observation-sync events are normalized in-memory to the
    -- canonical provenance/payload contract. The append-only event itself
    -- remains untouched.
    ELSIF p_event.event_type = 'REPOSITORY_OBSERVED' THEN
        DECLARE
            v_observation JSONB := pub_neural.normalize_repository_observation_payload(p_event.payload);
        BEGIN
            IF v_observation->>'repository' IS NULL
               OR v_observation->>'project_id' IS NULL
               OR v_observation->'provenance'->>'delivery_id' IS NULL
               OR v_observation->'provenance'->>'payload_hash' IS NULL THEN
                RETURN 'MALFORMED';
            END IF;

            INSERT INTO pub_neural.neural_repository_observations (
                observation_id, event_id, repository, source, source_event_id,
                event_type, project_id, trust_zone, external_actor, internal_actor,
                observed_at, delivery_id, received_at, payload_hash, ref, sha,
                details, created_at
            ) VALUES (
                COALESCE(
                    (v_observation->>'observation_id')::uuid,
                    pub_neural.uuid_generate_v5(
                        v_ns,
                        'obs:' || (v_observation->'provenance'->>'delivery_id')
                    )
                ),
                p_event.id,
                v_observation->>'repository',
                COALESCE(v_observation->>'source', 'github'),
                v_observation->>'source_event_id',
                v_observation->>'event_type',
                v_observation->>'project_id',
                COALESCE(v_observation->>'trust_zone', 'tz_internal_holding'),
                v_observation->>'external_actor',
                COALESCE(v_observation->>'internal_actor', p_event.actor_id),
                COALESCE((v_observation->>'observed_at')::timestamptz, p_event.recorded_at),
                v_observation->'provenance'->>'delivery_id',
                COALESCE(
                    (v_observation->'provenance'->>'received_at')::timestamptz,
                    p_event.recorded_at
                ),
                v_observation->'provenance'->>'payload_hash',
                v_observation->'payload'->>'ref',
                v_observation->'payload'->>'sha',
                COALESCE(v_observation->'payload'->'details', '{}'::jsonb),
                p_event.recorded_at
            )
            ON CONFLICT (delivery_id) DO UPDATE SET
                event_id = EXCLUDED.event_id,
                details = EXCLUDED.details,
                repository = EXCLUDED.repository,
                project_id = EXCLUDED.project_id,
                ref = EXCLUDED.ref,
                sha = EXCLUDED.sha,
                observed_at = EXCLUDED.observed_at,
                external_actor = EXCLUDED.external_actor,
                internal_actor = EXCLUDED.internal_actor,
                received_at = EXCLUDED.received_at;

            RETURN 'SUPPORTED';
        END;

    $branch$;

    v_def := substr(v_def, 1, v_start - 1)
          || v_branch
          || substr(v_def, v_end);

    EXECUTE v_def;
END;
$migration$;

INSERT INTO pub_neural.neural_schema_versions (
    component, current_version, minimum_compatible_version, updated_at
) VALUES (
    'neural_repository_observations', '0.3.0', '0.2.0', CURRENT_TIMESTAMP
)
ON CONFLICT (component) DO UPDATE SET
    current_version = EXCLUDED.current_version,
    minimum_compatible_version = EXCLUDED.minimum_compatible_version,
    updated_at = EXCLUDED.updated_at;
