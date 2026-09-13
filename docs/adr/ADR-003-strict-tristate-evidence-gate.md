# ADR-003: Strict Tri-State Evidence-Gated Retrieval

* **Status**: EXPERIMENTAL (Bounded to current 36-query calibration benchmark; requires adversarial expansion before Production Ready)
* **Date**: 2026-09-13
* **Context**: PUB Neural V0.2 Semantic Validation (Steps 2E.4 & 2E.5)
* **Deciders**: PUB Core / PDL Technical Architecture Team
* **Supersedes**: Implicit single-threshold scalar abstention (ADR-002)

---

## 1. Context & Problem Statement

Experimental findings from Steps 2E.1 through 2E.5 established the following empirical facts regarding hybrid neural retrieval:

1. **Retrieval != Evidence**: High dense similarity (cosine similarity up to `0.677905` in `QRY-35`) and high Reciprocal Rank Fusion (RRF) scores occur frequently on completely unsupported and out-of-domain queries due to generic distributed systems and technical vocabulary overlap. Scalar similarity thresholds fail to separate supported from unsupported queries without destroying supported recall.
2. **Retrieval Depth vs Decision Depth Separation**:
   - `RETRIEVAL_RECALL@1` is only `24.24%` (8/33 supported queries).
   - `RETRIEVAL_RECALL@10` reaches `93.94%` (31/33 supported queries).
   - `VERIFIER_EVIDENCE_RECALL@10` reaches `84.85%` (28/33 supported queries).
3. **The False Positive Hazard of Lenient Aggregation**:
   - In Step 2E.4, evaluating multiple candidates under a **Lenient Policy** (where `PARTIAL_SUPPORT` is accepted as an answerable signal) elevated recall but introduced **2 False Acceptances** at $K \ge 5$ (`QRY-34` and `QRY-35`), dropping unsupported containment to `33.33%`.
   - The root cause was incidental token matches (e.g., "rede neural" in hybrid validation reports for `QRY-34`, or "cluster/service" in schema docs for `QRY-35`) entering the candidate pool at ranks 4 and 5.
4. **The Strict Aggregation Invariant**:
   - Under **Aggregator B (Strict)**, where **only `DIRECT_SUPPORT` can produce `ANSWER`** and `PARTIAL_SUPPORT` is strictly routed to `ESCALATE`:
     - **Answer Precision**: `100.0%` across all $K \in \{1, 3, 5, 10\}$.
     - **Unsupported Containment**: `100.0%` (3/3 contained: `QRY-34` Escalate, `QRY-35` Escalate, `QRY-36` Abstain).
     - **False Acceptances**: `0` across all $K \in \{1, 3, 5, 10\}$.
   - Therefore, $K=3$ was merely a safety boundary for lenient aggregators. Under Strict Tri-State aggregation, **retrieving and inspecting $K=10$ candidates is completely safe**.

---

## 2. Decision: Strict Tri-State Architecture Contract

We establish the foundational architectural contract:

$$\text{RETRIEVAL DEPTH} \neq \text{DECISION DEPTH}$$

The retrieval engine and semantic verifier operate with a wide aperture ($K=10$) to maximize recall, while the decision policy operates under a strict evidence gate before answering.

```
       [ USER QUERY ]
              │
              ▼
   ┌──────────────────────┐
   │    RETRIEVAL (K)     │  DEFAULT_RETRIEVAL_K = 10 (High Recall: 93.94%)
   └──────────┬───────────┘
              │ Candidates (1..10)
              ▼
   ┌──────────────────────┐
   │  EVIDENCE VERIFIER   │  Evaluates scope, provenance, facts per candidate
   └──────────┬───────────┘
              │ Candidate Judgments [DIRECT, PARTIAL, INSUFFICIENT, OUT_OF_SCOPE]
              ▼
   ┌──────────────────────┐
   │ EVIDENCE AGGREGATOR  │  AGGREGATOR B (STRICT)
   └──────────┬───────────┘
              │ Bounded Synthesis
              ▼
   ┌──────────────────────┐
   │   TRI-STATE POLICY   │
   └──────────┬───────────┘
              │
      ┌───────┼───────┐
      ▼       ▼       ▼
   ANSWER  ESCALATE ABSTAIN
```

### 2.1 State Transition Contract

The Aggregator and Policy must enforce the following deterministic transitions:

| Best Candidate Judgment | Confidence Requirement | Tri-State Action | Architectural Meaning |
| :--- | :--- | :--- | :--- |
| **`DIRECT_SUPPORT`** | $\ge 0.80$ with verified provenance | **`ANSWER`** | Direct factual backing verified in candidate text. |
| **`PARTIAL_SUPPORT`** | Any | **`ESCALATE`** | Fragmentary evidence detected; cannot answer autonomously. |
| **`INSUFFICIENT_SUPPORT`**| Any | **`ESCALATE`** | Concepts ungrounded; potential hallucination hazard. |
| **`OUT_OF_SCOPE`** | Conf $\ge 0.90$ across all candidates | **`ABSTAIN`** | Query belongs outside tenant/project boundaries. |
| **`CONTRADICTORY`** | Any | **`ESCALATE`** | Competing candidates conflict factually. |

### 2.2 Prohibited Anti-Patterns (Negative Invariants)

The following behaviors are strictly forbidden by architectural invariant:

* **`PARTIAL_SUPPORT` $\rightarrow$ `ANSWER`**: FORBIDDEN. Partial matches never produce autonomous answers.
* **`HIGH_DENSE_SIMILARITY` $\rightarrow$ `ANSWER`**: FORBIDDEN. Similarity is a retrieval heuristic, not evidence.
* **`RRF_SCORE` $\rightarrow$ `ANSWER`**: FORBIDDEN. Fusion ranking scores have zero factual verification power.
* **`LEXICAL_MATCH_ISOLATED` $\rightarrow$ `ANSWER`**: FORBIDDEN. Keyword overlap without semantic predicate grounding is untrusted.
* **`MISSING_EVIDENCE` $\rightarrow$ `IMPLICIT_INFERENCE`**: FORBIDDEN. Fallback must always fail closed (`ESCALATE` or `ABSTAIN`).

---

## 3. Separation of Responsibilities

Each layer in the retrieval pipeline is decoupled with strict single responsibilities:

1. **Retriever**:
   - *Responsibility*: Retrieve candidate documents ($K \le 10$) using hybrid dense and lexical indexing.
   - *Boundary*: Does NOT decide truth, factual support, or autonomous answering.
2. **Verifier**:
   - *Responsibility*: Inspect each candidate individually for scope alignment, cryptographic provenance, and explicit factual predicate grounding.
   - *Boundary*: Does NOT determine final answer state or system action.
3. **Aggregator**:
   - *Responsibility*: Aggregate candidate judgments across the Top-K candidate pool according to the Strict Tri-State rules.
   - *Boundary*: Does NOT synthesize new factual assertions not present in candidate outputs.
4. **Policy**:
   - *Responsibility*: Emit the final executable action (`ANSWER`, `ESCALATE`, `ABSTAIN`) with mandatory audit telemetry.

---

## 4. Critical Safety Rules & Fail-Closed Semantics

### 4.1 Candidate Dominance Invariant
The presence of `PARTIAL_SUPPORT` candidates at any rank (e.g., ranks 1 through 10) **NEVER** elevates the query state to `ANSWER`.
Only the presence of at least one candidate with verified **`DIRECT_SUPPORT`** allows transition to `ANSWER`.

*Example A (Direct Support Discovered Deep in Pool)*:
- Rank 1: `INSUFFICIENT_SUPPORT`
- Rank 2: `INSUFFICIENT_SUPPORT`
- Rank 3: `PARTIAL_SUPPORT`
- Rank 4: `PARTIAL_SUPPORT`
- Rank 5: `DIRECT_SUPPORT` (verified)
- **Result**: `ANSWER` (Rank 5 provides verified factual grounding).

*Example B (Cumulative Partial Matches without Direct Support)*:
- Rank 1..10: All `PARTIAL_SUPPORT`
- **Result**: `ESCALATE` (Autonomous answering forbidden; escalated to secondary/human loop).

### 4.2 Mandatory Observability Telemetry
Any decision resulting in `ANSWER` MUST provide a complete, non-null telemetry envelope:
- `query_id` & `query_text`
- `candidate_document_id`
- `document_identity` (canonical URI/hash)
- `evidence_class` (`HIGH_EVIDENCE` from `DIRECT_SUPPORT`)
- `confidence` (calibrated $\ge 0.80$)
- `supporting_spans` (exact lines/snippets extracted from source)
- `provenance` (SHA-256 and commit hash verified)
- `scope` (tenant, project_id, trust_zone verified)
- `verifier_version`
- `aggregation_policy` (`STRICT_DIRECT_ONLY`)
- `retrieval_rank`

**Fail-Closed Rule**: If any required telemetry field is missing, empty, or unverified, autonomous `ANSWER` is immediately prohibited, and the decision falls back closed to **`ESCALATE`**.

---

## 5. Hard Negative Regression Suite

The canonical unsupported queries from V0.2 semantic validation are designated as permanent regression benchmarks:

1. **`QRY-34`**: *"como treinar uma rede neural convolucional para visao computacional em pytorch"*
   - *Invariant*: **MUST NEVER** produce `ANSWER`.
   - *Target*: `ESCALATE` (due to ungrounded ML framework predicates in PUB Core domain).
2. **`QRY-35`**: *"configuracao de cluster kubernetes com istio service mesh e pods autoscale"*
   - *Invariant*: **MUST NEVER** produce `ANSWER` despite high cosine similarity (`0.677905`).
   - *Target*: `ESCALATE` (hard negative containing generic distributed systems terminology).
3. **`QRY-36`**: *"contrato inteligente em solidity para minting de nfts erc-721 na blockchain ethereum"*
   - *Invariant*: **MUST NEVER** produce `ANSWER`.
   - *Target*: `ABSTAIN` (completely out of scope; zero domain vocabulary overlap).

---

## 6. Limitations & Status

* **Status**: `EXPERIMENTAL`
* **Calibration Scope**: Evaluated on 36 queries (33 supported, 3 unsupported) on the 44-document frozen V0.2 snapshot.
* **Limitations**: While empirical precision is 100% on this benchmark, statistical power on unsupported queries ($N=3$) is limited.
* **Gate for Production Promotion**: Prior to graduating ADR-003 to `PRODUCTION READY`, the test suite must pass the **Adversarial Benchmark Expansion** (Phase 2E.6), incorporating:
  - 100+ semantic hard negatives;
  - Cross-project tenant collisions;
  - Portuguese colloquial and noisy paraphrases;
  - Distributed multi-document evidence assertions;
  - Contradictory evidence stress tests.

---

## 7. Consequences & Verification

### Positive:
- Decouples retrieval depth ($K=10$, 93.94% recall) from decision safety ($0$ false accepts).
- Replaces uncalibrated scalar similarity thresholds with cryptographic provenance and verified factual grounding.
- Guarantees fail-closed behavior across all ambiguity and partial match cases.

### Negative:
- Direct autonomous answer rate is conservative (only queries with unambiguous direct support answer autonomously; partial matches escalate).
- Requires verification evaluation overhead across up to 10 candidates per query.
