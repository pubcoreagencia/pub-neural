-- ============================================================================
-- PUB NEURAL V0 CANONICAL DATABASE MIGRATION
-- Migration File: 0003_align_repository_observation_projector_contract.sql
-- Classification: SCHEMA ALIGNMENT (REPOSITORY OBSERVATION CONTRACT)
-- Target: PostgreSQL 16+ / 17+
-- ============================================================================

\set ON_ERROR_STOP on

-- Align pub_neural.neural_repository_observations with canonical projector contract
ALTER TABLE pub_neural.neural_repository_observations 
    ADD COLUMN IF NOT EXISTS source VARCHAR(32) NOT NULL DEFAULT 'github',
    ADD COLUMN IF NOT EXISTS source_event_id VARCHAR(64),
    ADD COLUMN IF NOT EXISTS event_type VARCHAR(64),
    ADD COLUMN IF NOT EXISTS external_actor VARCHAR(128),
    ADD COLUMN IF NOT EXISTS internal_actor VARCHAR(128) NOT NULL DEFAULT 'actor:system',
    ADD COLUMN IF NOT EXISTS received_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ADD COLUMN IF NOT EXISTS details JSONB NOT NULL DEFAULT '{}'::jsonb;

-- Record schema version
INSERT INTO pub_neural.neural_schema_versions (
    component, current_version, minimum_compatible_version, updated_at
) VALUES (
    'neural_repository_observations', '0.2.1', '0.2.0', CURRENT_TIMESTAMP
) ON CONFLICT (component) DO UPDATE SET
    current_version = EXCLUDED.current_version,
    updated_at = CURRENT_TIMESTAMP;
