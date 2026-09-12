# PUB Neural / PDL — Ingestion & Extraction Hardening Report V0.1

**Status:** HARDENED & PHYSICALLY PROVEN BASELINE  
**Scope:** Ingestion Pipelines, Graph Extraction Workers, Event Log Boundary, and Projector V0.1 Integration  
**Test Suite:** `tests/ingestion/test_ingestion_and_extraction.py` (ING-01 to ING-22)  
**Verification Environment:** Clean Isolated Docker PostgreSQL 16 Container (`pgvector/pgvector:pg16`), Run 1 & Run 2 from scratch  
**Baseline Immutability:** `src/projector_engine.sql` (FROZEN, 0 diffs), `migrations/0001_initial_v0_schema.sql` (FROZEN, 0 diffs)  

---

## 1. Formal Audit Classification Matrix

| Hardening Item | Classification | Verification Test | Physical Evidence / Mechanism |
|:---|:---:|:---:|:---|
| **ING-16: Real Semantic Idempotency** | **PROVEN** | `test_ing_16_real_idempotent_retry` | Verified across all 8 workers (`Scout`, `BlobVault`, `SourceIngestor`, `DocCapture`, `DocParser`, `EntityExtractor`, `RelationExtractor`, `EvidenceCapturer`). In each case: `EVENT_COUNT_BEFORE`, `EVENT_COUNT_AFTER_FIRST == BEFORE + 1`, `EVENT_COUNT_AFTER_RETRY == AFTER_FIRST`, and `replay_payload == original_payload`. |
| **ING-17: Real Process SIGKILL Crash & Recovery** | **PROVEN** | `test_ing_17_real_worker_crash_restart` | Independent subprocess running worker killed via `os.kill(PID, signal.SIGKILL)` mid-transaction (exit code -9). New worker process spawned; operation retried; converged to exactly 1 event on stream (`stream_version=1`) with 0 duplicate rows and 0 orphan lineage records. |
| **ING-18: Multi-Boundary Blob Recovery** | **PROVEN** | `test_ing_18_blob_manifest_event_recovery` | Boundaries tested: (A) Pre-filesystem write; (B) Post-filesystem write, pre-DB; (C) Post-event append, pre-manifest registration. Retries proved self-healing manifest registration referencing originating event without phantom state. |
| **ING-19: Event Identity vs Observation Metadata** | **PROVEN** | `test_ing_19_event_payload_determinism` | Identity comparison snapshot proves `IDENTITY_A == IDENTITY_B` and `DOMAIN_PAYLOAD_A == DOMAIN_PAYLOAD_B`, with `discovered_at` / `observed_at` explicitly classified and preserved as operational metadata. |
| **ING-20: Document Parsed Content Identity** | **PROVEN** | `test_ing_20_parser_content_identity` | Evaluated two distinct contents under identical `(document_id, parser_version, chunk_count)`. Derivation embeds `content_hash`: `UUIDv5(ns, "parsed:{doc}:{ver}:{content_hash}:{chunks}")` yielding `event_id(A) != event_id(B)`. |
| **ING-21: Source Context Scope Authorization** | **PROVEN** | `test_ing_21_source_context_authorization` | Tested 5 dimensions: authorized scope passes; authorized repo + wrong branch fails (`UNAUTHORIZED_BRANCH`); wrong project fails (`UNAUTHORIZED_PROJECT_ID`); wrong trust zone fails (`UNAUTHORIZED_TRUST_ZONE`); unauthorized repo fails (`UNAUTHORIZED_SOURCE_SCOPE`). |
| **ING-22: Node ID Collision Resistance & Unicode** | **PROVEN** | `test_ing_22_node_id_collision_resistance` | Normalized Portuguese diacritics via Unicode NFKD (`Decisão` -> `decisao`); distinct titles with identical slugs disambiguated via 8-char SHA-256 suffix (`Payment API Timeout` != `Payment API: Timeout`); verbose titles guaranteed <= 128 chars. |

---

## 2. In-Depth Technical Evidence per Invariant

### 2.1 ING-16: Real Semantic Idempotency
- **Mechanism:**
  ```python
  key = self._normalize_idempotency_key(idempotency_key) # Max 128 chars
  existing = self.client.check_idempotency(key)
  if existing:
      ev = self.client.get_event_by_id(uuid.UUID(str(existing["resulting_event_id"])))
      return {
          "event_id": str(existing["resulting_event_id"]),
          "global_sequence": ev["global_sequence"] if ev else -1,
          "payload": existing["response_payload"],
          "idempotent_replay": True
      }
  ```
