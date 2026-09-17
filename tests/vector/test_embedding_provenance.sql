-- P0 embedding provenance contract tests.
-- Run after migrations 0001 + 0002 against a disposable PostgreSQL/pgvector database.

\set ON_ERROR_STOP on

-- 1. Registry exists with required fields.
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='pub_neural'
      AND table_name='embedding_provenance'
      AND column_name='provider'
  ) THEN
    RAISE EXCEPTION 'P0: embedding_provenance.provider missing';
  END IF;
END $$;

-- 2. Unknown/incompatible legacy provenance cannot pass compatibility.
DO $$
DECLARE
  v_id UUID;
  v_ok BOOLEAN;
BEGIN
  SELECT id INTO v_id
  FROM pub_neural.embedding_provenance
  WHERE status='INCOMPATIBLE'
  LIMIT 1;

  IF v_id IS NOT NULL THEN
    SELECT pub_neural.embedding_provenance_compatible(
      v_id, 'legacy-unknown', 'legacy', NULL, 1536, 'legacy-v0', 'legacy-v0'
    ) INTO v_ok;
    IF v_ok THEN
      RAISE EXCEPTION 'P0: INCOMPATIBLE provenance was accepted';
    END IF;
  END IF;
END $$;

-- 3. ACTIVE provenance requires complete identity.
DO $$
DECLARE
  v_id UUID;
  v_ok BOOLEAN;
BEGIN
  INSERT INTO pub_neural.embedding_provenance (
    provider, model, model_version, dimension,
    corpus_version, index_version, normalization_config,
    status, identity_hash
  ) VALUES (
    'test-provider', 'test-model', 'v1', 1536,
    'test-corpus-v1', 'test-index-v1', '{"normalized":true}'::jsonb,
    'ACTIVE',
    encode(digest('p0-test-identity-v1','sha256'),'hex')
  )
  ON CONFLICT (identity_hash) DO UPDATE SET status='ACTIVE'
  RETURNING id INTO v_id;

  SELECT pub_neural.embedding_provenance_compatible(
    v_id, 'test-provider', 'test-model', 'v1', 1536,
    'test-corpus-v1', 'test-index-v1', '{"normalized":true}'::jsonb
  ) INTO v_ok;

  IF NOT v_ok THEN
    RAISE EXCEPTION 'P0: exact ACTIVE provenance was rejected';
  END IF;

  SELECT pub_neural.embedding_provenance_compatible(
    v_id, 'test-provider', 'test-model', 'v2', 1536,
    'test-corpus-v1', 'test-index-v1', '{"normalized":true}'::jsonb
  ) INTO v_ok;

  IF v_ok THEN
    RAISE EXCEPTION 'P0: model-version mismatch was accepted';
  END IF;

  SELECT pub_neural.embedding_provenance_compatible(
    v_id, 'test-provider', 'test-model', 'v1', 1536,
    'test-corpus-v2', 'test-index-v1', '{"normalized":true}'::jsonb
  ) INTO v_ok;

  IF v_ok THEN
    RAISE EXCEPTION 'P0: corpus-version mismatch was accepted';
  END IF;

  SELECT pub_neural.embedding_provenance_compatible(
    v_id, 'test-provider', 'test-model', 'v1', 1536,
    'test-corpus-v1', 'test-index-v2', '{"normalized":true}'::jsonb
  ) INTO v_ok;

  IF v_ok THEN
    RAISE EXCEPTION 'P0: index-version mismatch was accepted';
  END IF;

  SELECT pub_neural.embedding_provenance_compatible(
    v_id, 'test-provider', 'test-model', 'v1', 1537,
    'test-corpus-v1', 'test-index-v1', '{"normalized":true}'::jsonb
  ) INTO v_ok;

  IF v_ok THEN
    RAISE EXCEPTION 'P0: dimension mismatch was accepted';
  END IF;
END $$;

SELECT 'P0 embedding provenance contract tests passed' AS status;
