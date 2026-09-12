# PUB Neural / PDL — Technical Evidence Audit & Projector V0.1 Adversarial Report

**Evaluation Date:** 2026-09-12  
**Target Environment:** Isolated PostgreSQL 16.8 (`pgvector/pgvector:pg16` Docker container)  
**Schema & Engine Baseline:** `migrations/0001_initial_v0_schema.sql` + `src/projector_engine.sql`  
**Test Suite:** `tests/projectors/test_projectors_and_replay.sql` (Tests RPL-01 to RPL-20)  
**Verification Harness:** `tests/projectors/run_projector_tests.sh`

---

## 1. Executive Status & Final Gate Matrix

```text
HISTORICAL_REPLAY_ISOLATION = PASS
TAXONOMY_SEMANTIC_ALIGNMENT = PASS
REAL_RUN_PROJECTOR_CRASH_TEST = PASS
CRASH_PID_IDENTITY_PROOF = PASS
CRASH_SNAPSHOT_ROLLBACK = PASS
FULL_REPLAY_ATOMICITY = PASS
TAXONOMY_20_OF_20 = PASS
TAXONOMY_PROJECTED = 11
TAXONOMY_PASS_THROUGH = 9

PROJECTOR_V0_1_FINAL = PASS
```

---

## 2. Evidence of Critical Blockers Resolution

### 2.1 BLOCKER 1 — Historical Replay Isolation Policy (`HISTORICAL_REPLAY_ON_LIVE_PROJECTOR = FORBIDDEN`)
* **Policy Mandate:** On a live, operational projector with an active checkpoint $C > 0$, any call to `run_projector(projector, from_sequence, ...)` where `from_sequence <= C` is strictly forbidden.
* **Failure Mode:** PostgreSQL raises an explicit exception:
  ```text
  HISTORICAL_REPLAY_FORBIDDEN: requested range (from %) precedes current projector checkpoint (%) on live projection. Use full_replay() for historical recomputation.
  ```
* **Operational Guarantee:**
  - `run_projector()` operates **only forward** from the next sequence after the current checkpoint (`from_sequence > C`).
  - Historical recomputation requires an explicit, transactional `full_replay()` or future isolated/temporary projections.
  - Zero historical event re-reduction can silently mutate operational rows or updated timestamps in `neural_nodes`, `neural_edges`, `neural_sources`, `neural_evidence`, or `neural_fts`.
* **Empirical Proof (Test RPL-20):**
  - Live state measured at checkpoint $C = 10$.
  - Attempted `run_projector('graph_projector', 1, 2)`: Trapped and rejected with `HISTORICAL_REPLAY_FORBIDDEN`.
  - Attempted boundary `run_projector('graph_projector', 10, 10)`: Trapped and rejected with `HISTORICAL_REPLAY_FORBIDDEN`.
  - MD5 snapshots taken across all 5 projections (`neural_nodes`, `neural_edges`, `neural_sources`, `neural_evidence`, `neural_fts`) proved bit-for-bit equality before and after the rejected calls:
    $$\text{SNAPSHOT\_BEFORE} \equiv \text{SNAPSHOT\_AFTER} \quad \wedge \quad \text{CHECKPOINT\_BEFORE} \equiv \text{CHECKPOINT\_AFTER}$$
* **Status:** **`HISTORICAL_REPLAY_ISOLATION = PASS`**

### 2.2 BLOCKER 2 — Taxonomy Semantic Alignment (`UPDATE neural_nodes`)
* **Audit Finding & Code Confirmation:**
  - `DECISION_RATIFIED` reducer action:
    ```sql
    UPDATE pub_neural.neural_nodes
    SET promotion_state = 'INSTITUTIONAL',
        conflict_state = 'RESOLVED',
        is_active = TRUE,
        promotion_reason = 'Ratified by CEO: ' || COALESCE(p_event.payload->>'ratified_choice', ''),
        last_transition_event_id = p_event.id,
        updated_at = p_event.recorded_at
    WHERE id = p_event.payload->>'decision_id';
    ```
  - `GOVERNANCE_RULE_RATIFIED` reducer action:
    ```sql
    UPDATE pub_neural.neural_nodes
    SET promotion_state = 'INSTITUTIONAL',
        conflict_state = 'RESOLVED',
        is_active = TRUE,
        promotion_reason = 'Ratified by CEO governance mandate: ' || COALESCE(p_event.payload->>'compliance_mandate', ''),
        last_transition_event_id = p_event.id,
        updated_at = p_event.recorded_at
    WHERE id = p_event.payload->>'rule_id';
    ```
* **Documentation Reconciliation:** Corrected both entries from erroneous "INSERT" references to explicit `UPDATE neural_nodes (promotion_state='INSTITUTIONAL')`.
* **Status:** **`TAXONOMY_SEMANTIC_ALIGNMENT = PASS`**