- **Observed Physical Result:**
  - `ScoutWorker`: Initial count 1 -> First run count 2 -> Retry count 2. Payload equal.
  - `BlobVault`: First run count 3 -> Retry count 3. SHA-256 equal.
  - `SourceIngestor`: First run count 4 -> Retry count 4. Payload equal.
  - `DocCapturer`: First run count 5 -> Retry count 5. Payload equal.
  - `DocParser`: First run count 6 -> Retry count 6. Chunks equal.
  - `EntityExtractor`: First run count 7 -> Retry count 7. Payload equal.
  - `RelationExtractor`: First run count 8 -> Retry count 8. Payload equal.
  - `EvidenceCapturer`: First run count 9 -> Retry count 9. Payload equal.
- **Invariant Proof:** Proves that retry requests do not issue database exceptions or insert redundant canonical events; instead they return original sequences and payloads from `pub_neural.neural_idempotency_records`.

### 2.2 ING-17: Real Worker Process SIGKILL Crash Recovery
- **Mechanism:** Subprocess spawns worker and prints `PID:<pid>` and `READY_FOR_CRASH`. Test harness sends `signal.SIGKILL`. Child terminates abruptly with exit code `-9`. Database transaction drops. New client reconnects and retries the logical ingest.
- **Observed Physical Result:**
  - Run 1: Worker terminated on PID `16428`.
  - Run 2: Worker terminated on PID `16450`.
  - In both executions: Uncommitted transactions dropped with 0 orphaned rows. Post-restart retry completed with `cnt = 1`, `max_stream_version = 1`, and `orphan_parents = 0`.
- **Invariant Proof:** Operating system kill of worker processes does not corrupt stream versioning or leave partially-committed events.

### 2.3 ING-18: Multi-Boundary Blob Recovery
- **Mechanism & Source of Truth:**
  - Canonical event log `pub_neural.neural_events` is the authoritative source of truth.
  - Filesystem storage and PostgreSQL cannot share a 2PC.
  - Boundary A: File not written -> Retry writes file, appends event, registers manifest.
  - Boundary B: File written, DB uncommitted -> Retry completes DB commit without file re-download.
  - Boundary C: Event appended, manifest crashed -> Retry checks `neural_events`, detects existing `SOURCE_BLOB_VERIFIED`, self-heals by registering manifest in `source_blobs`, returning `idempotent_replay = True`.
- **Observed Physical Result:** Clean reconciliation across boundaries A, B, and C with zero phantom records.

### 2.4 ING-19: Event Identity vs Observation Metadata
- **Classification:**
  - `IDENTITY_FIELDS`: `event_id` (UUIDv5) derived from domain parameters. Invariant across retries.
  - `DOMAIN_PAYLOAD`: `repository`, `branch`, `commit_sha`, `file_path`, `project_id`, `trust_zone`. Bit-for-bit identical.
  - `OBSERVATION_METADATA`: `discovered_at` and `observed_at` recorded at capture time and preserved unchanged on replay.
- **Observed Physical Result:** `IDENTITY_A == IDENTITY_B` and `DOMAIN_A == DOMAIN_B`.

### 2.5 ING-20: Document Parsed Content Identity
- **Mechanism:**
  ```python
  content_sha256 = hashlib.sha256(text_content.encode("utf-8")).hexdigest()
  event_id = uuid.uuid5(ns, f"parsed:{document_id}:{parser_version}:{content_sha256}:{len(chunks)}")
  ```
- **Observed Physical Result:**
  - Document A (3 chunks) vs Document B (3 chunks) with same `document_id` and `parser_version` produce distinct event IDs and distinct content hashes (`res_a["event_id"] != res_b["event_id"]`).
  - Identical content re-parsed produces exact identical event ID (`res_a1["event_id"] == res_a2["event_id"]`).

