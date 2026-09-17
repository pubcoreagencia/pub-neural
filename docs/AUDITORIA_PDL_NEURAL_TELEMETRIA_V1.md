# AUDITORIA DE TELEMETRIA PDL → PUB NEURAL V1
### Diagnóstico Empírico da Infraestrutura de Telemetria, Observabilidade e Integração

**Status:** AUDITORIA EMPÍRICA CONCLUÍDA  
**Documento:** `docs/AUDITORIA_PDL_NEURAL_TELEMETRIA_V1.md`  
**Data:** 17 de Setembro de 2026  
**Repositório:** `pubcoreagencia/pub-neural`  
**Branch:** `feat/retrieval-abstention-v0.3`  
**Baseline Commit:** `b5a5cdd5a78bb8ef9de01d3eed34f2d3c6238edc`  

---

## 1. RESUMO EXECUTIVO

Esta auditoria investigou minuciosamente e empiricamente o código-fonte, esquemas de banco de dados, serviços de agregação e mecanismos de ingestão do ecossistema PUB Neural para responder com exatidão à pergunta central:

> **Quanto do fluxo operacional: `PDL → execução real → eventos/resultados → PUB Neural → observação operacional → comparação com prioridade declarada` já existe de fato?**

### Conclusões Principais

1. **A camada de modelos e ingestão de experiência (`NeuralExperienceService`) está completamente implementada e testada no core Python**, com validação estrita de contratos, derivação determinística de idempotência (UUIDv5) e garantia de que `CandidateFindings` nunca sejam auto-promovidas (`promotionState = CANDIDATE`).
2. **A observação física de repositórios (`RepositoryObservationSync`) está em plena operação em produção**, sincronizando commits, PRs e metadados dos 55 repositórios do GitHub com cursores persistentes (`observation_sync_runs`), alimentando `neural_repository_observations` e publicando o evento canônico `REPOSITORY_OBSERVED` no log de eventos.
3. **A agregação de atividade operacional (`activity_service.py`) já calcula o estado real por projeto**, combinando observações físicas do GitHub com eventos de experiência (`TASK_EXPERIENCE_RECORDED`), categorizando os projetos em: `ATIVIDADE_HOJE`, `ATIVIDADE_RECENTE`, `SEM_ATIVIDADE_NO_PERIODO` e `DADOS_INSUFICIENTES`.
4. **A autoridade de projetos (`pub_neural.holding_projects`) e mapeamento (`pub_neural.project_repositories`) está consolidada em produção**, com 34 projetos canônicos e 55 repositórios associados. Projetos sem repositório (como `proj:incubacao-labs`) são preservados como entidades de primeiro nível.
5. **O backend HTTP Console (`server.py`) é intencionalmente *read-only***. O writeback de telemetria do PDL ocorre via *in-process service* ou stdio/file bridge (`bridge_runner.py`), sem expor endpoints REST públicos de escrita irrestrita, o que protege a integridade do barramento.
6. **Prioridade declarada (`strategic_priority`) é estritamente inviolável**: ela é armazenada como atributo soberano de governança (`PADRAO`, `ALTA`, `CRITICA`, `BAIXA`) e **nenhuma rotina no código atual modifica ou recalcula prioridade com base em volume de atividade**.

---

## 2. RESPOSTAS DETALHADAS ÀS 20 PERGUNTAS CANÔNICAS

### 1. Como o PDL produz evidência de execução?
O PDL produz evidência através da estrutura `NeuralExperienceRecord` contendo o sub-objeto `TaskEvidence` (definido em `src/gate/models.py`). As evidências atestadas incluem:
- `validation_passed: bool` — gates de lint, build e tipagem.
- `worktree_clean: bool` — ausência de arquivos desnecessários ou sujos.
- `push_succeeded: bool` — push concluído no branch de trabalho.
- `remote_verified: bool` — verificação de SHA remoto correspondente.
- `runtime_verified: bool` — verificação de execução em runtime real.
- `test_summary: Dict[str, Any]` — sumário estruturado de testes (`total`, `passed`, `failed`).
- `delivery_verified: bool` — confirmação de entrega do artefato.
- `governance_verified: bool` — conformidade com regras organizacionais.

