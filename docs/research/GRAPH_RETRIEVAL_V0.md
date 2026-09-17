# PUB NEURAL — GRAPH RETRIEVAL V0 & 3-WAY HYBRID FUSION

## 1. Overview
Graph Retrieval introduces topological and structural retrieval capabilities to PUB Neural, complementing Lexical (PostgreSQL FTS) and Dense Vector (pgvector) modalities.

## 2. Fusion Architecture

```text
               RETRIEVAL OBJECTIVE
                       │
       ┌───────────────┼───────────────┐
       ▼               ▼               ▼
   KEYWORD           DENSE           GRAPH
  (PostgreSQL FTS)  (pgvector)    (Topological BFS)
       │               │               │
       └───────────────┼───────────────┘
                       ▼
             RECIPROCAL RANK FUSION
                       │
                       ▼
               ABSTENTION GATE
                       │
                       ▼
             FINAL KNOWLEDGE SET
```

## 3. 3-Way Reciprocal Rank Fusion Formula

For candidate item $d$:
$$\text{RRF}(d) = \sum_{m \in \{\text{lexical}, \text{dense}, \text{graph}\}} \frac{w_m}{k + \text{rank}_m(d)}$$

Where:
- $k = 60$ (smoothing constant).
- $w_{\text{lexical}} = 1.0$.
- $w_{\text{dense}} = 1.0$.
- $w_{\text{graph}} = 0.8$ (structural affinity weight).

Tie-breaking order: `(rrf_score DESC, target_id ASC)`.

## 4. Graph Candidate Generation
1. **Seed Matching**: Direct string / token match against node labels and identifiers.
2. **Neighborhood Expansion**: Bounded $1-2$ hop traversal over active directed and undirected edges.
3. **Shortest Path Discovery**: Computes direct semantic conduits connecting query entities.
4. **Structural Ranking**: Weighted by edge confidence, relation type (`USES`, `DEPENDS_ON` over `RELATED_TO`), and graph distance.