### 2.6 ING-21: Source Context Scope Authorization
- **Policy:** Explicit allowlist containment (`AUTHORIZED_REPOSITORIES`).
- **Observed Physical Result:**
  - Ingest with `pubcore/pub-ecom` on `main`, `tz_internal_holding`, `pub-ecom` -> PASS.
  - Ingest with wrong branch `feature-unapproved` -> ValueError(`UNAUTHORIZED_BRANCH`).
  - Ingest with wrong project `unauthorized-foreign-project` -> ValueError(`UNAUTHORIZED_PROJECT_ID`).
  - Ingest with wrong trust zone `tz_sovereign_governance` -> ValueError(`UNAUTHORIZED_TRUST_ZONE`).
  - Ingest with unknown repository `unauthorized/foreign-repo` -> ValueError(`UNAUTHORIZED_SOURCE_SCOPE`).

### 2.7 ING-22: Node ID Collision Resistance & Unicode Normalization
- **Algorithm:**
  ```python
  nfkd = unicodedata.normalize('NFKD', title.strip())
  ascii_text = nfkd.encode('ASCII', 'ignore').decode('ASCII').lower()
  clean_slug = re.sub(r'[^a-z0-9]+', '-', ascii_text).strip('-')
  title_hash = hashlib.sha256(title.strip().encode("utf-8")).hexdigest()[:8]
  node_id = f"{entity_type.lower()}:{project_id}:{clean_slug[:40]}-{title_hash}"
  ```
- **Observed Physical Result:**
  - `Decisão de Autenticação Segura` -> `decision:pub-ecom:decisao-de-autenticacao-segura-e05e5d16`
  - `Payment API Timeout` -> `rule:pub-ecom:payment-api-timeout-54e7d959`
  - `Payment API: Timeout` -> `rule:pub-ecom:payment-api-timeout-81b37341`
  - Long 180-char title -> truncated slug with hash, length 60 chars (well within SQL `VARCHAR(128)` limit), inserted into `pub_neural.neural_nodes` successfully.

---

## 3. Physical Test Execution Records (Clean Isolated Runs)

### Run 1 Execution Log:
```text
=== [1/6] Checking Docker Environment ===
=== [2/6] Starting Isolated PostgreSQL 16 Container ===
9100c2744e9efa1d0932897637fce1ac500f282cf3e5c2e3fd19d6afa75d3900
PostgreSQL is ready.
=== [3/6] Applying Baseline Schema Migration (0001) ===
=== [4/6] Applying Frozen Projector Engine V0.1 ===
=== [5/6] Executing Ingestion & Graph Extraction Test Suite (ING-01 to ING-22) ===
Ran 22 tests in 1.436s
OK
  -> TEST_PASSED [ING-01]: Source discovery emitted SOURCE_DISCOVERED.
  -> TEST_PASSED [ING-02]: Blob verification registered manifest and emitted SOURCE_BLOB_VERIFIED.
  -> TEST_PASSED [ING-03]: Blob hash mismatch rejected fail-closed.
  -> TEST_PASSED [ING-04]: Document capture preserved parent source lineage.
  -> TEST_PASSED [ING-05]: Parser chunk offsets and line boundaries verified.
  -> TEST_PASSED [ING-06]: Parser versioning emits separate lineage versions without overwriting.
  -> TEST_PASSED [ING-07]: Entity extraction emitted deterministic node with provenance.
  -> TEST_PASSED [ING-08]: Relation extraction emitted canonical typed edge.
  -> TEST_PASSED [ING-09]: Evidence locator bound quote, lines, and content hash.
  -> TEST_PASSED [ING-10]: 10x duplicate execution prevented semantic event duplication.
  -> TEST_PASSED [ING-11]: Worker client restart reconnected and resumed cleanly (SESSION_RECONNECT).
  -> TEST_PASSED [ING-12]: Entity identifiers and hashes are bit-for-bit deterministic.
  -> TEST_PASSED [ING-13]: 4-level causal parent lineage preserved in neural_event_parents.
  -> TEST_PASSED [ING-14]: Unauthorized source repository rejected fail-closed.
  -> TEST_PASSED [ING-15]: End-to-end ingestion pipeline successfully verified with Projector V0.1.
  -> TEST_PASSED [ING-16]: Real semantic idempotent retries verified across all 8 worker components with BEFORE==AFTER_RETRY counts and payload equality.
  -> TEST_PASSED [ING-17]: Real process SIGKILL crash (PID 16428) & restart converged with zero duplicate events and zero orphan lineage.
  -> TEST_PASSED [ING-18]: Multi-boundary blob recovery (A, B, C) proved recoverable convergence without split-brain state.
  -> TEST_PASSED [ING-19]: Explicit snapshot comparison proven (IDENTITY_A == IDENTITY_B, DOMAIN_PAYLOAD_A == DOMAIN_PAYLOAD_B).
  -> TEST_PASSED [ING-20]: Parser content identity proven (same content -> same ID; diff content -> diff ID).
  -> TEST_PASSED [ING-21]: Source ingest parameters fail-closed across all 4 unauthorized scope dimensions.
  -> TEST_PASSED [ING-22]: Unicode normalization, title hash disambiguation, and SQL length <= 128 verified.
=== [6/6] Cleanup Test Container ===
ALL INGESTION & GRAPH EXTRACTION TESTS PASSED!
```