### 2. Como chega ao PUB Neural?
Chega através do serviço `NeuralExperienceService.record(experience)` (`src/gate/experience_service.py`), suportado pela interface `ExperienceSink` (`InMemoryExperienceSink`, `FileBackedExperienceSink` ou barramento SQL direto). Para integrações externas em subprocesso, o PDL se comunica via `src/gate/bridge_runner.py` consumindo payloads JSON por `stdin` ou lendo arquivos do diretório `.neural/experience/`. O servidor HTTP de console (`console/backend/server.py`) não possui endpoint REST de POST aberto para gravação genérica.

### 3. Quais eventos já são persistidos?
Dois tipos de eventos principais são persistidos na tabela `pub_neural.neural_events`:
1. `TASK_EXPERIENCE_RECORDED`: gerado ao registrar uma execução de tarefa do PDL (stream `stream:task:{taskId}`).
2. `REPOSITORY_OBSERVED`: gerado pelo sincronizador contínuo do GitHub (`observation_sync.py`) com stream `repo_obs:{repo_name}`.
Adicionalmente, o reducer SQL (`migrations/0002_projector_engine_v0.sql`) projeta esses eventos em nós de grafo (`EVENT`, `LESSON`, `PATTERN`) na tabela `pub_neural.neural_nodes`.

### 4. Quais eventos são conceituais?
Eventos granulares específicos como `TEST_EXECUTION_COMPLETED`, `DEPLOY_PERFORMED`, `BLOCKER_DETECTED` e `BUILD_FAILED` existem atualmente apenas de forma **conceitual** ou como campos estruturados dentro do JSON `details` de `TaskEvidence` e `neural_repository_observations`. Eles não possuem `event_type` isolado e próprio no log de eventos `pub_neural.neural_events`.

### 5. O que `NeuralExperienceService` realmente recebe?
Recebe um objeto validado `NeuralExperienceRecord` contendo:
- `task_id: str`
- `project_id: str`
- `repository: str`
- `branch: str`
- `status: TaskExecutionStatus` (`SUCCESS`, `FAILED`, `ABORTED`, `BLOCKED`)
- `objective: str`
- `evidence: TaskEvidence`
- `completed_at: datetime`
- `commit_sha: Optional[str]`
- `remote_sha: Optional[str]`
- `agent_id: Optional[str]`
- `changed_files: List[str]`
- `candidate_findings: List[CandidateFinding]`
- `consumed_knowledge_ids: List[str]`
- `trace: Dict[str, Any]`
- `ingestion_source: str`
- `execution_id: Optional[str]`
- `correlation_id: Optional[str]`

### 6. Como `TASK_EXPERIENCE_RECORDED` é produzido?
É produzido em `NeuralExperienceService._create_event()`:
- `event_id`: gerado deterministicamente via `uuid.uuid5(uuid.NAMESPACE_DNS, f"exp:{idempotency_key}:{completed_at.isoformat()}")`.
- `stream_id`: `f"stream:task:{record.task_id}"`.
- `event_type`: `"TASK_EXPERIENCE_RECORDED"`.
- `payload`: dicionário contendo metadados completos da tarefa, hashes de commit, status, flags de validação e lista de `candidate_findings` com `candidateState: "CANDIDATE"`.

### 7. Como `observation_sync_runs` funciona?
A classe `RepositoryObservationSync` (`src/ingestion/observation_sync.py`) itera sobre repositórios cadastrados na tabela `pub_neural.project_registry`. A cada ciclo:
1. Registra o início do run em `pub_neural.observation_sync_runs`.
2. Executa a extração via `GitHubSignalExtractor` utilizando a CLI `gh api`.
3. Detecta commits novos, PRs atualizados e mudanças de branch posteriores ao cursor do último run (`last_commit_sha`, `last_pr_updated_at`).
4. Grava cada sinal em `pub_neural.neural_repository_observations`.
5. Emite `REPOSITORY_OBSERVED` em `pub_neural.neural_events`.
6. Atualiza o status do run com contadores de sucesso/erro e timestamp de encerramento.

### 8. Como `activity_service.py` calcula atividade?
`console/backend/services/activity_service.py` executa queries agregadas sobre `pub_neural.neural_repository_observations` e `pub_neural.neural_events`:
- Janela de hoje: `observed_at >= CURRENT_DATE` (UTC).
- Janela de 7 dias: `observed_at >= CURRENT_TIMESTAMP - INTERVAL '7 days'`.
- Realiza deduplicação por `(repository, event_type, external_id)`.
- Agrega por projeto mapeado via `pub_neural.project_repositories`.

