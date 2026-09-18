# Embedding Provenance V0 — Implementation Status

## Scope

P0 from GitHub issue #6: make embedding identity explicit and prevent silent mixing of vector spaces.

## Implemented in migration 0002

- Canonical `embedding_provenance` registry.
- Provider, model, model version, dimension, corpus version and index version.
- Normalization/configuration metadata.
- Explicit ACTIVE / RETIRED / INCOMPATIBLE / UNKNOWN lifecycle.
- Deterministic identity hash.
- Existing vectors are migrated as `legacy-unknown` + `INCOMPATIBLE`, never silently trusted.
- `neural_vectors.embedding_provenance_id` is mandatory.
- Compatibility function requires the complete identity and ACTIVE status.
- Schema version registry records the compatibility boundary.

## Fail-closed rule

A dense retrieval path is valid only when:

1. vector has a provenance record;
2. provenance status is ACTIVE;
3. provider matches;
4. model matches;
5. model version matches when declared;
6. dimension matches;
7. corpus version matches;
8. index version matches.

Dimension equality alone is insufficient.

## Remaining P0 application wiring

The Python embedding provider and vector worker must emit/register provenance before writing vectors, and hybrid retrieval must call the compatibility boundary before returning dense candidates.

Legacy vectors are intentionally unavailable to dense retrieval until re-indexed under an ACTIVE provenance identity.

## Required tests

- same dimension + different model => reject;
- same model + different model version => reject;
- same identity => accept;
- missing provenance => reject;
- RETIRED/INCOMPATIBLE provenance => reject;
- legacy vectors do not enter dense retrieval;
- re-indexed vectors enter retrieval only under matching provenance;
- provenance survives rebuild;
- corpus/index version changes require a new identity.
