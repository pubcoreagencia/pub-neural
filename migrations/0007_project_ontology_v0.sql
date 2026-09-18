-- ============================================================================
-- PUB NEURAL V0 CANONICAL DATABASE MIGRATION
-- Migration File: 0007_project_ontology_v0.sql
-- Classification: CANONICAL PROJECT ONTOLOGY & REPOSITORY ASSOCIATION (V0.2)
-- Target: PostgreSQL 16+ / 17+
-- Rule: REPOSITÓRIO != PROJETO (1 Project -> N Repositories)
-- ============================================================================

\set ON_ERROR_STOP on

-- 1. Holding Projects Table
CREATE TABLE IF NOT EXISTS pub_neural.holding_projects (
    id VARCHAR(128) PRIMARY KEY,
    slug VARCHAR(128) NOT NULL UNIQUE,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    project_type VARCHAR(64) NOT NULL DEFAULT 'PRODUCT',
    lifecycle_status VARCHAR(64) NOT NULL DEFAULT 'ATIVO',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_archived BOOLEAN NOT NULL DEFAULT FALSE,
    strategic_priority VARCHAR(32) NOT NULL DEFAULT 'PADRAO',
    owner_scope VARCHAR(128) NOT NULL DEFAULT 'pubcoreagencia',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_holding_projects_slug ON pub_neural.holding_projects(slug);
CREATE INDEX IF NOT EXISTS idx_holding_projects_type ON pub_neural.holding_projects(project_type);
CREATE INDEX IF NOT EXISTS idx_holding_projects_status ON pub_neural.holding_projects(lifecycle_status);
CREATE INDEX IF NOT EXISTS idx_holding_projects_active ON pub_neural.holding_projects(is_active);

-- Enable RLS for holding_projects
ALTER TABLE pub_neural.holding_projects ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS holding_projects_read_policy ON pub_neural.holding_projects;
CREATE POLICY holding_projects_read_policy ON pub_neural.holding_projects
    FOR SELECT
    USING (true);

-- 2. Project Repositories Association Table
CREATE TABLE IF NOT EXISTS pub_neural.project_repositories (
    project_id VARCHAR(128) NOT NULL REFERENCES pub_neural.holding_projects(id) ON DELETE CASCADE,
    repository_id VARCHAR(128) NOT NULL REFERENCES pub_neural.project_registry(id) ON DELETE CASCADE,
    relationship_type VARCHAR(64) NOT NULL DEFAULT 'PRIMARY',
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    association_status VARCHAR(32) NOT NULL DEFAULT 'PROPOSED',
    classification_source VARCHAR(64) NOT NULL DEFAULT 'RULE',
    classification_confidence NUMERIC(4,3) NOT NULL DEFAULT 0.500,
    classification_reason TEXT,
    classified_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    classified_by VARCHAR(128) NOT NULL DEFAULT 'system:ontology-classifier',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (project_id, repository_id)
);

CREATE INDEX IF NOT EXISTS idx_proj_repos_repo_id ON pub_neural.project_repositories(repository_id);
CREATE INDEX IF NOT EXISTS idx_proj_repos_proj_id ON pub_neural.project_repositories(project_id);
CREATE INDEX IF NOT EXISTS idx_proj_repos_status ON pub_neural.project_repositories(association_status);
CREATE INDEX IF NOT EXISTS idx_proj_repos_rel_type ON pub_neural.project_repositories(relationship_type);

-- Enable RLS for project_repositories
ALTER TABLE pub_neural.project_repositories ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS project_repositories_read_policy ON pub_neural.project_repositories;
CREATE POLICY project_repositories_read_policy ON pub_neural.project_repositories
    FOR SELECT
    USING (true);

-- Runtime catalog readers
GRANT SELECT ON pub_neural.holding_projects TO pub_neural_app, pub_neural_ceo;
GRANT SELECT ON pub_neural.project_repositories TO pub_neural_app, pub_neural_ceo;

-- 3. Update schema versions table
INSERT INTO pub_neural.neural_schema_versions (
    component,
    current_version,
    minimum_compatible_version,
    updated_at
) VALUES (
    'project_ontology',
    '0.2.0',
    '0.2.0',
    CURRENT_TIMESTAMP
)
ON CONFLICT (component) DO UPDATE SET
    current_version = EXCLUDED.current_version,
    minimum_compatible_version = EXCLUDED.minimum_compatible_version,
    updated_at = EXCLUDED.updated_at;
