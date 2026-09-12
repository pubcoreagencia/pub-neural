# PUB Neural / PDL — Ingestion Pipelines Specification V0.1

**Status:** CANONICAL ARCHITECTURAL SPECIFICATION  
**Scope:** PUB Neural / PDL Core Ingestion Engine  
**Contract Invariant:** `SOURCE -> BLOB -> DOCUMENT -> CHUNK -> CANONICAL_EVENT_LOG -> PROJECTOR`  

---

## 1. Executive Pipeline Architecture

The Ingestion Pipeline converts raw files from authorized repositories into canonical events stored in `pub_neural.neural_events`. It enforces strict provenance, byte-for-byte immutability, cryptographic hashing, and decoupled worker execution.

```text
               +-------------------------------------------+
               |             Source Discovery              |
               |        (Repository / Path / Commit)       |
               +---------------------+---------------------+
                                     |
                                     v
                           [SOURCE_DISCOVERED]
                                     |
                                     v
               +---------------------+---------------------+
               |             Blob Vault                    |
               |     (Read Bytes, SHA-256 Digest)          |
               +---------------------+---------------------+
                                     |
                                     +---> pub_neural.source_blobs
                                     |
                                     v
                          [SOURCE_BLOB_VERIFIED]
                                     |
                                     v
               +---------------------+---------------------+
               |          Source Ingestion Worker          |
               |     (Verify Blob Invariant & Project)     |
               +---------------------+---------------------+
                                     |
                                     v
                             [SOURCE_INGESTED]
                                     |
                                     v
               +---------------------+---------------------+
               |         Document Capture Worker           |
               |        (Metadata, Raw Unit Size)          |
               +---------------------+---------------------+
                                     |
                                     v
                            [DOCUMENT_CAPTURED]
                                     |
                                     v
               +---------------------+---------------------+
               |         Document Parser Worker            |
               |     (Deterministic Lexical Chunking)      |
               +---------------------+---------------------+
                                     |
                                     v
                             [DOCUMENT_PARSED]
```

---

## 2. Authorized Sources & Discovery Contract

### 2.1 Authorized Scopes (`SOURCE_SCOPE = EXPLICIT_ALLOWLIST`)
Ingestion workers are restricted to explicitly configured repositories and paths:
- `pubcore/pub-ecom` (`main` branch)
- `pubcore/pub-neural` (`main` branch)
- `pubcore/holding-governance` (`main` branch)

Any source outside authorized projects or pointing to unregistered branches is rejected fail-closed.

### 2.2 Event: `SOURCE_DISCOVERED`
- **Authorized Role:** `INGESTOR` or `CEO`
- **Payload Core Schema:**
  ```json
  {
    "source_id": "0191e4f0-0020-7000-8000-000000000001",
    "repository": "pubcore/pub-ecom",
    "branch": "main",
    "commit_sha": "a1b2c3d4e5f6...",
    "file_path": "docs/architecture.md",
    "trust_zone": "tz_internal_holding",
    "project_id": "pub-ecom",
    "discovered_at": "2026-09-12T14:30:00Z"
  }
  ```
- **Lineage:** Recorded in canonical log. Pass-through for Graph Projector V0.1.

---

## 3. Blob Preservation Contract (`BLOB_PRESERVATION = FAIL_CLOSED`)

### 3.1 Cryptographic Hashing
For every discovered source:
1. `file_sha256`: SHA-256 computed strictly over the raw binary payload.
2. `content_hash`: Normalized content hash (e.g., stripping carriage returns `\r` and trailing whitespace for text formats).
3. `byte_size`: Exact integer size in bytes.
4. `mime_type`: Authoritative MIME string (`text/markdown`, `text/x-python`, `application/json`).
5. `storage_uri`: Immutable storage location (`file:///vault/blobs/...` or `s3://pub-vault/...`).

### 3.2 Authoritative Manifest Registration
Before emitting `SOURCE_INGESTED`, the worker MUST call:
```sql
SELECT pub_neural.register_verified_blob(
    p_file_sha256 := '...',
    p_content_hash := '...',
    p_storage_uri := '...',
    p_storage_backend := 'LOCAL_DISK',
    p_byte_size := 1024,
    p_mime_type := 'text/markdown',
    p_event_id := '...'::uuid
);
```
And emit:
```text
SOURCE_BLOB_VERIFIED
```

