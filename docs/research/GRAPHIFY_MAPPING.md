# PUB NEURAL <-> GRAPHIFY CONCEPT MAPPING

This document establishes the formal, deterministic mapping between Graphify AST extraction concepts and PUB Neural canonical graph primitives.

## 1. Node & Entity Mapping

| Graphify Node Property / Type | PUB Neural Entity Type (`neural_entity_type`) | Canonical ID Format | Notes |
| :--- | :--- | :--- | :--- |
| `file_type: "document"`, `*.md`, `*.txt` | `DOCUMENT` | `document:{project_id}:{slug}` | File-level document nodes |
| `file_type: "code"`, File root node | `DOCUMENT` / `SOURCE` | `document:{project_id}:{slug}` | Module/file level container |
| `function`, `method` | `CONCEPT` | `concept:{project_id}:{slug}` | Capability / functional unit |
| `class`, `struct`, `interface` | `CONCEPT` | `concept:{project_id}:{slug}` | Structural entity |
| `variable`, `constant`, `field` | `CONCEPT` | `concept:{project_id}:{slug}` | Code symbol |
| `community` | Graph Cluster Metadata | N/A (stored in `scope` or node attributes) | Louvain / Leiden partition index |

---

## 2. Edge & Relationship Mapping

| Graphify Relation | PUB Neural Relation Type (`neural_relation_type`) | Directionality | Semantic Meaning |
| :--- | :--- | :--- | :--- |
| `imports` | `DEPENDS_ON` | Directed ($A \to B$) | Source file requires target module |
| `calls` | `USES` | Directed ($A \to B$) | Function / method invokes target function |
| `uses` | `USES` | Directed ($A \to B$) | General usage dependency |
| `inherits` | `IMPLEMENTS` | Directed ($A \to B$) | Class inherits or implements interface |
| `references` | `RELATED_TO` | Directed ($A \to B$) | Symbolic mention or reference |
| `contains` | `RELATED_TO` | Directed ($A \to B$) | File contains symbol |

---

## 3. Confidence & Provenance Mapping

| Graphify Confidence | PUB Neural Confidence Score | Promotion State | Provenance Classification |
| :--- | :--- | :--- | :--- |
| `EXTRACTED` | `0.95 - 1.00` | `OBSERVED` / `EXTRACTED` | Grounded in AST syntax |
| `INFERRED` | `0.55 - 0.65` | `CANDIDATE` | Deductive inference (requires caveat) |
| `AMBIGUOUS` | `0.20` | `CAPTURED` | Uncertain; subject to human/sovereign review |

---

## 4. Evidence Locators

Each normalized entity or relation maps its code anchor to `pub_neural.neural_evidence`:
- `start_line` / `end_line`: Extracted from `source_location` (e.g. `L42` or `L10-L25`).
- `file_path`: Extracted from `source_file`.
- `content_hash`: SHA-256 of code quote or label.
- `extractor_version`: `graphify:v8:adapter_v1.0.0`.
