# mem0ai/mem0 — Architecture Analysis

## 1. Core Memory Architecture
* Designed as an agent memory layer structured around scopes: `user_id`, `agent_id`, and `run_id`.
* Stores freeform text memories (`memory: str`) accompanied by JSON metadata.
* Storage backends are pluggable: Qdrant (default), PostgreSQL + pgvector, Chroma, SQLite (for history).

## 2. Graph Functionality Reality
* **Precise Audit Finding:** Graph memory is **not part of the current open-source (OSS) SDK** and is provided exclusively as a managed capability of the **Mem0 Platform**.
* In earlier releases, external graph drivers (Neo4j, Memgraph, Kùzu, Apache AGE) were supported. These drivers and the `enable_graph` parameter were removed from the OSS SDK to simplify the open-source codebase and differentiate the commercial platform.
* The open-source SDK provides only a secondary vector collection (`{collection}_entities`) used for entity vector boosting during search, with no graph edges or path traversals.

## 3. Ingestion & Retrieval Model
* **ADD-Only Extraction (v3):** Extracts facts from message turns and appends them without in-place mutation or deletion.
* **Retrieval:** Asymmetric boost model. Dense vector search generates 100% of candidate memories. BM25 keyword matching and entity overlaps are applied purely as score boosters during reranking.
