# microsoft/graphrag — Architecture Analysis

## 1. Storage & Data Pipeline
* Operates as an offline, batch-oriented data processing pipeline.
* Persists graph and text artifacts into column-oriented **Apache Parquet** tables on local disk or Azure Blob Storage.
* Vector embeddings are indexed in **LanceDB** or Azure AI Search.
* Does not use a live, transactional property graph database.

## 2. Hierarchical Leiden Clustering
* Implemented in `graphrag/graphs/hierarchical_leiden.py` using **`graspologic_native`** (Rust) and `graspologic`.
* Partitions entity-relationship graphs into multi-level hierarchical clusters ($C_0, C_1, \dots C_k$).
* Pre-computes comprehensive **Community Reports** using LLMs, generating structured summaries, findings, and ratings per cluster.

## 3. Query Path Architectures
1. **Global Search:** Map-Reduce query engine executing across community report summaries to answer high-level, dataset-wide thematic questions.
2. **Local Search:** Entity-centric expansion (1-2 hops) combining seed node vector matches with neighboring relationships, covariates, and text units.
3. **DRIFT Search:** Dynamic Reasoning and Inference with Flexible Traversal; uses a high-level community primer to guide targeted local search queries.
