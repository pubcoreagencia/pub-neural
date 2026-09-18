# PUB Neural V1.1-C — Runtime Query Scope Hardening

**Status:** IMPLEMENTED / CI VERIFIED  
**Branch:** `feat/retrieval-abstention-v0.3`  
**Verified HEAD:** `10ea7d3ca88312b0aa704b48bf1a441f4d622ee0`

## Objective

Close the query-side project isolation gap discovered after V1.1-B.

The Runtime API already authenticated callers and executed canonical Hybrid Retrieval, but query requests were not explicitly validated against the canonical `holding_projects` catalog before retrieval.

## Implemented

1. `NeuralQueryService` accepts an optional server-side `project_validator`.
2. Production Runtime injects `PostgresExperienceSink.is_canonical_project` as that validator.
3. Unknown, inactive, or archived projects return `INVALID_REQUEST`.
4. Catalog/database failures return `UNAVAILABLE`.
5. Validation occurs before retrieval, preventing an invalid project scope from reaching the retrieval engine.
6. Existing in-process callers without a validator remain backward compatible.
7. HTTP Runtime coverage proves rejection of an unknown project.

## Security / provenance invariant

The project scope is established by the server-side canonical catalog. The request cannot establish its own authority by merely supplying a project identifier.

## Verification

GitHub Actions run #167 passed:

- Unit Tests
- Ingestion & Extraction
- Hybrid Retrieval & Vector
- Projector Engine
- Runtime PostgreSQL E2E Closed Loop

The previous Runtime closed-loop proof remains green after the hardening change.

## Next boundary

V1.1-C now establishes:

`authenticated request → canonical project scope → retrieval → governed response`

The next phase should audit and connect the real PDL pre-task query consumer to this Runtime channel. No automatic promotion or governance mutation is introduced by this phase.
