# GraphRAG vs. PUB Neural — Concrete Comparison

| Dimension | PUB Neural | Microsoft GraphRAG | Comparison Analysis |
| :--- | :--- | :--- | :--- |
| **Operational Model** | Live, transactional event ingestion and querying | Offline, batch transformation pipeline | PUB Neural handles live execution gate writebacks; GraphRAG is designed for static document corpora. |
| **Storage Architecture**| PostgreSQL 16 + pgvector (ACID relational) | Parquet files + LanceDB (Columnar batch) | GraphRAG cannot support transactional concurrency, foreign keys, or Row-Level Security. |
| **Community Clustering**| Table schema migrated (`neural_community_reports`) | Implemented: Hierarchical Leiden (`graspologic_native`) | Schema is ready in PUB Neural; GraphRAG provides the proven clustering algorithm and prompts. |
| **Global Thematic RAG**| Hybrid search (RRF FTS + vector) focused on local entities| Map-Reduce over hierarchical community summaries | GraphRAG excels at dataset-wide thematic synthesis; PUB Neural currently focuses on targeted retrieval. |
| **Governance & Security**| Database Row-Level Security, Trust Zones, CEO bypass | None (File-based storage without access control) | PUB Neural provides cryptographic multi-tenancy; GraphRAG has no data-tier authorization. |
| **Extraction Quality** | Custom Python extractors bound to fixed ontology | Iterative gleaning loop (`LOOP_PROMPT`) | GraphRAG's gleaning loop reduces false negatives during entity extraction. |
