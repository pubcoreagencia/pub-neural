# STEP 2E.2 — Evidence Abstention Experimental Implementation

**Status:** IMPLEMENTED / NOT YET CALIBRATED  
**Date:** 2026-09-13  
**Production impact:** NONE

## What was implemented

A pure, policy-driven evaluator was added at:

`src/retrieval/evidence_abstention.py`

with focused tests at:

`tests/vector/test_evidence_abstention.py`

The evaluator accepts independently measured evidence signals:

- evidence coverage;
- verifier score;
- scope compatibility;
- contradiction state;
- provenance quality.

It produces one of:

- `ANSWER`
- `ABSTAIN`
- `ESCALATE`

with explicit reason codes and a policy version.

## Deliberate architectural boundary

The evaluator does **not** accept dense similarity or RRF as answerability inputs. Those remain retrieval/ranking signals as established by ADR-002.

The policy contains explicit thresholds only as constructor inputs. There are no production defaults and no automatic calibration from the 36-query sample.

This makes the component suitable for shadow experimentation while preventing an accidental V0.1 production gate.

## Conservative precedence

```text
CONTRADICTION -> ESCALATE
OUT_OF_SCOPE -> ABSTAIN
LOW_PROVENANCE -> ABSTAIN
LOW_COVERAGE -> ABSTAIN
MISSING_VERIFIER -> ESCALATE
LOW_VERIFIER -> ABSTAIN
ALL_REQUIRED_GATES -> ANSWER
```

## What has NOT been claimed

This implementation does **not** prove that the policy is calibrated, safe, or production-ready.

The thresholds used by the unit tests are synthetic test values only. They are not a recommendation for production.

The 36-query STEP 2E.1 benchmark has not yet been replayed through a real evidence verifier in this step because the complete per-query evidence records are not present in the canonical repository artifact set available to this commit.

No fabricated benchmark result is recorded.

## Next execution gate

The next experimental run must:

1. restore the complete 36-query input and candidate evidence records;
2. run hybrid retrieval against the same benchmark;
3. attach scope/provenance metadata;
4. invoke an actual semantic verifier or equivalent validated verifier;
5. generate per-query evidence records;
6. evaluate `ANSWER / ABSTAIN / ESCALATE`;
7. calculate supported-query recall, unsupported-query rejection, false abstention, unsafe accept, and escalation rate;
8. repeat on held-out queries;
9. hash and persist all generated artifacts;
10. only then create an architecture decision for or against promotion.

## Validation state

Repository-level code and tests have been committed. Runtime execution of the new tests was **not performed by the GitHub connector in this turn**. A local/CI execution is required before this component is treated as validated.
