# AUDITORIA TÉCNICA E DESIGN: BIDIRECTIONAL NEURAL KNOWLEDGE GATE

```text
STATUS: HISTORICAL AUDIT / DESIGN
IMPLEMENTATION STATUS: NOT IMPLEMENTED
DATA DE CONGELAMENTO: 2026-09-14
AUDITORES: Antigravity AI Assistant & PUB Core Engineering
REPOSITÓRIOS AUDITADOS:
  - pubcoreagencia/pub-dev-loop (c:/Users/Matheus Paes/Documents/ChatGPT/PUB DEV LOOP)
  - pubcoreagencia/pub-neural   (c:/Users/Matheus Paes/Documents/ChatGPT/PUB NEURAL)
CLASSIFICAÇÃO DO ESTADO:
  - IMPLEMENTED: Event sourcing, Projector Engine, Hybrid Retrieval V0.1, RLS, PDL Write Bridge
  - VALIDATED: Baseline V0.1 Foundation Freeze (pgvector, FTS português, RRF, Abstention)
  - NOT IMPLEMENTED: PDL Query to Neural, Neural HTTP Server, Bidirectional Gate Runtime
  - PROPOSED: Bidirectional Neural Knowledge Gate, Query & Experience Contracts, Phases A-F
```

---

## 1. PDL AUDIT

### 1.1 Como o PDL atualmente escreve no Neural?
Através do `DefaultPubNeuralBridge` (`src/pdl/neural/neural-bridge.ts`), que invoca o método `submit()` de uma implementação de `PubNeuralClient` (em produção/runtime, `HttpPubNeuralClient`). Internamente no processo do PDL, ele também invoca `LearningFeedbackEngine.processFeedback(...)` para alimentar a memória local do *The Office* (`src/office/learning-feedback.ts`), mas a persistência externa para o PUB Neural ocorre exclusivamente via requisição HTTP POST.

### 1.2 Onde isso acontece?
1. **`BaseWorker.execute`** (`src/worker-service.ts:708-723`): Chamado após a finalização da tarefa, verificação do worktree e confirmação de `finalizeResult.status === 'COMPLETED'` com `gateDecision.passed = true`.
2. **`CorrectionWorker.execute`** (`src/pdl/worker/correction-worker.ts:494-510`): Executado após a validação do Persistence Gate, repassando o status da ingestão para o `conversationStore` do CEO.
3. **`ChiefOfStaffAgent.handleCommand`** (`src/office/chief-of-staff-agent.ts:494-515`): Invocado no encerramento síncrono de comandos de engenharia do CEO.

### 1.3 Qual payload é enviado?
Objeto estrito `NeuralTaskStatePayload` (`src/pdl/neural/types.ts:20-35`) construído por `buildPayload()`:
```typescript
{
  taskId: string;
  projectId: string;
  repository: string;
  branch: string;
  commitSha: string | null;
  remoteSha: string | null;
  status: TaskStatus;
  objective: string;
  agentId?: string | null;
  changedFiles: string[];
  evidence: {
    validationPassed: boolean;
    worktreeClean: boolean;
    pushSucceeded: boolean;
    remoteVerified: boolean;
    runtimeVerified?: boolean;
  };
  trace?: Record<string, unknown>;
  completedAt: string;
  ingestionSource: 'pdl-persistence-gate';
}
```

### 1.4 Existe algum mecanismo de QUERY?
**NÃO.** O PDL não possui nenhum método de query, busca ou recuperação voltado para o PUB Neural. Os arquivos `src/pdl/neural/neural-bridge.ts` e `src/pdl/neural/types.ts` possuem apenas o método `submit()`. O mecanismo de lições existente no PDL (`InstitutionalLessonRetrievalEngine` em `src/office/lesson-retrieval.ts`) consulta unicamente a tabela PostgreSQL local do PDL (`institutional_lessons`) ou o cache em memória in-process. O PDL em runtime é cego em relação ao conhecimento persistido no PUB Neural.

### 1.5 Existe autenticação?
**SIM.** O `HttpPubNeuralClient` lê a variável de ambiente `PUB_NEURAL_TOKEN` (ou options injetadas) e envia o cabeçalho `Authorization: Bearer ${this.token}`.

### 1.6 Existe endpoint/API?
O client lê a URL em `PUB_NEURAL_ENDPOINT`. Se a variável não estiver definida, o client opera em *fail-closed*, retornando `{ acknowledged: false, persisted: false, status: 'UNAVAILABLE', error: 'PUB Neural endpoint not configured (PUB_NEURAL_ENDPOINT missing)' }`.

