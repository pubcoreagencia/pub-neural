# ADR-002 — Dense Similarity Is Not a Scalar Abstention Gate

**Status:** ACCEPTED
**Date:** 2026-09-13
**Scope:** PUB Neural retrieval / semantic validation

## Context

Production-data semantic validation evaluated 36 real query observations: 33 supported and 3 intentionally unsupported. Dense Top-1 similarity showed substantial overlap between the supported and unsupported distributions.

The strongest unsupported query reached `0.677905`, while 20/33 supported queries (60.6%) were at or below that value. A threshold of `0.68` therefore rejected 100% of unsupported queries but reduced supported acceptance to 36.4%.

Additional signals were also tested:

- RRF Top-1 score was frequently identical across supported and unsupported cases because RRF is rank-based.
- Lexical presence was absent for all unsupported queries but also absent for 30/33 supported queries.
- Top-1/Top-2 dense margin did not separate OOD from supported queries.

## Decision

PUB Neural V0.1 MUST NOT use a single scalar `dense_top1_similarity >= T` rule as its production abstention/OOD policy.

Dense similarity is a retrieval signal, not a calibrated probability of answerability.

RRF is a ranking signal, not confidence.

Lexical presence is supporting evidence, not a mandatory answerability gate.

Top-1/Top-2 margin is diagnostic evidence, not a standalone OOD detector.

## Consequences

### Positive

- Prevents catastrophic recall loss caused by arbitrary dense thresholds.
- Keeps retrieval and confidence semantically separate.
- Preserves the current hybrid retrieval baseline without contaminating production behavior with an uncalibrated gate.
- Creates a clear experimental boundary for future abstention work.

### Negative

- V0.1 does not yet have a fully calibrated automatic OOD/abstention mechanism.
- A future verifier/gate requires additional evaluation data and calibration.

## Required Next Architecture

Implement and benchmark an evidence-aware post-retrieval decision stage:

```text
QUERY
  -> RETRIEVAL
  -> CANDIDATE EVIDENCE
  -> DOMAIN / SCOPE CHECK
  -> EVIDENCE SUFFICIENCY / VERIFICATION
  -> ANSWER | ABSTAIN | ESCALATE
```

The verifier should preserve provenance and expose the evidence used for the decision.

Candidate signals for STEP 2E.2:

1. evidence coverage;
2. project/tenant/domain compatibility;
3. semantic entailment or verifier score;
4. contradiction detection;
5. dense similarity as one feature among several;
6. lexical evidence as an optional supporting feature;
7. calibrated composite decision policy.

Do not introduce a production threshold merely because it performs well on this small calibration sample. Expand the benchmark and validate on held-out data first.

## Evidence

See `docs/benchmarks/STEP_2E_1_ABSTENTION_CALIBRATION.md` for the complete empirical calibration summary and SHA-256 identifiers of the source/generated artifacts.
