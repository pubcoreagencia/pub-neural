# Retrieval Embedding Provenance Contract — V0

## Status
**IMPLEMENTED + VALIDATED — P0 COMPLETE (2026-09-18)**

Research-derived architectural requirement from the 2026-09-17 external agent ecosystem audit. Implementation landed through PR #7 and is now on `main` at `7e9ab1ec077500670b6242aa7dd45ccaa09d2235`.

## Problem

Vector dimension alone does not establish semantic compatibility. Changing embedding models can produce vectors with the same dimension but a different semantic space.

Silent mixing can degrade retrieval while appearing technically healthy.

## Contract

Every persisted embedding/index must retain provenance sufficient to determine compatibility:

- provider
- model
- model version, when available
- dimension
- corpus/version identifier
- index/version identifier
- created_at
- optional normalization/configuration metadata

## Compatibility rule

A retrieval path must not combine vectors from incompatible embedding identities merely because dimensions match.

If provenance is absent or incompatible, the system should fail closed or explicitly abstain rather than silently blend spaces.

## Migration rule

Embedding model changes require an explicit migration/version boundary:

1. register the new embedding identity
2. create a new corpus/index version
3. backfill or re-embed deterministically
4. validate retrieval quality
5. switch the active index
6. retain historical provenance for auditability

## PUB Neural alignment

This contract supports PUB Neural's principles of provenance, abstention, reproducibility and institutional memory integrity.

## Implementation evidence

Implemented in `migrations/0002_embedding_provenance_v0.sql` and runtime retrieval/indexing modules.

The implementation persists provider/model/model-version/dimension/corpus/index/normalization provenance, binds vectors to an immutable provenance identity, and blocks dense retrieval when no ACTIVE exact-compatible provenance exists.

Validation evidence:
- GitHub Actions isolated PostgreSQL 16 + pgvector suite: PASS.
- VECTOR-01..17: PASS in two clean passes.
- SEMANTIC-01..06: PASS.
- Normalization configuration participates in compatibility identity.
- PR #7 merged to `main`.

Migration/version changes must continue to preserve the explicit boundary defined above. New embedding spaces require a new provenance identity and explicit re-index/migration validation.