### 1.7 Existe timeout/retry?
- **Timeout:** SIM, padrão de 5000ms (`timeoutMs: 5000`) gerenciado via `AbortController` (`signal: controller.signal`).
- **Retry:** **NÃO.** Qualquer erro de rede, timeout ou HTTP $\ge 400$ encerra imediatamente a chamada com `status: 'FAILED'` sem novas tentativas.

### 1.8 Existe escopo por projeto?
No payload de saída constam `projectId` (`task.project`) e `repository` (`task.repository`). Não há escopo de consulta porque não há consulta.

### 1.9 Existe provenance?
O payload enviado pelo PDL registra `taskId`, `projectId`, `repository`, `branch`, `commitSha`, `remoteSha`, `completedAt` e `ingestionSource: 'pdl-persistence-gate'`.

### 1.10 Existe confidence?
A confiança não é expressa numericamente, mas sim como um conjunto de evidências booleanas auditadas: `validationPassed`, `worktreeClean`, `pushSucceeded`, `remoteVerified`, `runtimeVerified`.

### 1.11 Existe status/promotion?
O contrato aceita como resposta `status: 'ACKNOWLEDGED' | 'PERSISTED'`, mas não existe ciclo de promoção bidirecional (`CANDIDATE -> VALIDATED -> INSTITUTIONAL`) operando entre o PDL e o Neural.

### 1.12 O resultado é persistido no task?
- Em `src/worker-service.ts:709-723`: **NÃO.** O retorno da promessa não é salvo no objeto `Task`, nem na tabela `tasks` do banco nem no `trace`. É emitido apenas log/warn no console.
- Em `src/pdl/worker/correction-worker.ts:511-525`: O `neuralStatus` é repassado apenas para `conversationStore.recordTaskCompletion(...)` (memória de conversa do CEO), mas não na tabela `tasks`.

---

## 2. PUB NEURAL AUDIT

### 2.1 Qual é a forma CANÔNICA de consultar Neural hoje?
A forma canônica em código é:
1. **Em Python (in-process):** Invocação direta da classe `HybridSearchEngine.search(query, bearer_token, trust_zone, project_id, model_id)` em `src/retrieval/hybrid_search.py`.
2. **Em SQL:** Consultas SQL diretas às tabelas e projeções sob RLS no schema `pub_neural`:
   - `pub_neural.neural_fts` (Full-Text Search com ranking `ts_rank` e dicionário `'portuguese'`).
   - `pub_neural.neural_vectors` (Busca vetorial densa via operador de cosseno `<=>` com índice HNSW).
   - `pub_neural.neural_nodes`, `pub_neural.neural_evidence`, `pub_neural.neural_sources`.

### 2.2 Existe API?
Existe a **API de biblioteca Python interna** (`HybridSearchEngine`, `PubNeuralClient`, `VectorIndexingWorker`). **NÃO existe uma API de rede HTTP (REST/OpenAPI/FastAPI) em execução no repositório.**

### 2.3 Existe RPC?
No nível de banco de dados PostgreSQL existem Stored Procedures PL/pgSQL canônicas (`SECURITY DEFINER`) que operam como RPCs transacionais:
- `pub_neural.establish_session_context(actor_id, secret, trust_zone, project_id) -> bearer_token`
- `pub_neural.attach_session(bearer_token) -> boolean`
- `pub_neural.append_event(event_id, event_type, stream_id, stream_version, ...) -> global_sequence`
- `pub_neural.run_projector(projector_name, from_seq, to_seq) -> table`
- `pub_neural.register_verified_blob(...)`
Não há RPC de rede (gRPC ou tRPC).

### 2.4 Existe SQL direto?
**SIM.** A arquitetura do PUB Neural é fundamentalmente baseada em PostgreSQL 16+ com extensões `pgvector` e `pgcrypto`. O papel de aplicação `pub_neural_app` consulta projeções com RLS forçado (`FORCE ROW LEVEL SECURITY`), enquanto inserções canônicas são restritas à procedure `pub_neural.append_event`.

### 2.5 Existe endpoint HTTP?
**NÃO.** O repositório `pub-neural` não possui nenhum framework web configurado (nem FastAPI, nem Express, nem Flask, nem Hono).

### 2.6 Existe MCP?
**NÃO.** Não há servidor MCP configurado no repositório `pub-neural`.

