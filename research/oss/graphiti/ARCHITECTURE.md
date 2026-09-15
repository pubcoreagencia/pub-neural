# getzep/graphiti — Architecture Analysis

## 1. Storage & Graph Model
* Relies on native property graph databases (**Neo4j** or **FalkorDB**).
* Graph schema uses Labeled Property Graph (LPG) nodes (`:Entity`, `:Episodic`, `:Community`, `:Saga`) and edges (`:RELATES_TO`, `:MENTIONS`, `:NEXT_EPISODE`).
* **PostgreSQL / pgvector Support:** None. Queries are written directly in Cypher.

## 2. Bi-Temporal Edge Model
Every factual relationship (`EntityEdge`) tracks four timestamps:
* `valid_at`: Real-world assertion start time.
* `invalid_at`: Real-world invalidation time (populated upon contradiction).
* `created_at`: System insertion timestamp.
* `expired_at`: System deprecation timestamp.

## 3. Incremental Updating & Contradiction Resolution
* Ingestion of an `:Episodic` node triggers an LLM deduplication pass (`dedupe_edges.py`).
* Facts are categorized as duplicate, novel, or contradictory.
* Contradictions update existing edges in place (`invalid_at = episode.valid_at`, `expired_at = utc_now()`) and insert a new valid edge.
* Graph state is mutated in place; it is not event-sourced.

## 4. Retrieval
* Multi-index search: Vector cosine similarity on embeddings + BM25 full-text + breadth-first search (BFS) graph traversal.
* Fused using Reciprocal Rank Fusion (RRF) and optional cross-encoder rerankers.