### 9. Como `overview_service.py` calcula estado operacional?
A rotina correspondente reside em `get_overview_data()` dentro de `console/backend/services/activity_service.py`. O estado operacional de um projeto é determinado pelas seguintes regras determinísticas:
```sql
CASE 
    WHEN act.act_today > 0 THEN 'ATIVIDADE_HOJE'
    WHEN act.act_7d > 0 OR latest_obs.latest_observed_at >= CURRENT_TIMESTAMP - INTERVAL '7 days' THEN 'ATIVIDADE_RECENTE'
    WHEN act.obs_count > 0 THEN 'SEM_ATIVIDADE_NO_PERIODO'
    ELSE 'DADOS_INSUFICIENTES'
END
```

### 10. Como atividade é vinculada a `project_id`?
Para sinais de repositório (Git), o vínculo ocorre por junção canônica:
`pub_neural.project_registry reg LEFT JOIN pub_neural.project_repositories pr ON reg.id = pr.repository_id`.
Para registros de experiência (`TASK_EXPERIENCE_RECORDED`), o campo `project_id` é fornecido no próprio payload emitido pelo PDL. Caso um repositório não possua mapeamento em `project_repositories`, o sinal é computado como não-atribuído ou cai em fallback controlado.

### 11. Como múltiplos repositórios de um mesmo projeto são agregados?
A agregação SQL em `activity_service.py` agrupa por `hp.id` (`project_id`). As contagens de observações (`observation_count`, `act_today`, `act_7d`) de todos os repositórios vinculados através de `project_repositories` são somadas (`SUM`), e o número de repositórios distintos que registraram atividade é contado (`COUNT(DISTINCT pr.repository_id) AS observed_repos`).

### 12. Como projetos sem atividade são representados?
Projetos sem sinais nas janelas monitoradas recebem:
- `act_today = 0`, `act_7d = 0`.
- Se possuírem registros históricos mais antigos que 7 dias: estado `SEM_ATIVIDADE_NO_PERIODO`.
- Se possuírem zero registros históricos em toda a base: estado `DADOS_INSUFICIENTES`.
Em nenhum momento são excluídos do inventário de projetos.

### 13. Como projetos sem repositório são representados?
Projetos sem repositório cadastrado (exemplo comprovado em produção: `proj:incubacao-labs`) continuam presentes através da tabela `pub_neural.holding_projects`. Na consulta de atividade:
- `repository_count = 0`
- `observation_count = 0`
- `operational_activity_state = 'DADOS_INSUFICIENTES'`
Eles aparecem no catálogo e no Graph Explorer como nós de primeiro nível vinculados à Holding.

### 14. O runtime de agentes (ACP) já produz sinais diretamente?
Não diretamente no estado atual. O ACP não possui integração direta ou webhook próprio com o banco `pub_neural`. Os sinais de execução de agentes chegam exclusivamente quando o agente executa uma tarefa orquestrada pelo PDL, sendo reportado no campo `agent_id` dentro do `NeuralExperienceRecord`, ou quando um agente é validado e gera o evento cognitivo `AUTONOMOUS_AGENT_VALIDATED`.

### 15. O Git fornece sinais diretamente ao Neural?
Sim. A infraestrutura de `observation_sync.py` consulta diretamente a API do GitHub através da ferramenta CLI `gh`, extraindo commits, pull requests e branches para todos os repositórios listados em `project_registry`, convertendo-os em sinais estruturados.

### 16. Existe duplicação entre Git, PDL e experiência?
Há sobreposição semântica parcial, porém com separação estrita de streams e propósitos:
- Um commit realizado pelo PDL gera um `TASK_EXPERIENCE_RECORDED` (stream de tarefa com evidências cognitivas, validações e lições).
- O mesmo commit é posteriormente capturado pelo `observation_sync` como um `COMMIT` físico (stream `repo_obs:...`).
Essa dualidade é benéfica pois preserva a distinção entre a evidência física (o que o Git registrou) e a evidência de processo (se passou nos testes, qual foi a lição aprendida).

### 17. Qual é a janela temporal utilizada?
- **Imediata:** `CURRENT_DATE` UTC (atividade de hoje).
- **Semanal:** `INTERVAL '7 days'` (atividade recente).
- **Histórica / Heatmap:** 14, 30 ou 60 dias (parâmetro `window_days` na função `get_overview_data()`).