### 2.7 Existe semantic retrieval?
**SIM.** Implementado em `src/retrieval/hybrid_search.py:217-268`, utilizando `pub_neural.neural_vectors`, operador `<=>::vector(1536)` e verificação de integridade de hash para descarte de vetores obsoletos.

### 2.8 Existe hybrid retrieval?
**SIM.** O `HybridSearchEngine` (`src/retrieval/hybrid_search.py:28-66`) implementa Hybrid Retrieval V0.1 combinando FTS (lexical) + pgvector (denso) via **Reciprocal Rank Fusion (RRF)** com $k=60$ e desempate determinístico `(rrf_score DESC, target_id ASC)`.

### 2.9 Existe filtro por project/repository?
**SIM.** As queries SQL de FTS e vetoriais filtram explicitamente:
- `fts.trust_zone = %s` / `v.trust_zone = %s`
- `(fts.project_id = %s OR fts.project_id IS NULL)` (permitindo itens do projeto ou itens globais sem projeto).
- Na tabela `pub_neural.neural_sources`, há rastreamento estrito por `repository`, `branch`, `commit_sha` e `file_path`.

### 2.10 Existe provenance?
**SIM.** Toda entidade em `pub_neural.neural_nodes` possui `originating_event_id`. Toda evidência em `pub_neural.neural_evidence` possui `source_id`, `exact_quote`, `start_line`, `end_line`, `content_hash`. O `source_id` aponta para `pub_neural.neural_sources`, que preserva `repository`, `commit_sha`, `file_path`, `file_sha256`, `storage_uri` e `observed_at`.

### 2.11 Existe confidence?
**SIM.**
- `neural_nodes.confidence_score` (FLOAT, padrão 1.0)
- `neural_evidence.confidence` (FLOAT, padrão 1.0)
- `HybridSearchResult.rrf_score` (FLOAT computado)
- `RetrievalAbstentionPolicy` (`src/retrieval/abstention.py`): descarta resultados se a relevância for insuficiente para evitar alucinação.

### 2.12 Existe promotion state?
**SIM.** Enum PostgreSQL nativo `pub_neural.neural_promotion_state`:
`CAPTURED`, `OBSERVED`, `EXTRACTED`, `CANDIDATE`, `VALIDATED`, `ADOPTED`, `INSTITUTIONAL_CANDIDATE`, `INSTITUTIONAL`.

### 2.13 Existe contradiction handling?
**SIM.** Enum nativo `pub_neural.neural_conflict_state`:
`RESOLVED`, `CONTRADICTORY`, `BLOCKED`, `SUPERSEDED`, `DEPRECATED`, `REJECTED`. O motor de projeção (`src/projector_engine.sql:221-260`) suporta os eventos `KNOWLEDGE_SUPERSEDED` e `KNOWLEDGE_REJECTED`.

### 2.14 Existe resposta estruturada para agentes?
Em Python, o retorno é a dataclass `HybridSearchResult` (`src/retrieval/hybrid_search.py:12-26`). No entanto, essa resposta é in-process em Python e não está serializada como endpoint de rede para o PDL em Node.js.

---

## 3. CURRENT REALITY: MAPEAMENTO E DIVERGÊNCIAS

### Mapeamento Factual
- **PDL $\to$ atualmente envia:** Requisições HTTP POST contendo `NeuralTaskStatePayload` para a URL configurada em `PUB_NEURAL_ENDPOINT`.
- **PDL $\to$ atualmente recebe:** `{ acknowledged: false, persisted: false, status: 'UNAVAILABLE' }` em ambientes reais sem endpoint configurado, ou respostas simuladas em testes com `globalThis.fetch` mockado. Não recebe nenhum dado de consulta.
- **NEURAL $\to$ atualmente aceita:** Eventos canônicos via `pub_neural.append_event` com sessão bearer ativa em PostgreSQL. Arquivos locais para ingestão via pipeline `scout.py`.
- **NEURAL $\to$ atualmente retorna:** Linhas SQL ou instâncias Python de `HybridSearchResult` para callers in-process locais. Retorna ZERO bytes pela rede para o PDL.

---

## 4. DIVERGÊNCIAS DOCUMENTADAS

