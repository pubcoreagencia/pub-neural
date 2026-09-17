# Retrieval Embedding Provenance Contract — V0

## Status
Research-derived architectural requirement from the 2026-09-17 external agent ecosystem audit.

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

This is a design contract, not yet a database migration. Implementation must be proposed and tested separately.
