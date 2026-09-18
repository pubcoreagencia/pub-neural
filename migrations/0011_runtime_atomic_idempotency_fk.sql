-- ============================================================================
-- PUB NEURAL V0 CANONICAL DATABASE MIGRATION
-- Migration File: 0011_runtime_atomic_idempotency_fk.sql
-- Classification: RUNTIME ATOMIC IDEMPOTENCY
-- ============================================================================

\set ON_ERROR_STOP on

-- Runtime ingestion claims the idempotency key before appending the canonical
-- event so concurrent callers serialize on the PK. The event FK therefore must
-- be checked at transaction commit, after the event has been appended.
ALTER TABLE pub_neural.neural_idempotency_records
    DROP CONSTRAINT IF EXISTS neural_idempotency_records_resulting_event_id_fkey;

ALTER TABLE pub_neural.neural_idempotency_records
    ADD CONSTRAINT neural_idempotency_records_resulting_event_id_fkey
    FOREIGN KEY (resulting_event_id)
    REFERENCES pub_neural.neural_events(id)
    ON DELETE RESTRICT
    DEFERRABLE INITIALLY DEFERRED;

INSERT INTO pub_neural.neural_schema_versions (
    component, current_version, minimum_compatible_version, updated_at
) VALUES (
    'runtime_atomic_idempotency', '1.0.0', '1.0.0', CURRENT_TIMESTAMP
)
ON CONFLICT (component) DO UPDATE SET
    current_version = EXCLUDED.current_version,
    minimum_compatible_version = EXCLUDED.minimum_compatible_version,
    updated_at = CURRENT_TIMESTAMP;
