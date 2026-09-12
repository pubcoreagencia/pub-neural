# PUB Neural — Retrieval Abstention V0.3

## Purpose

V0.2 proved that Dense and Hybrid retrieval can return semantically adjacent documents even for explicitly unsupported queries. V0.3 adds an explicit, auditable confidence gate so callers can reject low-confidence candidate sets instead of treating every nearest neighbor as evidence.

## Safety contract

1. The policy is **disabled by default** to preserve V0.1 compatibility.
2. Enabling the policy requires an explicit `min_dense_similarity` threshold.
3. Threshold selection MUST be performed on the calibration split, never by tuning against the locked holdout split.
4. The gate operates after lexical retrieval, dense retrieval, and RRF candidate generation, but before results are returned to the caller.
5. A lexical candidate may be accepted without satisfying the dense threshold when `accept_on_lexical_candidate=true`. This preserves legitimate exact-identifier and terminology queries.
6. When the gate rejects the candidate set, `HybridSearchEngine.search()` returns an empty result set rather than low-confidence candidates.

## Environment configuration

```text
PUB_NEURAL_ABSTENTION_ENABLED=0|1
PUB_NEURAL_MIN_DENSE_SIMILARITY=<0.0..1.0>
PUB_NEURAL_ABSTENTION_ACCEPT_LEXICAL=0|1
```

`PUB_NEURAL_ABSTENTION_ENABLED=1` without `PUB_NEURAL_MIN_DENSE_SIMILARITY` is intentionally invalid and fails closed at policy construction time.

## Decision reasons

The policy emits an auditable `AbstentionDecision` with one of these reasons:

- `POLICY_DISABLED`
- `LEXICAL_EVIDENCE_PRESENT`
- `NO_DENSE_CANDIDATE`
- `DENSE_SIMILARITY_BELOW_THRESHOLD`
- `DENSE_SIMILARITY_ABOVE_THRESHOLD`

The decision also records top dense similarity, top RRF score, and the number of lexical and dense candidates considered.

## Calibration protocol

Before enabling the policy in production-like PDL workflows:

1. Run the existing V0.2 benchmark unchanged.
2. Analyze dense top-1 similarity distributions separately for supported and unsupported calibration queries.
3. Select a threshold that maximizes supported-query acceptance while rejecting unsupported behavior, documenting the trade-off.
4. Freeze the threshold.
5. Re-run the locked holdout set without modifying queries, qrels, or threshold.
6. Record acceptance rate, abstention rate, Recall@K, MRR, nDCG, and unsupported-query abstention rate.

The V0.2 observed unsupported dense similarities around the high-0.8 range are evidence that a gate is needed, but they MUST NOT be treated as a production threshold without calibration against supported examples.

## Non-goals

V0.3 does not claim that a fixed threshold is universally valid across embedding models, corpora, languages, or trust zones. Thresholds are model- and corpus-dependent configuration and must be versioned with their calibration evidence.
