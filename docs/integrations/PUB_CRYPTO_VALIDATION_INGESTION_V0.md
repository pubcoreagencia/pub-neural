# PUB Crypto Validation Ingestion Contract V0

## Status

Integration contract defined against the current verified PUB Neural governance model.

This document intentionally does **not** invent an HTTP endpoint, table name, RPC, or database migration that has not been verified in the current repository/runtime.

## Source

- Repository: `pubcoreagencia/pub-crypto`
- Artifact type: `TRADING_VALIDATION`
- Producer: `PUB_CRYPTO`

## Required provenance

Every accepted validation artifact must preserve:

- source repository;
- source commit;
- strategy version;
- dataset version;
- observation timestamp;
- validation status;
- trade count;
- regime attribution;
- Monte Carlo summary when present.

The source commit is mandatory for future reproducibility. The artifact must remain project-scoped until promotion is explicitly validated.

## Semantic mapping

```
PUB_CRYPTO
  |
  | TRADING_VALIDATION
  v
PUB_NEURAL
  |
  +-- SOURCE / provenance
  +-- EVIDENCE
  +-- EVENT / episodic record
  +-- DECISION / when applicable
  +-- LESSON candidate / only after validation
  +-- PATTERN candidate / only after validation
```

A validation artifact is evidence. It is not automatically an institutional lesson, rule, skill, or decision.

## Promotion boundary

`CAPTURED → OBSERVED → EXTRACTED → CANDIDATE → VALIDATED → ADOPTED → INSTITUTIONAL`

PUB Crypto may create the evidence artifact.

PUB Neural owns knowledge promotion.

## Fail-closed rules

Reject or abstain when:

1. source repository is missing;
2. source commit is missing;
3. strategy version is missing;
4. dataset version is missing;
5. observation timestamp is invalid;
6. validation status is unknown;
7. provenance cannot be preserved.

Do not silently coerce missing provenance.

## Current implementation boundary

The repository currently exposes the governance and knowledge model needed for this contract, but the exact runtime ingestion API/database write path is not sufficiently verified through the connected GitHub surface.

Therefore this commit is a **contract**, not a claim of live database ingestion.

The next implementation must first verify the concrete ingestion/projector path from the current PUB Neural runtime and then add the smallest adapter and tests against that real path.

## Security

No exchange credentials, private keys, API secrets, or real-capital authorization belong in this artifact.

## Principle

**Evidence crosses the project boundary first. Institutional knowledge crosses only after governance.**