| Dimensão | Documentado em `MASTER_CONTEXT.md` | Implementado em Testes | Realidade em Runtime / Código | Status |
|---|---|---|---|---|
| **PDL Consulta Neural** | "PDL consulta PUB Neural antes de agir (Seção 9)" | Não testado | **Inexistente.** Não há client ou chamada de query no PDL. | **DIVERGÊNCIA CRÍTICA** |
| **PDL Ingestão no Neural** | "PDL consome conhecimento e produz novas experiências para o Neural" | `neural-bridge-real-ingestion.test.ts` simula sucesso mockando `globalThis.fetch` | `HttpPubNeuralClient` falha com `UNAVAILABLE` se não houver endpoint HTTP rodando. | **DIVERGÊNCIA CRÍTICA** |
| **Endpoint HTTP no Neural** | Implícito como destino de rede para serviços | N/A | **Inexistente.** O repositório `pub-neural` é uma biblioteca Python e DDL/SQL PostgreSQL. | **DIVERGÊNCIA CRÍTICA** |
| **Repositórios Autorizados** | `pub-dev-loop` é cidadão de primeira classe | Ingestão testada com mocks | `src/ingestion/scout.py:8-12` autoriza apenas `pub-ecom`, `pub-neural` e `holding-governance`. `pub-dev-loop` é rejeitado (`UNAUTHORIZED_SOURCE_SCOPE`). | **DIVERGÊNCIA CRÍTICA** |
| **Hierarquia da Verdade** | `RUNTIME > TESTS > DOCS` | Aplicado em testes unitários | Válido no PDL (`ContextAuthority`: CURRENT > GOVERNED > HISTORICAL). | **CONFORME** |

---

## 5. RETRIEVAL AUDIT

O Hybrid Retrieval V0.1 em `src/retrieval/hybrid_search.py` foi totalmente auditado:
- **Lexical Retrieval:** Utiliza PostgreSQL Full-Text Search com `tsv_document @@ plainto_tsquery('portuguese', %s)` e função de ranking `ts_rank` com pesos diferenciados (Title: 1.0, Summary: 0.4, Content: 0.2).
- **Dense Retrieval:** Utiliza `pgvector` com distância de cosseno `<=>` sobre embeddings de 1536 dimensões indexados via HNSW (`m=16, ef_construction=64`).
- **Reciprocal Rank Fusion (RRF):**
  $$RRF(d) = \sum_{i \in \{lexical, dense\}} \frac{1}{60 + rank_i(d)}$$
  Com critério de desempate determinístico: `(rrf_score DESC, target_id ASC)`.
- **Filtros Nativos:** Filtra estritamente por `trust_zone` e `project_id` (com fallback para nós globais onde `project_id IS NULL`).
- **Verificação de Staleness:** Vetores cujo `content_hash` divirja do texto atual em `neural_nodes` são sumariamente descartados da busca densa.
- **Abstention Gate:** O `RetrievalAbstentionPolicy` (`src/retrieval/abstention.py`) calibra a rejeição de queries fora de domínio para evitar falsos positivos.

---

## 6. INGESTION AUDIT

- O pipeline de ingestão atual (`src/ingestion/`) é estruturado em:
  `SOURCE_DISCOVERED -> SOURCE_BLOB_VERIFIED -> SOURCE_INGESTED -> DOCUMENT_CAPTURED -> DOCUMENT_PARSED -> ENTITY_EXTRACTED -> EVIDENCE_CAPTURED`.
- O `ScoutWorker` (`src/ingestion/scout.py`) é o gateway de entrada de arquivos, mas restringe o escopo a `pubcore/pub-ecom`, `pubcore/pub-neural` e `pubcore/holding-governance`.
- O payload de tarefa emitido pelo PDL (`NeuralTaskStatePayload`) não possui um worker ou evento correspondente no pipeline de ingestão do Neural.

---

## 7. PROVENANCE

Todo item em `pub-neural` possui cadeia de custódia rastreável:
- `neural_nodes.originating_event_id`
- `neural_evidence.source_id`, `exact_quote`, `start_line`, `end_line`, `content_hash`
- `neural_sources.repository`, `branch`, `commit_sha`, `file_path`, `file_sha256`, `storage_uri`
- **Regra auditada:** Conhecimento sem proveniência rastreável deve ser rebaixado para autoridade mínima (`HISTORICAL`) ou descartado fail-closed no PDL.

---

## 8. VALIDITY / FRESHNESS

- O conhecimento no Neural nunca substitui a verdade física atual do repositório/runtime.
- Hierarquia não negociável:
  $$\text{CURRENT RUNTIME / DIRECT EVIDENCE} > \text{REAL EXECUTION} > \text{TESTS} > \text{VALIDATED KNOWLEDGE} > \text{HISTORICAL MEMORY}$$
