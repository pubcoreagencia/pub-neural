# PUB NEURAL — RESEARCH RUNTIME ARCHITECTURE V0

**Status:** CANONICAL ARCHITECTURAL CONTRACT  
**Document ID:** `docs/research/RESEARCH_RUNTIME_V0.md`  
**Consolidation Date:** 2026-09-17  
**Context:** Brain of PUB Core Holding  

---

## 1. Executive Summary & Foundational Contract

PUB Neural operates as the cognitive layer, institutional memory, and knowledge orchestrator of the PUB Core Holding.

The fundamental contract of Research in PUB Neural is:

```text
RESEARCH INTENT
      ↓
RESEARCH PLAN
      ↓
SCOUT / COLLECTION
      ↓
SOURCE EVIDENCE
      ↓
GRAPH EXTRACTION
      ↓
GRAPHIFY
      ↓
CANONICAL NEURAL GRAPH
      ↓
HYBRID RETRIEVAL (3-WAY RRF)
      ↓
CROSS-COMPARISON
      ↓
HYPOTHESIS / FINDINGS
      ↓
VALIDATION
      ↓
KNOWLEDGE PROMOTION
      ↓
INSTITUTIONAL MEMORY
```

> [!IMPORTANT]
> **Fundamental Epistemic Invariants:**
> 1. **Research is NOT Extraction:** Research determines *what needs to be discovered*; Extraction captures *what exists in a specific source*.
> 2. **Retrieval is NOT Evidence:** Retrieval discovers *candidates* for evaluation; Evidence requires source provenance, timestamp, snapshot, extractor identity, confidence, and epistemic classification.
> 3. **Graphify is a Structural Extractor Capability:** Graphify parses ASTs, discovers relationships, and computes topological clusters. It **never** decides institutional truth, promotes knowledge, or mutates ontology.
> 4. **No Automated Self-Promotion:** Knowledge never jumps autonomously from candidate findings to institutional canon. The human sovereign (Matheus / CEO) and governed consensus remain authoritative.

---

## 2. Separation of Cognitive Operations

The Research Runtime strictly delineates six cognitive operations to prevent epistemic conflation:

```text
┌─────────────────┬─────────────────────────────────────────────────┬──────────────────────────────────────────┐
│ Operation       │ Core Epistemic Question                         │ Subsystem / Capability                   │
├─────────────────┼─────────────────────────────────────────────────┼──────────────────────────────────────────┤
│ 1. Research     │ "O que precisamos descobrir?"                   │ Research Orchestrator / Intent Service   │
│ 2. Extraction   │ "O que existe nesta fonte?"                     │ Extractor Workers / Graphify Capability  │
│ 3. Retrieval    │ "O que já sabemos que é relevante?"             │ HybridSearchEngine (3-Way RRF Fusion)   │
│ 4. Synthesis    │ "O que as evidências combinadas indicam?"       │ Research Intelligence / Synthesis Engine │
│ 5. Validation   │ "Podemos confiar nessa conclusão?"              │ Verification Agent / Evidence Validator  │
│ 6. Promotion    │ "Isso merece virar conhecimento institucional?" │ Governance Reducer / CEO Sovereign Gate  │
└─────────────────┴─────────────────────────────────────────────────┴──────────────────────────────────────────┘
```

---

## 3. Audit of Research Primitives & Artifacts

Audit of existing canonical entities, tables, events, and models in the PUB Neural codebase:

| Artifact | Existe? | Onde? | Estado Atual | Papel Canônico no Runtime V0 |
| :--- | :--- | :--- | :--- | :--- |
| **Research** | Parcial | `src/gate/enums.py` (`AgentRole.RESEARCHER`), `src/research/graph_intelligence.py` | Não modelado como entidade de primeira classe na DB | Container raiz de uma investigação ativa com objetivo delimitado. |
| **ResearchQuestion**| Não | Inexistente na DB | Inexistente (Lacuna) | Questão formal que orienta o plano de investigação. |
| **ResearchTask** | Parcial | PDL Task Loop (`PreTaskKnowledgeGate`, `PostTaskExperienceGate`) | Operacional para tarefas de engenharia, não especializada para research | Tarefa operacional delimitada de coleta, extração ou análise. |
| **ResearchSource** | Sim | `pub_neural.source_blobs`, `neural_sources`, `scout.py` | `LIVE` na DB e Ingestion | Repositório, commit SHA, arquivo e URI imutável preservado em CAS. |
| **ResearchEvidence**| Sim | `pub_neural.neural_evidence`, `evidence_capturer.py` | `LIVE` na DB e Projeções | Citação exata vinculada a nós/arestas com `confidence` e `validation_state`. |
| **ResearchHypothesis**| Parcial | `neural_nodes` (`entity_type = 'CONCEPT'`), status `PROPOSED` | Representável genericamente, sem semântica específica de hipótese | Afirmação candidata sujeita a teste empírico ou estrutural. |
| **ResearchFinding** | Parcial | `TASK_EXPERIENCE_RECORDED` (`findings`), `graph_intelligence.py` | Presente no writeback de tarefas e análise topológica | Descoberta grounded em evidências estruturais ou semânticas. |
| **ResearchContradiction**| Parcial | `neural_conflict_state` (`CONTRADICTORY`), `neural_relation_type` (`CONTRADICTS`) | Primitivas presentes no schema PostgreSQL | Relação de oposição formal entre duas evidências ou hipóteses. |
| **ResearchBenchmark** | Não | `docs/OPEN_SOURCE_ARCHITECTURE_BENCHMARK.md` | Apenas documentação de benchmark | Medição quantitativa/qualitativa de desempenho ou arquitetura. |
| **ResearchSynthesis** | Parcial | `neural_community_reports` (Graph summarization) | Implementado no schema para resumos hierárquicos | Agregação contextual de múltiplos findings e evidências. |
| **ResearchDecision** | Sim | `neural_entity_type.DECISION`, `DECISION_PROPOSED`, `DECISION_RATIFIED` | `LIVE` (governança soberana CEO) | Resolução de trade-off arquitetural com status ratificado pelo CEO. |

---

## 4. Contradiction as First-Class Cognitive Data

No PUB Neural, contradições entre evidências **NÃO são erros de ingestão**. Elas representam divergências reais entre implementações, documentações desatualizadas ou conflitos de design:

```text
Evidence A (Source: repo-backend @ sha1) ──supports──► Hypothesis X (SSR Token Required)
                                                              ▲
Evidence B (Source: repo-frontend @ sha2) ──contradicts───────┘
```

### Regras de Governança de Contradição:
1. **Preservação Mútua:** Nenhuma evidência conflitante pode ser descartada ou silenciosamente apagada.
2. **Registro Relacional:** A relação `CONTRADICTS` é registrada em `neural_edges` conectando as duas evidências ou a evidência à hipótese.
3. **Estado de Conflito:** O nó associado recebe `conflict_state = 'CONTRADICTORY'`.
4. **Escalação:** Conflitos que afetam decisões arquiteturais requerem auditoria e resolução humana soberana (`CEO`), emitindo `KNOWLEDGE_SUPERSEDED` ou `KNOWLEDGE_REJECTED`.

---

## 5. Temporality & Bi-Temporal Integrity

A pesquisa no PUB Neural é estritamente situada no tempo. Deve ser possível reconstruir:
$$\text{Research}(T) = f(\text{KnowledgeAt}(T), \text{SourcesAt}(T), \text{SnapshotsAt}(T))$$

O schema V0 do PUB Neural garante essa capacidade através de:
- **`recorded_from` / `recorded_until` (System Time):** Quando a afirmação foi registrada no cérebro.
- **`valid_from` / `valid_until` (Valid Time):** Quando o fato era verídico no repositório/mundo real.
- **Snapshot Identity:** Todo artefato vincula-se ao Commit SHA exato e ao hash criptográfico do blob (`file_sha256`).

---

## 6. Hybrid Retrieval na Pesquisa

Ao conduzir uma investigação, o Research Runtime não depende de um único método de busca. Ele combina três sinais complementares:

```text
                           RESEARCH QUERY
                                 │
           ┌─────────────────────┼─────────────────────┐
           ▼                     ▼                     ▼
     LEXICAL SEARCH        DENSE EMBEDDINGS      GRAPH TOPOLOGY
      (PostgreSQL FTS)      (pgvector Cosine)     (CTE Traversal)
           │                     │                     │
           └─────────────────────┼─────────────────────┘
                                 ▼
                    RECIPROCAL RANK FUSION (RRF)
                      k=60, w_lex=1.0, w_dense=1.0, w_graph=0.8
                                 │
                                 ▼
                     RETRIEVAL ABSTENTION GATE
                                 │
                                 ▼
                     CANDIDATE KNOWLEDGE SET
                                 │
                                 ▼
                      GROUNDED EVIDENCE VERIFICATION
```

- **FTS (Lexical):** Encontra identificadores exatos, nomes de classes, rotas e constantes.
- **pgvector (Dense):** Captura proximidade conceitual e similaridade semântica de alto nível.
- **Graph (Topological):** Descobre dependências transitivas, comunidades Louvain e pontes arquiteturais.
- **Evidence Binding:** Candidatos ranqueados são cruzados com `neural_evidence` para extrair citações com números de linha exatos.
