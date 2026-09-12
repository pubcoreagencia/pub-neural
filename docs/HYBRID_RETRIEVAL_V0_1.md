# PUB Neural / PDL — Hybrid Retrieval & Vector Indexing Specification (V0.1)

**Status:** IMPLEMENTED & OPERATIONAL  
**Layer:** `HYBRID_RETRIEVAL_AND_VECTOR_INDEXING`  
**Classification:** `DERIVED_OPERATIONAL_AI_STATE`  
**Canonical Event Boundary:** Projections derived strictly from `ENTITY_EXTRACTED` and `EVIDENCE_CAPTURED`. Zero new canonical event types added; Schema V0 and Projector V0.1 remain 100% frozen.

---

## 1. Vector Schema & Lineage Contract

The table `pub_neural.neural_vectors` stores dense vector embeddings derived from canonical knowledge graph projections:

```sql
CREATE TABLE IF NOT EXISTS pub_neural.neural_vectors (
    id UUID PRIMARY KEY,
    target_type VARCHAR(32) NOT NULL,
    target_id VARCHAR(128) NOT NULL,
    trust_zone VARCHAR(64) NOT NULL DEFAULT 'tz_internal_holding',
    project_id VARCHAR(64),
    model_id VARCHAR(64) NOT NULL,
    embedding vector(1536) NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    originating_event_id UUID NOT NULL REFERENCES pub_neural.neural_events(id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_neural_vectors_target_model UNIQUE (target_type, target_id, model_id),
    CONSTRAINT chk_neural_vectors_target_type CHECK (target_type IN ('NODE', 'EVIDENCE', 'COMMUNITY'))
);
```

### Deterministic Content-Addressable Identity
```text
vector_id = UUIDv5(PUB_NEURAL_VECTOR_NS, target_type + ":" + target_id + ":" + model_id)
content_hash = SHA256(trimmed_text)
```

### Staleness & Model Coexistence
- **Staleness Detection:** Prior to dense retrieval, `content_hash` in `neural_vectors` is compared against live text in `neural_nodes` or `neural_evidence`. Stale vectors are automatically filtered out from search results until refreshed by `VectorIndexingWorker`.
- **Model Coexistence:** Primary uniqueness is `(target_type, target_id, model_id)`, allowing parallel embeddings (e.g. `text-embedding-3-small` and `text-embedding-3-large`) for the same node without mutual interference.

---

## 2. Vector Indexing Tradeoff & Selection

| Dimension | HNSW (`vector_cosine_ops`) | IVFFlat (`vector_cosine_ops`) | Selection for V0.1 |
|---|---|---|---|
| Expected Vectors | 1k to 100k items | > 100k items | **HNSW** |
| Dimensionality | 1536 float4 | 1536 float4 | **HNSW** |
| Mutation Pattern | Incremental streaming per event | Batch training clusters | **HNSW** |
| Query Recall Target | High recall (> 98%) | Moderate recall (~ 90%) | **HNSW** |
| Rebuild Cost | Low at V0 scale | High cluster re-training | **HNSW** |

- **Metric:** Cosine distance (`<=>`).
- **Configuration:** `m = 16, ef_construction = 64`.

---

## 3. Lexical Retrieval & Portuguese Stemming

- **Ranking Engine:** `POSTGRES_FTS_RANKING` (`ts_rank`).
- **Language Config:** `portuguese` stemming with stopword removal.
- **Field Weights:**
  - `Title`: Weight 'A' (1.0)
  - `Summary`: Weight 'B' (0.4)
  - `Content`: Weight 'C' (0.2)

---

## 4. Reciprocal Rank Fusion (RRF) Formulation

Given two independent candidate rankings (Lexical and Dense):

$$RRF\_score(d) = \sum_{i \in \{lexical, dense\}} \frac{1}{k + rank_i(d)}$$

- **Parameters:**
  - $k = 60$ (standard smoothing constant)
  - $K_{lexical} = 20$
  - $K_{dense} = 20$
  - $K_{final} = 10$
- **Deterministic Tie-Breaking:** `(rrf_score DESC, target_id ASC)`.

---

## 5. Row-Level Security (RLS) Isolation

Queries enforce tenant clearance:
- Filter condition: `(trust_zone = %s) AND (project_id = %s OR project_id IS NULL)`.
- Verified in `VECTOR-14`: No cross-boundary leakage between `tz_internal_holding` and `tz_client_facing`.
