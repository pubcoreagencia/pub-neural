-- ============================================================================
-- PUB NEURAL V0 CANONICAL DATABASE MIGRATION
-- Migration File: 0009_observation_sync_runs_v0_5.sql
-- Classification: CONTINUOUS REPOSITORY OBSERVATION TELEMETRY (V0.5)
-- Target: PostgreSQL 16+ / 17+
-- ============================================================================

\set ON_ERROR_STOP on

CREATE TABLE IF NOT EXISTS pub_neural.observation_sync_runs (
    id UUID PRIMARY KEY,
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,
    status VARCHAR(32) NOT NULL DEFAULT 'RUNNING',
    repositories_scanned INTEGER NOT NULL DEFAULT 0,
    repositories_changed INTEGER NOT NULL DEFAULT 0,
    observations_created INTEGER NOT NULL DEFAULT 0,
    observations_deduplicated INTEGER NOT NULL DEFAULT 0,
    observations_failed INTEGER NOT NULL DEFAULT 0,
    error_detail TEXT,
    cursor_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_obs_sync_runs_started ON pub_neural.observation_sync_runs (started_at DESC);
CREATE INDEX IF NOT EXISTS idx_obs_sync_runs_status ON pub_neural.observation_sync_runs (status);

-- Grant privileges
GRANT SELECT ON pub_neural.observation_sync_runs TO pub_neural_app, pub_neural_ceo;
GRANT ALL ON pub_neural.observation_sync_runs TO pub_neural_admin;

-- Record schema version
INSERT INTO pub_neural.neural_schema_versions (
    component, current_version, minimum_compatible_version, updated_at
) VALUES (
    'observation_sync_runs', '0.5.0', '0.5.0', CURRENT_TIMESTAMP
) ON CONFLICT (component) DO UPDATE SET
    current_version = EXCLUDED.current_version,
    updated_at = CURRENT_TIMESTAMP;
