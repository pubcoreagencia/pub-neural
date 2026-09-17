# PUB NEURAL — RESEARCH LIFECYCLE SPECIFICATION V0

**Status:** CANONICAL LIFECYCLE SPECIFICATION  
**Document ID:** `docs/research/RESEARCH_LIFECYCLE_V0.md`  
**Consolidation Date:** 2026-09-17  

---

## 1. O Ciclo Operacional de Pesquisa (Research Lifecycle V0)

```text
DEFINE
  ↓
SCOUT
  ↓
COLLECT
  ↓
CLASSIFY EVIDENCE
  ↓
EXTRACT
  ↓
GRAPHIFY
  ↓
RETRIEVE
  ↓
CROSS-COMPARE
  ↓
BENCHMARK
  ↓
SYNTHESIZE
  ↓
VALIDATE
  ↓
DECIDE
  ↓
IMPLEMENT
  ↓
EVALUATE
  ↓
INSTITUTIONALIZE
```

---

## 2. Contrato Detalhado de Cada Etapa

| # | Etapa | Input | Output | Subsistema Responsável | Evento Emitido | Proveniência Requerida | Estado de Falha |
|---|:---|:---|:---|:---|:---|:---|:---|
| 1 | **DEFINE** | Intenção de pesquisa ou problema de negócio | Pergunta formulada (`ResearchQuestion`) & escopo | Research Coordinator | `RESEARCH_INITIATED` | ID do Operador, timestamp, contexto | `INVALID_SCOPE` (Aborta) |
| 2 | **SCOUT** | Escopo autorizado e alvos (repositórios, docs) | Fontes descobertas e listadas | `ScoutWorker` (`src/ingestion/scout.py`) | `SOURCE_DISCOVERED` | Repo, branch, commit SHA, file path | `UNAUTHORIZED_SCOPE` (Rejeita fonte) |
| 3 | **COLLECT** | Arquivos brutos das fontes autorizadas | Blobs imutáveis preservados em WORM/CAS | `SourceIngestorWorker` & `BlobVault` | `SOURCE_BLOB_VERIFIED`, `SOURCE_INGESTED` | SHA-256 byte digest, content hash, CAS URI | `CORRUPTED_BLOB` (Quarentena) |
| 4 | **CLASSIFY EVIDENCE**| Documentos capturados | Chunks determinísticos e tipos de fonte | `DocumentParserWorker` | `DOCUMENT_PARSED` | Offsets de linha, hash de chunk | `PARSE_ERROR` (Isola chunk) |
| 5 | **EXTRACT** | Chunks e ASTs de código | Entidades preliminares e menções de texto | `EntityExtractorWorker`, Tree-Sitter | `ENTITY_EXTRACTED` | `source_chunk_id`, linhas, confiança | `EXTRACTION_SKIPPED` |
| 6 | **GRAPHIFY** | Snapshot de código do repositório | Artefato estrutural `graph.json` | Graphify CLI Capability (Sandboxed) | `RELATION_EXTRACTED` via `GraphifyIngestor` | Extractor version (`graphify-v8`), node/link hashes | `GRAPH_BUILD_FAILED` |
| 7 | **RETRIEVE** | Consultas da investigação | Candidatos estruturais, densos e lexicais | `HybridSearchEngine` (3-Way RRF) | `KNOWLEDGE_RETRIEVED` (Audit log) | Query text, RRF weights, ranking scores | `ABSTAIN` (Sem resultados relevantes) |
| 8 | **CROSS-COMPARE** | Grafos de diferentes repositórios/projetos | Matriz de compatibilidade, divergências | `ResearchGraphIntelligence` | `CROSS_PROJECT_COMPARED` | Entidades comparadas, métricas topológicas | `NO_OVERLAP` |
| 9 | **BENCHMARK** | Padrões externos e estado interno | Relatório de gaps arquiteturais | Research Analyst / Benchmark Engine | `BENCHMARK_EVALUATED` | Fontes externas comparadas | `INCONCLUSIVE` |
| 10| **SYNTHESIZE** | Conjunto de evidências e métricas | `ResearchFinding` contextualizado | Community Summarizer & Intelligence | `RESEARCH_SYNTHESIZED` | Evidence IDs vinculados, parent events | `INSUFFICIENT_EVIDENCE` |
| 11| **VALIDATE** | Descobertas e hipóteses | Veredito de consistência e reprodutibilidade | Verifier Agent / QA Engine | `KNOWLEDGE_VALIDATED` | Método de verificação, test evidence | `VALIDATION_FAILED` (Marca `REJECTED`) |
| 12| **DECIDE** | Proposta de solução / ADR | Decisão ratificada | **CEO Sovereign** (`actor_role = 'CEO'`) | `DECISION_RATIFIED` | Assinatura do CEO, justificativa | `DECISION_REJECTED` |
| 13| **IMPLEMENT** | Diretriz aprovada e ADR | Código e artefatos versionados | PDL Governed Execution | `TASK_EXPERIENCE_RECORDED` | Commit SHA, task identity, test proofs | `BUILD_FAILED` / `TEST_FAILED` |
| 14| **EVALUATE** | Runtime pós-implantação | Evidência empírica de funcionamento | Observation Sync / Runtime Monitor | `RUNTIME_EVALUATED` | Métricas de telemetria, logs de erro | `REGRESSION_DETECTED` |
| 15| **INSTITUTIONALIZE**| Solução validada em produção | Conhecimento promovido e consolidado | Reducer Engine & Governance | `KNOWLEDGE_ADOPTED` / `MASTER_CONTEXT_UPDATED` | Causal DAG completo, linhagem temporal | `PROMOTION_BLOCKED` |

---

## 3. Papel do Graphify dentro do Ciclo

Graphify entra estritamente na transição entre **CLASSIFY EVIDENCE / EXTRACT** e **RETRIEVE**:

```text
               +-----------------------------+
               | 4. CLASSIFY EVIDENCE        |
               +--------------+--------------+
                              |
                              v
               +-----------------------------+
               | 5. EXTRACT & 6. GRAPHIFY    |
               | (Ast Extraction, Calls,     |
               |  Communities, graph.json)   |
               +--------------+--------------+
                              |
                              v [RELATION_EXTRACTED]
               +-----------------------------+
               | CANONICAL NEURAL GRAPH      |
               | (neural_nodes, neural_edges)|
               +--------------+--------------+
                              |
                              v
               +-----------------------------+
               | 7. HYBRID RETRIEVAL (3-WAY) |
               +-----------------------------+
```

### Regra de Ouro:
Graphify **nunca** é executado antes do **SCOUT** (pois as fontes precisam ser autorizadas previamente) e **nunca** é executado durante o **DECIDE** ou **INSTITUTIONALIZE** (pois não possui autoridade de julgamento institucional).
