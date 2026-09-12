# PUB Neural / PDL — Graph Extraction Workers Specification V0.1

**Status:** CANONICAL ARCHITECTURAL SPECIFICATION  
**Scope:** Knowledge Graph Extraction, Relational Lineage & Evidence Locators  
**Contract Invariant:** `DOCUMENT_PARSED -> ENTITY_EXTRACTED -> RELATION_EXTRACTED -> EVIDENCE_CAPTURED`  

---

## 1. Executive Extraction Architecture

Graph Extraction Workers transform structured text units (`DOCUMENT_PARSED`) into semantic entities, typed relations, and grounded evidence locators.
Workers do **NOT** mutate database projection tables directly. They author canonical events to `pub_neural.neural_events`, leaving projection derivation entirely to `pub_neural.reduce_event()`.

```text
               +-------------------------------------------+
               |             DOCUMENT_PARSED               |
               |        (Chunks, Offsets, Text)            |
               +---------------------+---------------------+
                                     |
                                     v
               +---------------------+---------------------+
               |         Entity Extractor Worker           |
               |     (Identify Entities, Assign Slugs)     |
               +---------------------+---------------------+
                                     |
                                     v
                            [ENTITY_EXTRACTED]
                                     |
                                     v
               +---------------------+---------------------+
               |        Relation Extractor Worker          |
               |     (Extract Typed Semantic Edges)        |
               +---------------------+---------------------+
                                     |
                                     v
                           [RELATION_EXTRACTED]
                                     |
                                     v
               +---------------------+---------------------+
               |         Evidence Capturer Worker          |
               |      (Bind Quotes, Lines, Offsets)        |
               +---------------------+---------------------+
                                     |
                                     v
                           [EVIDENCE_CAPTURED]
```

---

## 2. Entity Extraction Contract

### 2.1 Deterministic Collision-Resistant Entity Identity (`NODE_ID_DETERMINISM = SLUG_PLUS_HASH`)
Every node has a canonical deterministic identifier format:
- `<entity_type_lower>:<project_id>:<slug>-<title_hash>` (e.g. `decision:pub-ecom:auth-strategy-d5a52e94`).
- **Unicode & Diacritic Normalization:** Titles undergo NFKD Unicode normalization and ASCII transliteration, stripping diacritics while preserving phonetic semantics.
- **Collision Resistance:** Appending the 8-character hex digest of the raw title (`SHA256(raw_title)[:8]`) guarantees that distinct titles normalizing to identical slugs (e.g. "API Timeout" vs "API: Timeout") remain distinctly identifiable without ID collisions.

### 2.2 Event: `ENTITY_EXTRACTED`
- **Authorized Role:** `AGENT` or `CEO`
- **Payload Core Schema:**
  ```json
  {
    "node_id": "decision:pub-ecom:auth-strategy",
    "entity_type": "DECISION",
    "title": "Supabase SSR Session Tokens",
    "slug": "decision-pub-ecom-auth-strategy",
    "summary": "Architecture for SSR token refresh",
    "content": "Full extracted textual statement...",
    "trust_zone": "tz_internal_holding",
    "scope": "GLOBAL",
    "project_id": "pub-ecom",
    "initial_state": "CANDIDATE",
    "confidence_score": 0.95,
    "source_chunk_id": "chunk:pub-ecom:architecture:0",
    "extractor_version": "v1.0.0"
  }
  ```
- **Projector Action:** Upserts row in `pub_neural.neural_nodes` and indexes lexical tsvector in `pub_neural.neural_fts`.

---

## 3. Relation Extraction Contract

### 3.1 Typed Relational Ontology
Allowed relation types (`pub_neural.neural_relation_type`):
`USES`, `DEPENDS_ON`, `IMPLEMENTS`, `DISCOVERED_IN`, `DERIVED_FROM`, `VALIDATED_BY`, `SUPPORTED_BY`, `CONTRADICTS`, `SUPERSEDES`, `RELATED_TO`, `APPLIES_TO`, `CREATED_BY`, `USED_BY`, `REQUIRES`.

### 3.2 Event: `RELATION_EXTRACTED`
- **Authorized Role:** `AGENT` or `CEO`
- **Payload Core Schema:**
  ```json
  {
    "source_id": "decision:pub-ecom:auth-strategy",
    "relation_type": "IMPLEMENTS",
    "target_id": "rule:pub-core:zero-mutation",
    "weight": 0.95,
    "is_bidirectional": false,
    "trust_zone": "tz_internal_holding",
    "scope": "GLOBAL",
    "source_chunk_id": "chunk:pub-ecom:architecture:0",
    "extractor_version": "v1.0.0"
  }
  ```
- **Projector Action:** Upserts row in `pub_neural.neural_edges` (derives UUIDv5). Both `source_id` and `target_id` must exist in `neural_nodes`.

---

## 4. Evidence Capture Contract (`NO_PROVENANCE = NO_TRUST`)

### 4.1 Grounded Evidence Grounding
Every claim, entity, or relationship extracted from text must be backed by a locator pointing to the parent source.

### 4.2 Event: `EVIDENCE_CAPTURED`
- **Authorized Role:** `AGENT` or `CEO`
- **Payload Core Schema:**
  ```json
  {
    "target_type": "NODE",
    "target_id": "decision:pub-ecom:auth-strategy",
    "source_id": "0191e4f0-0020-7000-8000-000000000001",
    "content_hash": "c1a2b3...",
    "start_line": 12,
    "end_line": 15,
    "quote": "Tokens must be refreshed on edge middleware",
    "context_before": "Section 2.1 Auth flow",
    "context_after": "Latency SLA is 20ms",
    "confidence": 0.98,
    "validation_state": "UNVERIFIED",
    "extractor_version": "v1.0.0",
    "trust_zone": "tz_internal_holding",
    "project_id": "pub-ecom"
  }
  ```
- **Projector Action:** Inserts row in `pub_neural.neural_evidence` (derives UUIDv5). Target entity and source must exist.

---

## 5. Idempotency & Fault Isolation

1. **Idempotent Emission:** Workers compute a deterministic hash of `(source_chunk_id, entity_type, slug)` or `(source_id, relation_type, target_id)`. If an extraction was already registered in `neural_idempotency_records`, subsequent worker invocations skip re-emission.
2. **Crash & Restart:** Because events are append-only and UUIDs are deterministic v5 / slugs, killed workers can restart from the latest unprocessed chunk without creating orphan or duplicated knowledge entities.
3. **Database Security Lockdown:** Workers connect as `pub_neural_app`. Direct writes to `pub_neural.neural_nodes`, `neural_edges`, and `neural_evidence` are strictly revoked. All interactions go through `pub_neural.append_event()`.
