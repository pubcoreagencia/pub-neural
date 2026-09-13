# STEP 2E.2 — Evidence-Based Abstention Specification

**Status:** EXPERIMENTAL SPECIFICATION  
**Date:** 2026-09-13  
**Scope:** PUB Neural retrieval / semantic validation  
**Production impact:** NONE at this stage

## Objective

Define an experimental post-retrieval decision stage that distinguishes:

- retrieved similarity;
- evidence sufficiency;
- answerability;
- abstention;
- escalation.

STEP 2E.1 established that a scalar dense similarity threshold cannot safely perform this job on the current 36-query benchmark. ADR-002 therefore prohibits promoting such a threshold into V0.1 production.

## Decision Pipeline

```text
QUERY
  -> QUERY ANALYSIS
  -> HYBRID RETRIEVAL
  -> TOP-K CANDIDATES
  -> DOMAIN / SCOPE CHECK
  -> EVIDENCE SUFFICIENCY
  -> VERIFICATION
  -> DECISION
       |-> ANSWER
       |-> ABSTAIN
       `-> ESCALATE
```

## Decision Semantics

### ANSWER

Return an answer only when the candidate evidence is sufficiently relevant, in scope, non-contradictory and adequately supported.

### ABSTAIN

Refuse to synthesize an unsupported answer when available evidence is insufficient, out of scope, contradictory, or otherwise fails the verifier policy.

### ESCALATE

Request stronger verification or human/agent review when evidence is potentially relevant but the system cannot establish sufficient confidence safely.

## Experimental Signals

The experiment MUST keep the following signals separate before calibration:

1. `dense_similarity`: vector proximity;
2. `rrf_rank_signal`: relative retrieval rank;
3. `lexical_evidence`: optional lexical support;
4. `scope_compatibility`: project/tenant/domain compatibility;
5. `evidence_coverage`: how much of the requested information is supported;
6. `entailment_or_verifier_score`: whether candidate evidence actually supports the query/claim;
7. `contradiction_signal`: whether retrieved evidence conflicts;
8. `provenance_quality`: source authority, freshness and validation state.

No individual signal should be interpreted as calibrated answerability probability without validation.

## Minimum Evidence Record

Every experimental decision should be serializable with at least:

```yaml
query_id: <id>
decision: ANSWER | ABSTAIN | ESCALATE
candidates:
  - document_id: <id>
    rank: <integer>
    dense_similarity: <float>
    lexical_rank: <integer|null>
    rrf_score: <float>
evidence:
  coverage: <float>
  scope_compatible: <bool>
  verifier_score: <float|null>
  contradiction: <bool>
provenance:
  source: <source identifier>
  authority: <runtime|test|code|decision|documentation|other>
  freshness: <value|null>
reason_codes: []
policy_version: <version>
```

## Required Reason Codes

At minimum, the experiment should distinguish:

- `SUFFICIENT_EVIDENCE`
- `INSUFFICIENT_EVIDENCE`
- `OUT_OF_SCOPE`
- `CONTRADICTORY_EVIDENCE`
- `LOW_VERIFIER_SUPPORT`
- `LOW_PROVENANCE_QUALITY`
- `INSUFFICIENT_COVERAGE`
- `ESCALATION_REQUIRED`

## Benchmark Protocol

STEP 2E.2 MUST initially run in shadow/experimental mode. It must not alter production retrieval behavior.

Evaluation requirements:

1. Reuse the 36-query baseline from STEP 2E.1.
2. Preserve all existing query labels.
3. Add explicit decision labels where possible: answerable, unsupported, ambiguous, contradictory.
4. Record every signal independently.
5. Produce a confusion matrix for ANSWER / ABSTAIN / ESCALATE.
6. Evaluate held-out examples before promoting any policy.
7. Measure supported-query recall separately from unsupported-query rejection.
8. Record false abstentions and unsafe accepts independently.
9. Preserve SHA-256 hashes of benchmark inputs and generated artifacts.
10. Do not hardcode thresholds into production from this sample.

## Promotion Gate

No evidence-aware policy becomes production behavior until it demonstrates, on a sufficiently expanded and held-out benchmark, that it improves safety without unacceptable recall degradation.

Promotion requires:

```text
IMPLEMENT
  -> EXPERIMENT
  -> REPEATABLE TEST
  -> HELD-OUT VALIDATION
  -> EVIDENCE
  -> ARCHITECTURE DECISION
  -> REVIEW
  -> PRODUCTION PROMOTION
```

## Architectural Principle

Retrieval answers the question:

> "What information appears relevant?"

Verification answers the different question:

> "Is there enough trustworthy evidence to answer?"

The PUB Neural must not collapse these two questions into one score.

## Relationship to ADR-002

This specification operationalizes the required next architecture defined by `ADR-002-DENSE-ABSTENTION-NOT-SCALAR.md`.

It is an experimental contract, not proof that the proposed verifier is already implemented or production-ready.
