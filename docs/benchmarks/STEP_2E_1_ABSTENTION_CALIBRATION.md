# STEP 2E.1 — Dense Similarity Abstention Calibration

**Status:** COMPLETED / EXPERIMENTAL
**Date:** 2026-09-13
**Production code changed:** NO
**Baseline commit:** `2f19cadf5dc36c65876ffaed334317a7d31ff647`

## Objective

Determine whether a single threshold on `dense_top1_similarity` can reliably distinguish supported/in-domain queries from unsupported/out-of-domain queries for PUB Neural retrieval.

## Dataset

- Total queries: 36
- Supported: 33
- Unsupported: 3 (`QRY-34`, `QRY-35`, `QRY-36`)
- Calibration input SHA-256: `0742cf6a20e66f4c2fb01f67c5bc4234bba2a2ccc2c73f6a174af66b20c2fdf5`
- Generated artifact SHA-256: `4279695acbaa92c6d8e13ff5cb9c0a9d7ac2ae28fb6eaccb195cb5f9c11682ee`

## Key Findings

### 1. Dense-only threshold is insufficient

Supported similarity range: `0.055386` → `0.899932`.

Unsupported similarity range: `0.128329` → `0.677905`.

There is severe empirical distribution overlap. 20/33 supported queries (60.6%) have Top-1 similarity less than or equal to the maximum unsupported similarity (`QRY-35 = 0.677905`).

A threshold of `0.68` rejects all 3 unsupported queries, but also rejects 21/33 supported queries, leaving only 36.4% supported acceptance.

### 2. Unsupported cases

| Query | Type | Top-1 similarity | First grid threshold rejecting |
|---|---|---:|---:|
| QRY-34 | CNN/PyTorch OOD | 0.501285 | 0.51 |
| QRY-35 | Kubernetes/Istio OOD | 0.677905 | 0.68 |
| QRY-36 | Solidity/ERC-721 OOD | 0.128329 | 0.13 |

### 3. RRF is not confidence

Top-1 RRF is `0.016393 = 1/(60+1)` for many supported and unsupported queries. RRF measures rank contribution, not semantic confidence. It must not be used as an isolated confidence/abstention score.

### 4. Lexical presence is not a sufficient gate

All 3 unsupported queries had zero lexical matches, but 30/33 supported queries also had zero lexical matches in this corpus. Requiring lexical evidence would reject 90.9% of supported queries.

### 5. Top-1/Top-2 margin is not sufficient

`QRY-34` has a dense margin of `0.1416`, larger than the margin of 18 supported queries. Margin alone does not reliably identify OOD queries.

## Threshold Trade-off

| Threshold | Supported acceptance | Unsupported rejection |
|---:|---:|---:|
| 0.00–0.05 | 100.0% | 0.0% |
| 0.13 | 75.8% | 33.3% |
| 0.51 | 66.7% | 66.7% |
| **0.68** | **36.4%** | **100.0%** |
| 0.75 | 24.2% | 100.0% |

## Architectural Decision

**Do not hardcode a naive scalar dense-similarity abstention threshold in PUB Neural V0.1.**

Dense retrieval remains a candidate-generation/ranking signal. Abstention must be based on evidence sufficiency and/or calibrated multi-signal verification.

## Next Step

Proceed to **STEP 2E.2 — Evidence-Based Abstention**. Evaluate a post-retrieval verification layer using candidate evidence coverage, semantic/domain compatibility, metadata/project scope, contradiction detection, and an experimentally calibrated verifier. Keep retrieval scores and answer confidence as separate concepts.

## Research Alignment

Recent work supports treating abstention as an evidence-sufficiency/OOD problem rather than assuming a single retrieval score is a calibrated probability. In particular, recent RAG abstention research evaluates insufficient and conflicting evidence explicitly, while OOD work explores KB-aligned gates and calibrated detection.

This experiment is the PUB Neural empirical baseline and takes precedence over generic assumptions when making implementation decisions for this corpus.