- Itens cujos commits de proveniência divirjam da branch ativa no PDL devem ser sinalizados com `isStale: true`.

---

## 9. SECURITY

1. **Tokens Sanitizados:** `PUB_NEURAL_ENDPOINT` e `PUB_NEURAL_TOKEN` estão explicitamente protegidos no sanitizador de ambiente do PDL (`src/tools/security.ts:192-193`).
2. **Conhecimento Recuperado é DADO, Não Instrução:**
   Conhecimento vindo do Neural deve ser delimitado em blocos de dados inertes (`<neural_retrieved_data>`).
3. **Defesa contra Injeção de Prompt:**
   O `ContextAssemblyEngine` descarta afirmações de autoridade não verificadas (`UNTRUSTED_AUTHORITY_CLAIM`). Qualquer tentativa de jailbreak ou override de regras institucionais contida no conhecimento recuperado é neutralizada.
4. **Isolamento de Tenant:**
   Garantido via `trust_zone` (`tz_internal_holding` vs `tz_client_facing`) por RLS em PostgreSQL.

---

## 10. FAILURE MODEL

| Cenário | Comportamento do PDL | Registro em Evidência | Política |
|---|---|---|---|
| **OFFLINE** | Continua com contexto local | `neural_fallback: 'OFFLINE_CONTINUED'` | `CAN_CONTINUE_WITHOUT_NEURAL` |
| **TIMEOUT (>5s)** | Aborta e segue local | `neural_fallback: 'TIMEOUT_CONTINUED'` | `CAN_CONTINUE_WITHOUT_NEURAL` |
| **EMPTY** | Prossegue normalmente | `neural_status: 'EMPTY_RESULTS'` | `CAN_CONTINUE_WITHOUT_NEURAL` |
| **CONTRADICTORY** | Descarta conflitantes | `neural_fallback: 'CONTRADICTION_DROPPED'` | `CAN_CONTINUE_WITHOUT_NEURAL` |
| **STALE** | Rebaixa para baixa confiança | `neural_status: 'STALE_DEMOTED'` | `CAN_CONTINUE_WITHOUT_NEURAL` |
| **UNAUTHORIZED** | Falha se for governança | `neural_error: 'UNAUTHORIZED'` | **BLOCK** para tarefas governadas |

---

## 11. PROPOSED QUERY CONTRACT

```typescript
export interface NeuralKnowledgeQuery {
  project: string;
  repository: string;
  scope: 'GLOBAL' | 'PROJECT' | 'TASK';
  agentRole: 'chief-of-staff' | 'architect' | 'developer' | 'reviewer' | 'qa-engineer';
  query: string;
  taskContext?: {
    intent: string;
    objective: string;
    targetFiles?: string[];
  };
  limit?: number;
}
```

---

## 12. PROPOSED WRITE CONTRACT

```typescript
export interface NeuralExperiencePayload {
  taskId: string;
  projectId: string;
  repository: string;
  branch: string;
  commitSha: string;
  remoteSha: string;
  status: 'COMPLETED' | 'FAILED';
  objective: string;
  agentRole: string;
  changedFiles: string[];
  durationMs: number;
  evidence: {
    validationPassed: boolean;
    worktreeClean: boolean;
    pushSucceeded: boolean;
    remoteVerified: boolean;
    runtimeVerified?: boolean;
    testSummary?: { total: number; passed: number; failed: number };
  };
  candidateFindings?: Array<{
    type: 'LESSON' | 'PATTERN';
    title: string;
    statement: string;
    scope: 'PROJECT' | 'GLOBAL';
    confidence: number;
  }>;
  completedAt: string;
  ingestionSource: 'pdl-bidirectional-gate';
}
```

---

## 13. KNOWLEDGE CLASSES

- **Escopos:** `GLOBAL`, `PROJECT`, `AGENT`, `TASK`.
- **Classes:** `GOVERNANCE`, `DECISION`, `PATTERN`, `LESSON`, `SKILL`, `SEMANTIC`, `PROCEDURAL`, `EPISODIC`.
- **Isolamento:** Conhecimento institucional não pode ser misturado com conhecimento específico de projeto sem ratificação explícita do CEO/Governança.

---

## 14. PRE-TASK FLOW

