-- ============================================================================
-- PUB NEURAL V0 CANONICAL DATABASE MIGRATION
-- Migration File: 0008_project_ontology_governance_v0_3.sql
-- Classification: PROJECT ONTOLOGY EPISTEMOLOGICAL GOVERNANCE (V0.3)
-- Target: PostgreSQL 16+ / 17+
-- Rule: Distinguish entity existence vs repository association
-- ============================================================================

\set ON_ERROR_STOP on

-- 1. Add epistemological metadata columns to holding_projects
ALTER TABLE pub_neural.holding_projects
    ADD COLUMN IF NOT EXISTS ontology_status VARCHAR(32) NOT NULL DEFAULT 'PROPOSED',
    ADD COLUMN IF NOT EXISTS ontology_source VARCHAR(64) NOT NULL DEFAULT 'RULE',
    ADD COLUMN IF NOT EXISTS ontology_confidence NUMERIC(4,3) NOT NULL DEFAULT 0.500,
    ADD COLUMN IF NOT EXISTS ontology_reason TEXT,
    ADD COLUMN IF NOT EXISTS ontology_verified_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS ontology_verified_by VARCHAR(128) DEFAULT 'system:ontology-classifier';

CREATE INDEX IF NOT EXISTS idx_holding_projects_ontology_status ON pub_neural.holding_projects(ontology_status);
CREATE INDEX IF NOT EXISTS idx_holding_projects_ontology_source ON pub_neural.holding_projects(ontology_source);

-- 2. Update schema versions table
INSERT INTO pub_neural.neural_schema_versions (
    component,
    current_version,
    minimum_compatible_version,
    updated_at
) VALUES (
    'project_ontology',
    '0.3.0',
    '0.3.0',
    CURRENT_TIMESTAMP
)
ON CONFLICT (component) DO UPDATE SET
    current_version = EXCLUDED.current_version,
    minimum_compatible_version = EXCLUDED.minimum_compatible_version,
    updated_at = EXCLUDED.updated_at;