### 2.3 BLOCKER 3 — Real `run_projector` Crash Test & PID Identity Proof
* **Verification Objective:** Prove that `pg_terminate_backend()` was executed specifically against the active backend running `pub_neural.run_projector(...)`, that the targeted PID was killed, and that PostgreSQL performed a clean, total transaction rollback.
* **PID Identity Proof (Captured from `pg_stat_activity` before termination):**
  ```text
  pid              | 160
  usename          | postgres
  application_name | psql
  query            | SET pub_neural.test_pause_at_sequence = '2';
                   | SET pub_neural.test_pause_duration = '10.0';
                   | SELECT * FROM pub_neural.run_projector('graph_projector', 1, NULL);
  state            | active
  wait_event_type  | Timeout
  wait_event       | PgSleep
  ```
* **Termination & Death Verification:** `pg_terminate_backend(160)` returned `t`. Subsequent query on `pg_stat_activity WHERE pid = 160` confirmed count = 0 (PID dead).
* **Snapshot Rollback Verification:** Full MD5 aggregate snapshots of all 5 projection tables and checkpoint sequence were taken before the crash and compared after backend death:
  ```text
  SNAPSHOT_BEFORE_CRASH == SNAPSHOT_AFTER_ROLLBACK
  (neural_nodes, neural_edges, neural_sources, neural_evidence, neural_fts, neural_projection_checkpoints)
  ```
* **Convergence:** Invoking `pub_neural.run_projector('graph_projector', 1, 2)` completed cleanly with `status = 'HEALTHY'`.
* **Status:** **`REAL_RUN_PROJECTOR_CRASH_TEST = PASS`** / **`CRASH_PID_IDENTITY_PROOF = PASS`** / **`CRASH_SNAPSHOT_ROLLBACK = PASS`**

### 2.4 BLOCKER 4 — Atomic Full Replay (MODELO A)
* **Verification Objective:** Prove that when `full_replay()` encounters a malformed event in the log, the initial `TRUNCATE` is rolled back completely along with all partial work, leaving pre-existing projections, checkpoints, and canonical tables 100% intact.
* **Evidence (Test RPL-19):**
  - Canonical event log count before: $N$. After: $N+1$ (the injected corrupt event).
  - Source blobs count before/after: Unchanged.
  - Event parents count before/after: Unchanged.
  - Nodes, edges, and checkpoint counts before/after: Exact match.
* **Status:** **`FULL_REPLAY_ATOMICITY = PASS` (MODELO A — ATOMIC FULL REPLAY)**

---

## 3. Canonical Event Taxonomy Matrix (11 PROJECTED / 9 PASS_THROUGH)

| # | Event Type | Schema Definition | Reducer Action | Semantic Classification | Verification Reference |
|---|---|---|---|---|---|
| 1 | `GENESIS_BOOTSTRAP` | Schema V0 §4.5 | Canonical log record | `PASS_THROUGH` | Bootstrap Assertion |
| 2 | `SOURCE_BLOB_VERIFIED` | Schema V0 §4.5 | Canonical manifest in `source_blobs` | `PASS_THROUGH` | RPL-01, RPL-10 |
| 3 | `SOURCE_INGESTED` | Schema V0 §4.5 | Upserts `neural_sources` | **`PROJECTED`** | RPL-01, RPL-03 |
| 4 | `SOURCE_DISCOVERED` | Schema V0 §4.5 | Discovery log record | `PASS_THROUGH` | Reducer Engine |
| 5 | `DOCUMENT_CAPTURED` | Schema V0 §4.5 | Ingestion capture record | `PASS_THROUGH` | Reducer Engine |
| 6 | `DOCUMENT_PARSED` | Schema V0 §4.5 | Ingestion chunk lineage | `PASS_THROUGH` | Reducer Engine |
| 7 | `EVIDENCE_CAPTURED` | Schema V0 §4.5 | Inserts `neural_evidence` | **`PROJECTED`** | RPL-01, RPL-03, RPL-11 |
| 8 | `ENTITY_EXTRACTED` | Schema V0 §4.5 | Upserts `neural_nodes` & `neural_fts` | **`PROJECTED`** | RPL-01, RPL-03, RPL-04 |
| 9 | `RELATION_EXTRACTED` | Schema V0 §4.5 | Upserts `neural_edges` | **`PROJECTED`** | RPL-01, RPL-03, RPL-11 |
| 10 | `KNOWLEDGE_CANDIDATE_CREATED` | Schema V0 §4.5 | Updates node `promotion_state='CANDIDATE'` | **`PROJECTED`** | Reducer Engine |
| 11 | `KNOWLEDGE_VALIDATED` | Schema V0 §4.5 | Updates node `promotion_state='VALIDATED'` | **`PROJECTED`** | Reducer Engine |
| 12 | `KNOWLEDGE_SUPERSEDED` | Schema V0 §4.5 | Sets node `is_active=FALSE, conflict_state='SUPERSEDED'` | **`PROJECTED`** | Reducer Engine |
| 13 | `KNOWLEDGE_REJECTED` | Schema V0 §4.5 | Sets node `is_active=FALSE, conflict_state='REJECTED'` | **`PROJECTED`** | Reducer Engine |
| 14 | `PROMOTION_PROPOSED` | Schema V0 §4.5 | Updates node `promotion_state='INSTITUTIONAL_CANDIDATE'` | **`PROJECTED`** | Reducer Engine |
| 15 | `DECISION_PROPOSED` | Schema V0 §4.5 | ADR proposal log record | `PASS_THROUGH` | Reducer Engine |
| 16 | `DECISION_RATIFIED` | Schema V0 §4.5 | Updates decision node `promotion_state='INSTITUTIONAL'` | **`PROJECTED`** | RPL-01, RPL-03 |
| 17 | `GOVERNANCE_RULE_PROPOSED` | Schema V0 §4.5 | Policy proposal log record | `PASS_THROUGH` | Reducer Engine |
| 18 | `GOVERNANCE_RULE_RATIFIED` | Schema V0 §4.5 | Updates rule node `promotion_state='INSTITUTIONAL'` | **`PROJECTED`** | RPL-01, RPL-03 |
| 19 | `ACTOR_REGISTERED` | Schema V0 §4.5 | Trusted actor registry event | `PASS_THROUGH` | Reducer Engine |
| 20 | `ACTOR_REVOKED` | Schema V0 §4.5 | Trusted actor revocation event | `PASS_THROUGH` | Reducer Engine |

