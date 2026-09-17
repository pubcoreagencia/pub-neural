-- ============================================================================
-- PUB NEURAL V0 CANONICAL DATABASE MIGRATION
-- Migration File: 0006_project_registry_v0.sql
-- Classification: CANONICAL PROJECT & REPOSITORY REGISTRY (V0.1)
-- Target: PostgreSQL 16+ / 17+
-- ============================================================================

\set ON_ERROR_STOP on

CREATE TABLE IF NOT EXISTS pub_neural.project_registry (
    id VARCHAR(128) PRIMARY KEY,
    repository_full_name VARCHAR(255) NOT NULL UNIQUE,
    repository_name VARCHAR(128) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(64) NOT NULL DEFAULT 'OPERACIONAL',
    lifecycle_status VARCHAR(64) NOT NULL DEFAULT 'ATIVO',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_archived BOOLEAN NOT NULL DEFAULT FALSE,
    is_private BOOLEAN NOT NULL DEFAULT FALSE,
    monitoring_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    strategic_priority VARCHAR(32) NOT NULL DEFAULT 'PADRAO',
    github_url VARCHAR(512),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_discovered_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_project_registry_lifecycle ON pub_neural.project_registry(lifecycle_status);
CREATE INDEX IF NOT EXISTS idx_project_registry_category ON pub_neural.project_registry(category);
CREATE INDEX IF NOT EXISTS idx_project_registry_active ON pub_neural.project_registry(is_active);

-- Enable RLS
ALTER TABLE pub_neural.project_registry ENABLE ROW LEVEL SECURITY;

-- Allow read access for authenticated actors and trusted roles
DROP POLICY IF EXISTS project_registry_read_policy ON pub_neural.project_registry;
CREATE POLICY project_registry_read_policy ON pub_neural.project_registry
    FOR SELECT
    USING (true);

-- Update schema versions table
INSERT INTO pub_neural.neural_schema_versions (
    component,
    current_version,
    minimum_compatible_version,
    updated_at
) VALUES (
    'project_registry',
    '0.1.0',
    '0.1.0',
    CURRENT_TIMESTAMP
)
ON CONFLICT (component) DO UPDATE SET
    current_version = EXCLUDED.current_version,
    minimum_compatible_version = EXCLUDED.minimum_compatible_version,
    updated_at = EXCLUDED.updated_at;
