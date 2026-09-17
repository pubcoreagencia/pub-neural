# PUB NEURAL — GRAPHIFY INTEGRATION SPECIFICATION

## 1. Context & Objective

PUB Neural integrates graph extraction capabilities from **Graphify** (`branch v8`, Apache-2.0).

> [!IMPORTANT]
> **Core Architectural Invariant:**
>
> `GRAPHIFY = ENGINE/CAPABILITY DE GRAPH EXTRACTION`
> `PUB NEURAL = CANONICAL COGNITIVE GRAPH + MEMORY + PROVENANCE + GOVERNANCE`
>
> Graphify is an external extractor capability. PUB Neural is the sovereign Source of Truth.
> Neural does NOT become a clone or fork of Graphify.

---

## 2. Boundary Definition

```text
┌────────────────────────────────────────────────────────┐
│                   GRAPHIFY OWNS                        │
│  - Source scanning & Tree-sitter AST parsing          │
│  - Structural relationship discovery (AST)             │
│  - Local syntax graph construction                     │
│  - Graph traversal primitives                          │
│  - Community detection algorithms                      │
│  - Structural explanations & god-node detection        │
└──────────────────────────┬─────────────────────────────┘
                           │ (Intermediate graph.json / CLI)
                           ▼
┌────────────────────────────────────────────────────────┐
│               PUB NEURAL ADAPTER LAYER                 │
│  - Subprocess / CLI invocation isolation               │
│  - Security sanitization & secret filtering            │
│  - JSON schema validation & size cap enforcement       │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│                PUB NEURAL NORMALIZER                   │
│  - Node -> Canonical Entity conversion                 │
│  - Edge -> Canonical Relation conversion               │
│  - EXTRACTED -> High confidence provenance             │
│  - INFERRED  -> Inferential provenance (non-factual)  │
│  - Evidence anchoring (file, line ranges, quotes)      │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│                   PUB NEURAL OWNS                      │
│  - Canonical Identity & Deterministic UUIDs            │
│  - Provenance & Bi-temporal State (valid / recorded)   │
│  - Epistemic Classification (CONFIRMED/PROPOSED)       │
│  - Canonical Event Log (neural_events)                 │
│  - Knowledge Lifecycle & Governance Promotion          │
│  - Embeddings & Vector Indexing (pgvector)             │
│  - Hybrid 3-Way Retrieval (Lexical + Dense + Graph)   │
│  - Retrieval Abstention Gate                           │
│  - Research Intelligence & Findings                    │
└────────────────────────────────────────────────────────┘
```

---

## 3. Epistemic Integrity

1. **EXTRACTED Relations:**
   - Explicitly present in the source AST (e.g. `import`, explicit function call).
   - Mapped to confidence score `0.95 - 1.00`.
   - Classified as direct observational knowledge.

2. **INFERRED Relations:**
   - Deduced through heuristic analysis, second-pass call matching, or co-occurrence.
   - Mapped to confidence score `0.55 - 0.65`.
   - **Never promoted automatically to institutional facts**.
   - Kept in `CANDIDATE` state and flagged with epistemic caveat.

3. **AMBIGUOUS Relations:**
   - Weak confidence (`0.20`), flagged for human or sovereign review.

---

## 4. Pipeline & Lifecycle

1. **Scan Phase:** Graphify extracts code dependencies from target repository snapshot.
2. **Export Phase:** Emits `graph.json` artifact.
3. **Adapt Phase:** Neural Adapter reads `graph.json`, applies size caps and secret scans.
4. **Normalize Phase:** Neural Normalizer transforms raw nodes and links into `ENTITY_EXTRACTED` and `RELATION_EXTRACTED` payloads.
5. **Event Ingest Phase:** Events appended to `pub_neural.neural_events` with deterministic UUIDv5 identities.
6. **Projection Phase:** Projector updates `neural_nodes`, `neural_edges`, and `neural_evidence`.
7. **Retrieval Phase:** Graph Search evaluates neighborhoods, structural paths, and feeds 3-way RRF.