### Run 2 Execution Log (Re-run from scratch):
```text
=== [1/6] Checking Docker Environment ===
=== [2/6] Starting Isolated PostgreSQL 16 Container ===
75510be2ec61bb381bc18bdd2e781cdd8424bc1e979066874c1ca4f0b54beb3e
PostgreSQL is ready.
=== [3/6] Applying Baseline Schema Migration (0001) ===
=== [4/6] Applying Frozen Projector Engine V0.1 ===
=== [5/6] Executing Ingestion & Graph Extraction Test Suite (ING-01 to ING-22) ===
Ran 22 tests in 1.646s
OK
  -> TEST_PASSED [ING-01]: Source discovery emitted SOURCE_DISCOVERED.
  -> TEST_PASSED [ING-02]: Blob verification registered manifest and emitted SOURCE_BLOB_VERIFIED.
  -> TEST_PASSED [ING-03]: Blob hash mismatch rejected fail-closed.
  -> TEST_PASSED [ING-04]: Document capture preserved parent source lineage.
  -> TEST_PASSED [ING-05]: Parser chunk offsets and line boundaries verified.
  -> TEST_PASSED [ING-06]: Parser versioning emits separate lineage versions without overwriting.
  -> TEST_PASSED [ING-07]: Entity extraction emitted deterministic node with provenance.
  -> TEST_PASSED [ING-08]: Relation extraction emitted canonical typed edge.
  -> TEST_PASSED [ING-09]: Evidence locator bound quote, lines, and content hash.
  -> TEST_PASSED [ING-10]: 10x duplicate execution prevented semantic event duplication.
  -> TEST_PASSED [ING-11]: Worker client restart reconnected and resumed cleanly (SESSION_RECONNECT).
  -> TEST_PASSED [ING-12]: Entity identifiers and hashes are bit-for-bit deterministic.
  -> TEST_PASSED [ING-13]: 4-level causal parent lineage preserved in neural_event_parents.
  -> TEST_PASSED [ING-14]: Unauthorized source repository rejected fail-closed.
  -> TEST_PASSED [ING-15]: End-to-end ingestion pipeline successfully verified with Projector V0.1.
  -> TEST_PASSED [ING-16]: Real semantic idempotent retries verified across all 8 worker components with BEFORE==AFTER_RETRY counts and payload equality.
  -> TEST_PASSED [ING-17]: Real process SIGKILL crash (PID 16450) & restart converged with zero duplicate events and zero orphan lineage.
  -> TEST_PASSED [ING-18]: Multi-boundary blob recovery (A, B, C) proved recoverable convergence without split-brain state.
  -> TEST_PASSED [ING-19]: Explicit snapshot comparison proven (IDENTITY_A == IDENTITY_B, DOMAIN_PAYLOAD_A == DOMAIN_PAYLOAD_B).
  -> TEST_PASSED [ING-20]: Parser content identity proven (same content -> same ID; diff content -> diff ID).
  -> TEST_PASSED [ING-21]: Source ingest parameters fail-closed across all 4 unauthorized scope dimensions.
  -> TEST_PASSED [ING-22]: Unicode normalization, title hash disambiguation, and SQL length <= 128 verified.
=== [6/6] Cleanup Test Container ===
ALL INGESTION & GRAPH EXTRACTION TESTS PASSED!
```

---

## 4. Final Repository Checksums (`FINAL_REPOSITORY_EVIDENCE`)

```text
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
8d5e86352816c7820d4b37b7062ddaf06424de5d13299516a5ca01fde7f9bf02  src/projector_engine.sql (FROZEN)
f4d6521f18ae5e90fad1ab3414f3493223f6497abe5b8c26965058937a310b40  migrations/0001_initial_v0_schema.sql (FROZEN)
```