1. CEO Task Intake $\to$ Identificação de projeto, repositório e papel do especialista.
2. Consulta ao Neural via `BidirectionalNeuralKnowledgeGate.retrievePreTaskContext(...)`.
3. Execução de Hybrid Retrieval (FTS + Dense + RRF + Abstention).
4. Verificação de proveniência e frescor contra o estado Git atual.
5. `ContextAssemblyEngine` aloca blocos governados com limite de caracteres e ordenação estrita de autoridade.
6. Despacho do prompt contextualizado para execução pelo Worker.

---

## 15. POST-TASK FLOW

1. Worker conclui alterações e testes automatizados.
2. Persistence Gate valida worktree clean, commit e push remoto.
3. Se `COMPLETED`, `BidirectionalNeuralKnowledgeGate.recordPostTaskExperience(...)` formata `RAW_EXPERIENCE` e `CANDIDATE_LESSON`.
4. Ingestão no Neural via evento canônico (`TASK_EXECUTION_RECORDED`).
5. Projector atualiza projeções.
6. A experiência é armazenada com status `CANDIDATE`. **NUNCA é promovida automaticamente para `INSTITUTIONAL`.**

---

## 16. PROPOSED GATE

Criação do componente conceitual `BidirectionalNeuralKnowledgeGate`:
- Desacopla `BaseWorker`, `CorrectionWorker` e `ChiefOfStaffAgent`.
- Centraliza chamadas pré e pós-execução.
- Garante tratamento uniforme de fallbacks, métricas e isolamento de falhas.

---

## 17. OBSERVABILITY

Rastreamento no trace da tarefa:
- `queryExecuted: boolean`
- `queryLatencyMs: number`
- `retrievalCount: number`
- `topRrfScore: number`
- `knowledgeNodeIdsUsed: string[]`
- `fallbackApplied: boolean`
- `fallbackReason?: string`
- `experienceEventId?: string`
- `experienceStatus: 'ACKNOWLEDGED' | 'PERSISTED' | 'FAILED' | 'UNAVAILABLE'`

---

## 18. TEST STRATEGY

17 cenários mandatórios a serem implementados em fase futura:
1. Neural available
2. Neural empty
3. Neural timeout
4. Neural unavailable
5. Malformed result
6. Stale knowledge
7. Contradictory knowledge
8. Project scope mismatch
9. Provenance missing
10. High-confidence validated knowledge
11. Low-confidence candidate knowledge
12. Query before task
13. Experience after task
14. No automatic institutional promotion
15. Current runtime overrides stale Neural knowledge
16. Prompt injection-like content in retrieved knowledge
17. Token never reaches LLM/sandbox

---

## 19. ARCHITECTURAL DECISION

- **Reutilização:** O motor de busca híbrida (`HybridSearchEngine`), o Projector Engine, o schema `pub_neural`, o `ContextAssemblyEngine` e o `PersistenceGate` estão maduros e serão 100% preservados.
- **Adaptação Mínima:** Em vez de inventar uma nova infraestrutura, criar uma interface de adapter de rede para o Neural (`/v1/query` e `/v1/experience`), estender o allowlist do `scout.py` para incluir `pubcore/pub-dev-loop`, e integrar o `BidirectionalNeuralKnowledgeGate` no PDL.

---

## 20. IMPLEMENTATION PLAN (FASES FUTURAS)

- **Phase A:** Contracts & Schemas
- **Phase B:** Neural Query Adapter
- **Phase C:** PDL Pre-Execution Context
- **Phase D:** Experience/Evidence Writeback
- **Phase E:** Validation / Tests
- **Phase F:** Controlled E2E

---

## 21. CRITICAL NON-GOALS

- NÃO implementar Web research.
- NÃO implementar YouTube/Instagram research.
- NÃO implementar backlog discovery autônomo.
- NÃO implementar enxame de agentes novos.
- NÃO sincronizar com Obsidian nesta fase.
- NÃO introduzir banco de grafos especializado (PostgreSQL 16 + pgvector é suficiente).
- NÃO substituir o Git como fonte de verdade factual.

---

## 22. REPOSITORY BOUNDARY

A fronteira é estrita e isolada:
- **PUB PROTOTYPE (PP):** Totalmente fora de escopo.
- **ESCOPO EXCLUSIVO:** Apenas `pubcoreagencia/pub-dev-loop` e `pubcoreagencia/pub-neural`.

---

## 23. FINAL VERDICT

```text
FINAL VERDICT: DESIGN_READY
IMPLEMENTATION STATUS: NOT IMPLEMENTED
GOVERNANCE CHECKPOINT: CONSOLIDATED
```
