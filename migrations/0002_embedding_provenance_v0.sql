-- ============================================================================
-- PUB NEURAL P0 — EMBEDDING PROVENANCE & COMPATIBILITY
-- Migration: 0002_embedding_provenance_v0.sql
-- Purpose: prevent silent mixing of incompatible embedding spaces.
-- ============================================================================

\set ON_ERROR_STOP on

CREATE TABLE IF NOT EXISTS pub_neural.embedding_provenance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider VARCHAR(64) NOT NULL,
    model VARCHAR(128) NOT NULL,
    model_version VARCHAR(64),
    dimension INTEGER NOT NULL,
    corpus_version VARCHAR(128) NOT NULL,
    index_version VARCHAR(128) NOT NULL,
    normalization_config JSONB NOT NULL DEFAULT '{}'::jsonb,
    status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
    identity_hash VARCHAR(64) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    retired_at TIMESTAMPTZ,
    CONSTRAINT chk_embedding_provenance_dimension CHECK (dimension > 0),
    CONSTRAINT chk_embedding_provenance_status
        CHECK (status IN ('ACTIVE', 'RETIRED', 'INCOMPATIBLE', 'UNKNOWN')),
    CONSTRAINT uq_embedding_provenance_identity
        UNIQUE (
            provider,
            model,
            model_version,
            dimension,
            corpus_version,
            index_version,
            normalization_config
        )
);

COMMENT ON TABLE pub_neural.embedding_provenance IS
'Canonical identity/provenance for every persisted embedding space and index version.';

COMMENT ON COLUMN pub_neural.embedding_provenance.identity_hash IS
'Deterministic SHA-256 identity over provider/model/version/dimension/corpus/index/config.';

-- Existing vectors predate this contract. They are deliberately marked
-- INCOMPATIBLE instead of pretending their semantic identity is known.
INSERT INTO pub_neural.embedding_provenance (
    provider,
    model,
    model_version,
    dimension,
    corpus_version,
    index_version,
    normalization_config,
    status,
    identity_hash
)
SELECT
    'legacy-unknown',
    model_id,
    NULL,
    1536,
    'legacy-v0',
    'legacy-v0',
    '{}'::jsonb,
    'INCOMPATIBLE',
    encode(
        digest(
            concat_ws('|',
                'legacy-unknown',
                model_id,
                '',
                '1536',
                'legacy-v0',
                'legacy-v0',
                '{}'
            ),
            'sha256'
        ),
        'hex'
    )
FROM pub_neural.neural_vectors
GROUP BY model_id
ON CONFLICT (identity_hash) DO NOTHING;

ALTER TABLE pub_neural.neural_vectors
    ADD COLUMN IF NOT EXISTS embedding_provenance_id UUID;

UPDATE pub_neural.neural_vectors v
SET embedding_provenance_id = p.id
FROM pub_neural.embedding_provenance p
WHERE p.provider = 'legacy-unknown'
  AND p.model = v.model_id
  AND p.dimension = 1536
  AND p.corpus_version = 'legacy-v0'
  AND p.index_version = 'legacy-v0'
  AND v.embedding_provenance_id IS NULL;

ALTER TABLE pub_neural.neural_vectors
    ALTER COLUMN embedding_provenance_id SET NOT NULL;

ALTER TABLE pub_neural.neural_vectors
    ADD CONSTRAINT fk_neural_vectors_embedding_provenance
    FOREIGN KEY (embedding_provenance_id)
    REFERENCES pub_neural.embedding_provenance(id)
    ON DELETE RESTRICT;

CREATE INDEX IF NOT EXISTS idx_embedding_provenance_active
    ON pub_neural.embedding_provenance (status, provider, model, dimension);

CREATE INDEX IF NOT EXISTS idx_neural_vectors_provenance
    ON pub_neural.neural_vectors (embedding_provenance_id);

-- Runtime roles need explicit access to the provenance registry because the table is
-- created after the baseline role grants in migration 0001.
GRANT SELECT ON pub_neural.embedding_provenance TO pub_neural_app, pub_neural_ceo, pub_neural_projector, pub_neural_admin;
GRANT INSERT, UPDATE ON pub_neural.embedding_provenance TO pub_neural_projector, pub_neural_admin;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA pub_neural TO pub_neural_projector, pub_neural_admin;

-- Version boundaries are explicit. A retrieval path must use an ACTIVE
-- provenance identity and must match the complete identity, not only dimension.
CREATE OR REPLACE FUNCTION pub_neural.embedding_provenance_compatible(
    p_provenance_id UUID,
    p_provider VARCHAR,
    p_model VARCHAR,
    p_model_version VARCHAR,
    p_dimension INTEGER,
    p_corpus_version VARCHAR,
    p_index_version VARCHAR,
    p_normalization_config JSONB
) RETURNS BOOLEAN
LANGUAGE SQL
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, pub_neural, public
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM pub_neural.embedding_provenance p
        WHERE p.id = p_provenance_id
          AND p.status = 'ACTIVE'
          AND p.provider = p_provider
          AND p.model = p_model
          AND p.model_version IS NOT DISTINCT FROM p_model_version
          AND p.dimension = p_dimension
          AND p.corpus_version = p_corpus_version
          AND p.index_version = p_index_version
          AND p.normalization_config = p_normalization_config
    );
$$;

REVOKE ALL ON FUNCTION pub_neural.embedding_provenance_compatible(
    UUID, VARCHAR, VARCHAR, VARCHAR, INTEGER, VARCHAR, VARCHAR, JSONB
) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION pub_neural.embedding_provenance_compatible(
    UUID, VARCHAR, VARCHAR, VARCHAR, INTEGER, VARCHAR, VARCHAR, JSONB
) TO pub_neural_app, pub_neural_projector, pub_neural_admin, pub_neural_ceo;

-- Schema registry records the compatibility boundary.
INSERT INTO pub_neural.neural_schema_versions (
    component,
    current_version,
    minimum_compatible_version
) VALUES (
    'embedding_provenance',
    'v0',
    'v0'
)
ON CONFLICT (component) DO UPDATE SET
    current_version = EXCLUDED.current_version,
    minimum_compatible_version = EXCLUDED.minimum_compatible_version,
    updated_at = CURRENT_TIMESTAMP;
