-- ============================================================================
-- PUB NEURAL V0 CANONICAL DATABASE MIGRATION
-- Migration File: 0010_observation_scheduler_hardening_v0_5_1.sql
-- Classification: CONTINUOUS OBSERVATION SCHEDULER & HARDENING (V0.5.1)
-- Target: PostgreSQL 16+ / 17+
-- ============================================================================

\set ON_ERROR_STOP on

ALTER TABLE pub_neural.observation_sync_runs
    ADD COLUMN IF NOT EXISTS consecutive_failures INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS last_success_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS last_failure_at TIMESTAMPTZ;

-- Record schema version
INSERT INTO pub_neural.neural_schema_versions (
    component, current_version, minimum_compatible_version, updated_at
) VALUES (
    'observation_sync_runs', '0.5.1', '0.5.0', CURRENT_TIMESTAMP
) ON CONFLICT (component) DO UPDATE SET
    current_version = EXCLUDED.current_version,
    updated_at = CURRENT_TIMESTAMP;