### 3.3 Event: `SOURCE_INGESTED`
- **Invariant:** Requires previously registered blob manifest with status `VERIFIED`.
- **Payload Core Schema:**
  ```json
  {
    "source_id": "0191e4f0-0020-7000-8000-000000000001",
    "repository": "pubcore/pub-ecom",
    "branch": "main",
    "commit_sha": "a1b2c3d4e5f6...",
    "file_path": "docs/architecture.md",
    "file_sha256": "3a7b9c...",
    "trust_zone": "tz_internal_holding",
    "project_id": "pub-ecom",
    "observed_at": "2026-09-12T14:30:00Z"
  }
  ```
- **Projector Action:** Upserts row in `pub_neural.neural_sources`.

---

## 4. Document Capture & Parsing Contracts

### 4.1 Event: `DOCUMENT_CAPTURED`
- **Purpose:** Represents the logical document extraction derived from a verified physical source blob.
- **Payload Core Schema:**
  ```json
  {
    "document_id": "doc:pub-ecom:architecture",
    "source_id": "0191e4f0-0020-7000-8000-000000000001",
    "file_sha256": "3a7b9c...",
    "document_title": "PUB Ecom Architecture Specification",
    "raw_byte_size": 1024,
    "mime_type": "text/markdown",
    "observed_at": "2026-09-12T14:30:00Z"
  }
  ```

### 4.2 Event: `DOCUMENT_PARSED`
- **Purpose:** Represents the structural decomposition of a document into deterministic chunks.
- **Event Identity Determinism:** `UUIDv5(ns, "parsed:{document_id}:{parser_version}:{content_hash}:{len(chunks)}")`.
- **Payload Core Schema:**
  ```json
  {
    "document_id": "doc:pub-ecom:architecture",
    "source_id": "0191e4f0-0020-7000-8000-000000000001",
    "parser_version": "v1.0.0",
    "content_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "text_unit_count": 3,
    "chunks": [
      {
        "chunk_id": "chunk:pub-ecom:architecture:0",
        "start_line": 1,
        "end_line": 25,
        "chunk_hash": "c1a2b3...",
        "content": "## 1. Overview\nArchitecture rules..."
      }
    ]
  }
  ```
- **Versioning Rule:** Reparsing with `parser_version = 'v2.0.0'` or across modified text content produces distinct deterministic events incorporating `content_hash`, preventing collision across versions or payloads while retaining historical lineage.

---

## 5. Failure Models, Atomicity & Hardened Idempotency

### 5.1 Real Semantic Idempotency (`neural_idempotency_records`)
All worker executions consult and write to `pub_neural.neural_idempotency_records`:
- **Workflow:**
  1. Derive deterministic request key (e.g. `scout:{repo}:{branch}:{commit}:{path}`, `source_ingest:...`, `parsed:...`).
  2. Normalize key with SHA-256 digest if exceeding VARCHAR(128).
  3. Consult `pub_neural.neural_idempotency_records` and `pub_neural.neural_events`.
  4. If record exists: return existing `resulting_event_id`, sequence, and payload with `idempotent_replay = True`.
  5. If new: execute append, write manifest/projections as applicable, commit, and record idempotency record.

### 5.2 Blob + Manifest + Canonical Event Atomicity & Crash Recovery
Filesystem storage and PostgreSQL transaction engines do not share a two-phase commit. To prevent split-brain states:
1. **Local/Remote Blob Storage Write:** Raw bytes are flushed and fsynced to disk (`{file_sha256}.bin`).
2. **Canonical Event Append:** `SOURCE_BLOB_VERIFIED` is committed to `pub_neural.neural_events`.
3. **Manifest Registration:** `pub_neural.register_verified_blob()` registers the row in `pub_neural.source_blobs` referencing the `originating_event_id`.
4. **Crash Recovery Semantics:** If an abort occurs after step 2 but before step 3, subsequent worker executions detect the committed `SOURCE_BLOB_VERIFIED` event, immediately complete manifest registration in `pub_neural.source_blobs`, and record idempotency, guaranteeing convergence without phantom events.

### 5.3 Source Context Authorization & Scope Containment
Caller-supplied values for `branch`, `trust_zone`, and `project_id` are strictly verified against the authoritative allowlist contract (`AUTHORIZED_REPOSITORIES`). Any discrepancy (e.g. attempting to ingest an authorized repository under an unapproved `project_id` or `trust_zone`) is rejected fail-closed with explicit error types:
- `UNAUTHORIZED_SOURCE_SCOPE`
- `UNAUTHORIZED_BRANCH`
- `UNAUTHORIZED_TRUST_ZONE`
- `UNAUTHORIZED_PROJECT_ID`