---

## 4. Complete Test Suite Coverage (RPL-01 to RPL-20 + Real Crash)

* **`RPL-01`**: Full deterministic replay from genesis.
* **`RPL-02`**: Partial replay from checkpoint processed 0 events.
* **`RPL-03`**: Double snapshot equality ($A == B$) across all 21+ projection columns including deterministic timestamps.
* **`RPL-04`**: 10x duplicate reduction confirmed full state idempotency (`SNAPSHOT_BEFORE == SNAPSHOT_AFTER`).
* **`RPL-05`**: Malformed payload classification as `MALFORMED` without crashing.
* **`RPL-06`**: Unsupported event type classification as `UNSUPPORTED`.
* **`RPL-07`**: Event ordering with sequence gaps processed cleanly.
* **`RPL-08`**: Causal DAG recursive traversal (CTE 2-level ancestor reachability).
* **`RPL-09`**: Multi-hop indirect cycle ($D_1 \to D_2 \to D_3 \to D_1$) trapped by recursive acyclicity trigger.
* **`RPL-10`**: Missing source blob manifest causes reduction to `REJECTED`.
* **`RPL-11`**: Node, edge, and evidence reconstructions verified.
* **`RPL-12`**: Lexical Portuguese FTS verified with title/summary/content weights and morphological stemming.
* **`RPL-13`**: Vector lineage with fixed 1536-dim contract verified.
* **`RPL-14`**: Community generation isolation retained historical generation.
* **`RPL-15`**: Checkpoint crash semantics: corrupt event does not advance cursor, STALLED status recorded.
* **`RPL-16`**: Unauthorized caller (`pub_neural_app`) blocked from invoking `full_replay`.
* **`RPL-17`**: Sequence range validation (inverted range rejected).
* **`RPL-18`**: Direct projection and checkpoint write lockdown verified for `pub_neural_app` (DML revoked).
* **`RPL-19`**: Atomic full replay verified (MODELO A): corrupted event triggers complete rollback of TRUNCATE while preserving canonical tables.
* **`RPL-20`**: Historical replay isolation on live projection: `p_from <= checkpoint` raises `HISTORICAL_REPLAY_FORBIDDEN` with 0 projection mutation and 0 checkpoint regression.
* **`REAL_CRASH`**: Direct `run_projector` termination with target PID verification and bit-for-bit snapshot rollback.

---

## 5. Non-Goals & Frozen Scope for V0.1

1. **Parallel Stream Partitioning:** Replay remains sequential and monotonic per projector, serialized via `pg_advisory_xact_lock(hashtext('projector_lock:' || projector_name))`.
2. **LLM & Vector Embedding Synthesis:** Embedding calculation and LLM community summary generation remain external worker responsibilities; the database engine strictly projects and validates lineage.
3. **External Consumer Notifications:** Streaming `pg_notify` for background daemon wakeups is deferred to V0.2.
4. **Historical Branch/Diff Projections:** Replaying historical segments to compare against current state must be executed via separate isolated/temporary tables, not against the live operational projection.
