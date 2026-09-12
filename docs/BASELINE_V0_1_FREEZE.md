# PUB Neural / PDL — Baseline V0.1 Foundation Freeze Specification

**Status:** OFFICIALLY FROZEN BASELINE  
**Git Tag:** `pub-neural-v0.1-foundation`  
**Scope:** Foundation Layer (Schema V0, Projector V0.1, Ingestion & Graph Extraction V0.1)  
**Security & Governance Invariant:** `SOURCE -> VERIFY_BLOB -> CANONICAL_EVENT_LOG -> PROJECTOR -> DETERMINISTIC_PROJECTIONS`  

---

## 1. Frozen Baseline Components

The following components are strictly frozen. Any subsequent modifications require a formalized architectural divergence document and a new semantic version baseline:

1. **Schema V0 (`migrations/0001_initial_v0_schema.sql`):**
   - Canonical event log (`neural_events`, `neural_event_parents`).
   - Append-only immutability triggers and DAG acyclicity verification.
   - Dual-zone multi-tenant RLS policies (`tz_internal_holding`, `tz_client_facing`).
   - Trusted actor authority registry and opaque 256-bit bearer session validation.
   - Idempotency records (`neural_idempotency_records`) and verified blob manifests (`source_blobs`).
   - Projections: `neural_nodes`, `neural_edges`, `neural_sources`, `neural_evidence`, `neural_vectors`, `neural_community_reports`, `neural_fts`.

2. **Projector Engine V0.1 (`src/projector_engine.sql`):**
   - Deterministic replay cursor (`pub_neural.run_projector`).
   - Checkpoint tracker (`neural_projection_checkpoints`) maintaining state transitions (`HEALTHY`, `STALLED`).
   - Multi-tenant projector state with support for atomic full replay (`is_full_replay`).
   - Isolated historical replay semantics preventing operational projection corruption.
   - Reducer taxonomy covering 20 canonical event types (11 PROJECTED, 9 PASS_THROUGH).

3. **Ingestion & Graph Extraction Engine V0.1 (`src/ingestion/`, `src/extraction/`):**
   - Allowlist scope containment (`AUTHORIZED_REPOSITORIES`).
   - Multi-boundary crash-resilient blob vault with normalized hashing (`BlobVault`).
   - Real semantic idempotency backed by `pub_neural.neural_idempotency_records`.
   - Process crash / SIGKILL resilience with zero orphan lineages.
   - Content-addressed document chunking and parsed event identities (`content_sha256`).
   - Collision-resistant entity identifiers with Unicode NFKD normalization and 8-character title hash disambiguation.

---

## 2. Cryptographic Checksum Manifest (`FINAL_REPOSITORY_EVIDENCE`)

The exact SHA-256 digests binding this frozen baseline are:

```text
8d5e86352816c7820d4b37b7062ddaf06424de5d13299516a5ca01fde7f9bf02  src/projector_engine.sql
f4d6521f18ae5e90fad1ab3414f3493223f6497abe5b8c26965058937a310b40  migrations/0001_initial_v0_schema.sql
6ef9dae398f7e3f811e9b7200ec1ff265122498d31d8fac281ab6f27ca609323  src/ingestion/__init__.py
107316cb6e0d8b252b0c1b66ab319bd5625bfc7e4fd9c92234280bee17b28226  src/ingestion/blob_vault.py
e582385bc85610b4fa7314a63df8197a455ee1a912d1a8dfa80dada75fa9d959  src/ingestion/client.py
3d521763af3e711f49546f7df11b9c8b5e3d8964b8d706103537fcb991244148  src/ingestion/doc_capturer.py
f00aa061d81499dd1f019206fa8616e823cce8af254bd7c9386259461802bba7  src/ingestion/doc_parser.py
15680d06d0ed16b68ffe7e61180d54dac0efc4f79af31ecf51772cb9722195fe  src/ingestion/scout.py
a4a07d08f3b73166861d34a05f8479a38be6ae9508cc2070eede8ec2de727adb  src/ingestion/source_ingestor.py
e89613855127f34a0fb89211f31b8097865182f0e3cbef7d807bc10b4066ee6d  src/extraction/__init__.py
f883374cf08459203be6ac6bc74c739d4152e437b3cee655becbe13b0e7be903  src/extraction/entity_extractor.py
9b0dc10ce2e0fc4edd2c11b02810f1c636a1f90bc7e7e3bdfe5cb10ce6aea415  src/extraction/evidence_capturer.py
a811e37dffd6d876857438ab74455265df5f84ea62e2597d56750735c88656d3  src/extraction/relation_extractor.py
208b566ad8128d9ce1dfd51d6ad79c5b5f4e11b970d512c7046b67151e92c390  tests/ingestion/test_ingestion_and_extraction.py
f5e4a2839c7738e946cdf5da51bd077078614c55f384a811e965badc946a3b12  tests/ingestion/run_ingestion_tests.sh
f22a9ef37c07554cf692d7c94b85df40a88cfee618740d4bc901b7e515a51f54  docs/INGESTION_V0_1_HARDENING_REPORT.md
```

---

## 3. Immutability Policy & Governance Rules

1. **Zero Direct Writes to Projections:** Neither workers nor application APIs may issue direct `INSERT`, `UPDATE`, or `DELETE` statements against projection tables (`neural_nodes`, `neural_edges`, `neural_sources`, `neural_evidence`, `neural_fts`).
2. **Canonical Mutation Invariant:** Every modification to the knowledge graph must originate as an authenticated canonical event authored via `pub_neural.append_event()`.
3. **Deterministic Derivation:** The graph projection state is completely reconstructible from sequence 1 through the projector engine without external side effects.
4. **Baseline Evolution Rule:** Future changes to schema, projectors, or ingestion contracts require a formal divergence proposal, audit verification, and tagging of a new baseline (e.g., `v0.2`).