### 18. Existe distinção entre commit, tarefa, teste, deploy e resultado?
- **Física:** O `observation_sync` distingue explicitamente `COMMIT`, `PULL_REQUEST` e `BRANCH_CHANGE`.
- **Operacional:** `TASK_EXPERIENCE_RECORDED` encapsula tarefa, testes e validações em um único registro.
- **Deploy:** Não há evento isolado de deploy no barramento; o deploy é atestado via flag booleana `delivery_verified` ou `runtime_verified` dentro do `TaskEvidence`.

### 19. O cálculo mede execução significativa ou apenas volume de eventos?
Atualmente, o cálculo mede predominantemente **volume de sinais observados**. Não há ponderação qualitativa no SQL para distinguir um commit trivial de documentação de uma grande entrega arquitetural ou refatoração estrutural. Essa distinção qualitativa é um dos objetivos definidos para o contrato V1.

### 20. Quais partes estão realmente em produção?
- **Produção Ativa (Validada):**
  - `pub_neural.holding_projects` (34 projetos organizacionais ativos).
  - `pub_neural.project_repositories` (55 vínculos físicos).
  - `pub_neural.project_registry` (registro de repositórios físicos).
  - `pub_neural.neural_repository_observations` e `observation_sync_runs` (ingestão real do GitHub).
  - `console/backend/services/activity_service.py` (cálculo de atividade em produção).
  - Visualização unificada no Graph Explorer (`/api/v1/graph/unified`).
- **Implementado no Core / Em Transição:**
  - `NeuralExperienceService` e `TaskEvidence`: implementado com 100% de cobertura de testes unitários no Python, aguardando canal permanente de streaming em produção (atualmente suportado via in-process e stdio-bridge).

---

## 3. MATRIZ DE SINAIS DE TELEMETRIA (10 SINAIS AUDITADOS)

| # | Sinal de Telemetria | Origem | Destino no Neural | Status Atual | Idempotência Atual | Projeção no Grafo |
|---|---------------------|--------|-------------------|--------------|--------------------|-------------------|
| 1 | `TASK_START` | PDL | Nenhum (apenas logs locais) | Não persistido | Ausente | Nenhuma |
| 2 | `TASK_PROGRESS` | PDL | Nenhum (stdout do agente) | Não persistido | Ausente | Nenhuma |
| 3 | `TASK_COMPLETED` | PDL | `TASK_EXPERIENCE_RECORDED` | Implementado (Core) | UUIDv5 determinístico (`exp:...`) | Nó `EVENT` + Nós `LESSON`/`PATTERN` |
| 4 | `COMMIT_CREATED` | Git / GitHub | `neural_repository_observations` | Produção Ativa | `delivery_id = gh:{repo}:commit:{sha}` | Aresta física / bridge |
| 5 | `PR_OPENED_UPDATED` | Git / GitHub | `neural_repository_observations` | Produção Ativa | `delivery_id = gh:{repo}:pr:{number}` | Nó de observação |
| 6 | `TEST_SUITE_RUN` | PDL | Campo `test_summary` em `TaskEvidence` | Parcial (Embutido) | Herda da tarefa | Não projetado isoladamente |
| 7 | `DEPLOY_VERIFIED` | PDL / Runner | Campo `runtime_verified` em `TaskEvidence` | Parcial (Embutido) | Herda da tarefa | Não projetado isoladamente |
| 8 | `BLOCKER_ENCOUNTERED` | PDL | Status `BLOCKED` em `NeuralExperienceRecord` | Parcial (Embutido) | Herda da tarefa | Não projetado isoladamente |
| 9 | `CANDIDATE_FINDING` | PDL | Campo `candidate_findings` em `NeuralExperienceRecord` | Implementado (Core) | Derivada de `task_id` + índice | Nós `LESSON`/`PATTERN` (`CANDIDATE`) |
| 10 | `AGENT_METRICS` | ACP / PDL | Campos `agent_id` e `trace` no payload | Parcial (Metadados) | Herda da tarefa | Não projetado isoladamente |

---

## 4. FLUXO REAL DE PROVENIÊNCIA E CADEIA CAUSAL

A cadeia causal completa rastreada no código é estruturada em 4 camadas ontológicas:

