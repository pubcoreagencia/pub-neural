# PUB Neural — Retrieval Abstention V0.3

## Purpose

V0.2 proved that Dense and Hybrid retrieval can return semantically adjacent documents even for explicitly unsupported queries. V0.3 adds an explicit, auditable confidence gate so callers can reject low-confidence candidate sets instead of treating every nearest neighbor as evidence.

## Safety contract

1. The policy is **disabled by default** to preserve V0.1 compatibility.
2. Enabling the policy requires an explicit `min_dense_similarity` threshold.
3. Threshold selection MUST be performed on the calibration split, never by tuning against the locked holdout split.
4. The gate operates after lexical retrieval, dense retrieval, and RRF candidate generation, but before results are returned to the caller.
5. A lexical candidate may be accepted without satisfying the dense threshold when `accept_on_lexical_candidate=true`. This preserves legitimate exact-identifier and terminology queries, but means lexical bypass behavior must be evaluated separately during calibration.
6. When the gate rejects the candidate set, `HybridSearchEngine.search()` returns an empty result set rather than low-confidence candidates.

## Environment configuration

```text
PUB_NEURAL_ABSTENTION_ENABLED=0|1
PUB_NEURAL_MIN_DENSE_SIMILARITY=<0.0..1.0>
PUB_NEURAL_ABSTENTION_ACCEPT_LEXICAL=0|1
```

When no explicit `abstention_policy` is supplied to `HybridSearchEngine`, the engine now constructs the policy from these environment variables. Supplying an explicit policy remains authoritative and is useful for tests or controlled callers.

`PUB_NEURAL_ABSTENTION_ENABLED=1` without `PUB_NEURAL_MIN_DENSE_SIMILARITY` is intentionally invalid and fails closed at policy construction time.

## Decision reasons

The policy emits an auditable `AbstentionDecision` with one of these reasons:

- `POLICY_DISABLED`
- `LEXICAL_EVIDENCE_PRESENT`
- `NO_DENSE_CANDIDATE`
- `DENSE_SIMILARITY_BELOW_THRESHOLD`
- `DENSE_SIMILARITY_ABOVE_THRESHOLD`

The decision also records top dense similarity, top RRF score, and the number of lexical and dense candidates considered.

## Calibration data contract

The calibration harness expects one JSON list of query measurements. Each record must contain:

```json
{
  "query_id": "QRY-34",
  "evaluation_split": "CALIBRATION",
  "query_type": "Q13_UNSUPPORTED",
  "dense_top1_similarity": 0.8814
}
```

The harness rejects invalid similarity values and rejects any query ID that appears in both calibration and holdout. Holdout records are allowed to be present for audit visibility, but are categorically excluded from threshold selection.

Run:

```bash
python scripts/calibrate_abstention_v0_3.py measurements.json \
  --output abstention_calibration.json
```

Threshold candidates are generated from observed calibration similarities and their midpoints. Selection is deterministic and uses balanced accuracy, then supported-query acceptance, then unsupported-query rejection, then the highest threshold as tie-breakers.

## Calibration protocol

Before enabling the policy in production-like PDL workflows:

1. Run the existing V0.2 benchmark unchanged.
2. Capture dense top-1 similarity for every query, keeping `CALIBRATION` and `HOLDOUT` labels intact.
3. Feed the measurements to `scripts/calibrate_abstention_v0_3.py`.
4. Select and document the resulting threshold and its calibration trade-off.
5. Freeze the threshold and the calibration artifact.
6. Re-run the locked holdout set without modifying queries, qrels, or threshold.
7. Record acceptance rate, abstention rate, Recall@K, MRR, nDCG, and unsupported-query abstention rate.

The V0.2 observed unsupported dense similarities around the high-0.8 range are evidence that a gate is needed, but they MUST NOT be treated as a production threshold without calibration against supported examples.

## Non-goals

V0.3 does not claim that a fixed threshold is universally valid across embedding models, corpora, languages, or trust zones. Thresholds are model- and corpus-dependent configuration and must be versioned with their calibration evidence.