```text
[EXECUÇÃO FÍSICA]
  GitHub Commits (SHA) ──► RepositoryObservationSync ──► pub_neural.neural_repository_observations
                                                                │
                                                                ▼
                                                   pub_neural.neural_events
                                                   (REPOSITORY_OBSERVED)
                                                                │
[EXECUÇÃO OPERACIONAL]                                         │
  PDL Task Execution                                            │
  (task_id, commit_sha, agent_id)                              │
           │                                                    │
           ▼                                                    │
  NeuralExperienceRecord                                        │
  (TaskEvidence, CandidateFindings)                             │
           │                                                    │
           ▼                                                    │
  NeuralExperienceService.record()                              │
           │                                                    │
           ▼                                                    │
  pub_neural.neural_events ◄────────────────────────────────────┘
  (TASK_EXPERIENCE_RECORDED)
           │
           ▼ (Reducer SQL: reduce_event)
[PROJEÇÃO COGNITIVA]
  pub_neural.neural_nodes (exp:{project_id}:{task_id} -> EVENT)
  pub_neural.neural_nodes (finding:{project_id}:{task_id}:{idx} -> LESSON/PATTERN [CANDIDATE])
  pub_neural.neural_edges (finding -> DERIVED_FROM -> experience)
  pub_neural.neural_fts (Indexação textual perene)
  pub_neural.neural_vector_index_jobs (Fila de embeddings vetoriais)
           │
           ▼
[OBSERVAÇÃO & GOVERNANÇA]
  console/backend/services/activity_service.py (get_overview_data)
  ┌─────────────────────────────────────────────────────────────┐
  │  ATIVIDADE OBSERVADA (Hoje, 7d, Heatmap)                    │
  │                     VS                                      │
  │  PRIORIDADE SOBERANA (holding_projects.strategic_priority)  │
  └─────────────────────────────────────────────────────────────┘
```

---

## 5. DEFINIÇÃO DE ATIVIDADE OPERACIONAL

### Critérios de Atividade
No código em produção (`activity_service.py`), um projeto é considerado ativo caso possua registros em `pub_neural.neural_repository_observations` ou eventos em `pub_neural.neural_events`:
- **Atividade Hoje (`ATIVIDADE_HOJE`):** Pelo menos 1 sinal registrado com `observed_at >= CURRENT_DATE`.
- **Atividade Recente (`ATIVIDADE_RECENTE`):** Pelo menos 1 sinal nos últimos 7 dias.
- **Sem Atividade no Período (`SEM_ATIVIDADE_NO_PERIODO`):** Zero sinais nos últimos 7 dias, porém com histórico pregresso.
- **Dados Insuficientes (`DADOS_INSUFICIENTES`):** Zero sinais em toda a história do projeto.

---

## 6. CORRELAÇÃO DE PRIORIDADE SOBERANA VS ATIVIDADE OBSERVADA

No modelo de governança da holding, a prioridade não é uma métrica computada, mas uma **diretiva soberana**:
- **Campo Canônico:** `pub_neural.holding_projects.strategic_priority`.
- **Valores Permitidos:** `'CRITICA'`, `'ALTA'`, `'PADRAO'`, `'BAIXA'`.
- **Invariante Absoluta:** O volume de atividade observado nunca altera o valor de `strategic_priority`.
- **Detecção de Desalinhamento Operacional:**
  - Projeto `CRITICA` com estado `SEM_ATIVIDADE_NO_PERIODO` $\rightarrow$ **Alerta Crítico de Desatenção**.
  - Projeto `BAIXA` com volume desproporcional de atividade $\rightarrow$ **Alerta de Dispersão de Esforço**.

---

## 7. GAPS REAIS E RECOMENDAÇÕES ESTRUTURAIS

1. **Ausência de Endpoint de Ingestão de Streaming HTTP Seguro:** O writeback do PDL opera via stdio/in-process. É recomendável formalizar um endpoint REST autenticado com mTLS ou HMAC para receber telemetria de agentes remotos.
2. **Granularidade de Eventos Intermediários:** Falhas de compilação ou execuções de suítes de testes estão embutidas em JSON em vez de emitirem telemetria de primeiro nível.
3. **Ponderação Qualitativa:** O cálculo de atividade trata 1 commit de typo com o mesmo peso de uma release completa de software.
