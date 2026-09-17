# MODELO OPERACIONAL PUB NEURAL V1
### Arquitetura Canônica do Sistema Operacional Cognitivo da PUB Core Holding

**Status:** CANONICAL ARCHITECTURAL SPECIFICATION (V1.0)  
**Documento:** `docs/MODELO_OPERACIONAL_PUB_NEURAL_V1.md`  
**Data:** 17 de Setembro de 2026  
**Autoridade:** PUB Core Holding / CEO Sovereign Governance  
**Classificação:** Arquitetural e Conceitual — Pré-Implementação  
**Repositório:** `pubcoreagencia/pub-neural` (`feat/retrieval-abstention-v0.3`)

---

## 1. OBJETIVO

O **PUB Neural** é o sistema operacional cognitivo, memória institucional perene e cérebro de governança da **PUB Core Holding**.

O objetivo deste documento é consolidar o **Modelo Operacional PUB Neural V1**, estabelecendo uma arquitetura conceitual e ontológica unificada para toda a holding a partir da auditoria empírica do ecossistema existente (`pub-neural`, `pub-dev-loop`, `pub-core-os`, `ACP` e `Git`).

### A Invariante Fundamental: Generalização sem Cópia

> [!IMPORTANT]
> **PUB NEURAL NÃO É UM PDL GIGANTE.**  
> O PUB Dev Loop (PDL) é um laboratório validado e especializado em **execução de tarefas de engenharia de software**. O PUB Neural **NÃO** deve copiar pipelines, workers de código, métricas estritamente de pull requests, arquivos temporários ou lógicas microscópicas de desenvolvimento (`Developer`, `Reviewer`, `QA`, `MAX_REVIEW_ITERATIONS`).  
> O Neural extrai do PDL os **princípios universais de inteligência e consciência organizacional**, generalizando-os para o nível da **Holding, Empresas, Projetos, Oportunidades, Decisões e Governança Humana**.

---

## 2. PRINCÍPIOS FUNDAMENTAIS

1. **Inteligência Observa e Explica; Inteligência Não Governa e Não Executa:**  
   O sistema cognitivo correlaciona fatos, analisa telemetria e sugere diagnósticos. Toda síntese analítica é consultiva.
2. **Soberania Humana Estrita (`requiresHumanDecision = true`):**  
   O Neural nunca decide estratégia, nunca altera prioridades soberanas silenciosamente e nunca auto-promove conhecimento para o cânone institucional sem a chancela do CEO / Governante.
3. **Fato vs Inferência vs Recomendação:**  
   O sistema separa rigorosamente:
   * **Observado (`EXTRACTED` / `OBSERVED`):** Registro factual com proveniência e hash de evidência.
   * **Inferido (`INFERRED` / `CANDIDATE`):** Hipótese ou correlação probabilística com score de confiança explícito.
   * **Recomendado (`PROPOSED` / `ADVISORY`):** Sugestão de ação estrutural que demanda deliberação soberana.
4. **Sem Ranking, Sem Punição e Sem Atividade Falsa:**  
   A telemetria serve para identificar gargalos, desalinhamentos e riscos sistêmicos, nunca para rankear pessoas ou premiar atividade artificial (ex: commits inflados, micro-tarefas vazias).
5. **Prioridade Declarada vs Atividade Observada:**  
   Prioridade não nasce do volume de código nem do ruído operacional de agentes. Prioridade é uma **decisão humana soberana**. O papel do Neural é comparar a intenção com a realidade.
6. **Imutabilidade e Event Sourcing:**  
   Toda evolução de estado é derivada de logs de eventos monotônicos (`neural_events`), auditáveis e protegidos contra envenenamento de memória (*memory poisoning*).

---

## 3. FONTES DE VERDADE E DELIMITAÇÃO DE AUTORIDADE

A holding opera com divisão estrita de autoridade física, operacional e cognitiva:

```text
┌────────────────────────┬──────────────────────────────────────────────────────────────────────────┐
│ Sistema / Subsistema   │ Esfera de Autoridade Exclusiva                                           │
├────────────────────────┼──────────────────────────────────────────────────────────────────────────┤
│ GitHub / Git           │ Fonte de verdade física do código versionado (55 repositórios, commits,  │
│                        │ branches, paths, blobs, tags). Git dita o estado real do software.       │
├────────────────────────┼──────────────────────────────────────────────────────────────────────────┤
│ PUB Dev Loop (PDL)     │ Fonte de telemetria e execução operacional de ciclos de engenharia       │
│                        │ (tarefas, gates de experiência, testes de regressão, reviews).          │
├────────────────────────┼──────────────────────────────────────────────────────────────────────────┤
│ ACP Runtime            │ Runtime físico de execução e orquestração de agentes.                     │
├────────────────────────┼──────────────────────────────────────────────────────────────────────────┤
│ PUB Neural             │ Fonte de verdade institucional, ontológica e cognitiva. Preserva a       │
│                        │ memória histórica, o grafo unificado, decisões soberanas e inteligência. │
└────────────────────────┴──────────────────────────────────────────────────────────────────────────┘
```

> [!NOTE]
> O PUB Neural correlaciona e projeta as evidências providas pelo Git, PDL e ACP, mas **não assume propriedade sobre a realidade física** que pertence ao Git nem sobre o runtime efêmero de tarefas.

---

## 4. ARQUITETURA EM CINCO CAMADAS

O ecossistema do PUB Neural V1 organiza-se em cinco camadas concêntricas e desacopladas:

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ 5. EXPERIÊNCIA (O Escritório, Missões, Conquistas, Telemetria Humana)    │
├──────────────────────────────────────────────────────────────────────────┤
│ 4. OPERAÇÃO (Missões, Tarefas, Execuções, Validações, Riscos, Gargalos)  │
├──────────────────────────────────────────────────────────────────────────┤
│ 3. PORTFÓLIO (Holding, Empresas, Produtos, Projetos, Oportunidades, Ideas)│
├──────────────────────────────────────────────────────────────────────────┤
│ 2. COMANDO (Intenção, Decisão Soberana, Estratégia, Objetivos, Prioridade)│
├──────────────────────────────────────────────────────────────────────────┤
│ 1. CÉREBRO (Conhecimento, Memória Bi-Temporal, Grafos, Evidências, RRF)  │
└──────────────────────────────────────────────────────────────────────────┘
```

### 4.1 CÉREBRO (Camada Cognitiva Fundacional)
* **Responsabilidade:** Ingestão de fontes, extração estrutural, preservação de blobs em CAS (`source_blobs`), ancoragem de evidências (`neural_evidence`), bi-temporalidade (`valid_time` vs `system_time`), busca híbrida (3-Way RRF), resolução de contradições e projeção de grafos (`neural_nodes`, `neural_edges`).
* **Invariante:** O Cérebro preserva o passado de forma imutável via replay de eventos.

### 4.2 COMANDO (Camada Estratégica e Soberana)
* **Responsabilidade:** Registro de intenções do CEO, decisões ratificadas (`DECISION_RATIFIED`), formulação de estratégia da holding, definição de objetivos estratégicos e atribuição explícita de **prioridade soberana**.
* **Invariante:** Nenhuma IA ou agente pode aprovar decisões de governança ou alterar a prioridade estratégica de um projeto sem mandato explícito de `pub_neural_ceo`.

### 4.3 PORTFÓLIO (Camada Ontológica da Holding)
* **Responsabilidade:** Mapeamento estrutural das organizações (`ORGANIZATION`), unidades de negócio / empresas, linhas de produto, ideias de mercado, oportunidades mapeadas e projetos organizacionais (`holding_projects`).
* **Invariante:** Mantém a dissociação formal entre o **Projeto** (entidade de negócio/portfólio) e os **Repositórios** (artefatos de código).

### 4.4 OPERAÇÃO (Camada de Execução e Alinhamento)
* **Responsabilidade:** Orquestração de grandes missões, vínculo de tarefas operacionais, monitoramento de dependências entre projetos, detecção de gargalos de entrega, bloqueios técnicos e validação de resultados.
* **Invariante:** A operação reflete o trabalho real executado pelo time e pelos agentes, gerando evidências empíricas de progresso.

### 4.5 EXPERIÊNCIA (Camada de Interação e Consciência)
* **Responsabilidade:** Interface imersiva (*O Escritório da PUB Core Holding*), visualização do grafo de conhecimento, painel de controle executivo (Central de Comando), linha do tempo causal de eventos e trilha de conquistas verificáveis.
* **Invariante:** Proporciona consciência situacional instantânea ao tomador de decisão sem expor complexidades de baixo nível do banco de dados.

---

## 5. CICLO OPERACIONAL CANÔNICO DA HOLDING

O ciclo operacional completo da PUB Core Holding segue um fluxo descendente de intenção e ascendente de evidência e aprendizado:

```text
                  CEO / HOLDING
                        ↓
                     INTENÇÃO
                        ↓
                     DECISÃO
                        ↓
                    ESTRATÉGIA
                        ↓
                     OBJETIVO
                        ↓
                    PRIORIDADE (Humana Soberana)
                        ↓
                   OPORTUNIDADE
                        ↓
                      IDEIA
                        ↓
                     PROJETO
                        ↓
                     MISSÃO
                        ↓
                     TAREFA
                        ↓
                    EXECUÇÃO
                        ↓
                    RESULTADO
                        ↓
                    EVIDÊNCIA (Física / Git / Runtime)
                        ↓
           GARGALO / RISCO / DEPENDÊNCIA
                        ↓
                    CONQUISTA
                        ↓
                   APRENDIZADO (Lições / Padrões)
                        ↓
                 MEMÓRIA NEURAL (Imutável)
                        ↓
                  PRÓXIMA DECISÃO
```

---

## 6. MODELO DE ENTIDADES E RELAÇÕES

### 6.1 Catálogo de Entidades do Modelo V1

| Entidade Conceitual | Nível / Camada | Representação Canônica no PUB Neural | Estado Atual no Schema |
| :--- | :--- | :--- | :--- |
| **Holding / Organização** | Portfólio | `pub_neural.neural_nodes` (`entity_type = 'ORGANIZATION'`) | `EXISTENTE E CANÔNICO` (`org:pubcoreagencia`) |
| **Projeto** | Portfólio | `pub_neural.holding_projects` (`proj:<slug>`) e `neural_nodes` (`PROJECT`) | `EXISTENTE E CANÔNICO` (34 projetos mapeados) |
| **Repositório** | Infra / Físico | `pub_neural.project_registry` (`repo:<org>/<name>`) e `neural_nodes` (`REPOSITORY`) | `EXISTENTE E CANÔNICO` (55 repositórios) |
| **Ideia / Oportunidade** | Portfólio / Negócio| `pub_neural.neural_nodes` (`entity_type = 'CONCEPT'`), status `PROPOSED` | `EXISTENTE MAS ESPECÍFICO` (A ser generalizado) |
| **Decisão Estratégica** | Comando | `pub_neural.neural_nodes` (`entity_type = 'DECISION'`), status `VALIDATED`/`INSTITUTIONAL` | `EXISTENTE E CANÔNICO` |
| **Regra / Governança** | Comando | `pub_neural.neural_nodes` (`entity_type IN ('RULE', 'GOVERNANCE')`) | `EXISTENTE E CANÔNICO` |
| **Padrão / Lição** | Cérebro / Memória | `pub_neural.neural_nodes` (`entity_type IN ('PATTERN', 'LESSON')`) | `EXISTENTE E CANÔNICO` |
| **Missão** | Operação | Agrupamento de nós de execução vinculados a `project_id` com escopo temporal | `AUSENTE` (Projetado como abstração sobre `neural_nodes`) |
| **Tarefa / Execução** | Operação | `pub_neural.neural_events` (`TASK_EXPERIENCE_RECORDED`) / telemetria PDL | `EXISTENTE E CANÔNICO` |
| **Evidência** | Cérebro | `pub_neural.neural_evidence` (citações de código, commits, relatórios) | `EXISTENTE E CANÔNICO` |
| **Fonte de Código** | Cérebro / Git | `pub_neural.neural_sources` e `pub_neural.source_blobs` | `EXISTENTE E CANÔNICO` |
| **Ator / Agente** | Operação / Comando | `pub_neural.trusted_actors` e `neural_nodes` (`AGENT`) | `EXISTENTE E CANÔNICO` |

### 6.2 Catálogo de Relações Canônicas

O modelo utiliza estritamente o enum `neural_relation_type`:
* `CONTAINS`: Holding $\to$ Projeto; Projeto $\to$ Repositório.
* `IMPLEMENTS`: Repositório $\to$ Projeto; Código $\to$ Decisão.
* `APPLIES_TO`: Regra $\to$ Projeto; Lição $\to$ Missão.
* `USES`: Projeto A $\to$ Projeto B (dependência sistêmica); Repositório $\to$ Lib.
* `DEPENDS_ON`: Projeto $\to$ Projeto; Missão $\to$ Missão.
* `DERIVED_FROM`: Decisão $\to$ Evidência; Aprendizado $\to$ Execução.
* `VALIDATED_BY`: Hipótese $\to$ Evidência / Teste em produção.
* `CONTRADICTS`: Evidência Divergente $\to$ Hipótese / Documento Obsoleto.
* `SUPERSEDES`: Nova Decisão Soberana $\to$ Decisão Antiga.

---

## 7. CICLOS DE VIDA CANÔNICOS

### 7.1 Ciclo de Vida da Ideia / Oportunidade

Toda iniciativa de negócio ou inovação percorre um funil auditável:

```text
IDEIA
  ↓
RASCUNHO (Conceito inicial registrado sem compromisso de recurso)
  ↓
PESQUISA (Scout de mercado, viabilidade técnica, benchmark)
  ↓
VALIDAÇÃO (Critérios de tração, aderência arquitetural, aprovação)
  ↓
OPORTUNIDADE (Caso de negócio claro e qualificado)
  ↓
PROJETO (Criação formal em holding_projects com slug canônico)
  ↓
PROTÓTIPO (Primeiro repositório, prova de conceito funcional)
  ↓
PRODUTO (Entregável comercialmente viável e testado)
  ↓
MERCADO (Operação real com usuários e tração)
  ↓
NEGÓCIO (Geração de receita e sustentabilidade operacional)
  ↓
ESCALA (Expansão de infraestrutura e equipe)
  ↓
SAÍDA (Incorporação, cisão ou conclusão do ciclo institucional)
```

### 7.2 Ciclo de Vida do Projeto

Conforme implementado no schema (`holding_projects.lifecycle_status` e `project_registry.lifecycle_status`):

```text
IDEIA
  ↓
DESCOBERTA (Levantamento de escopo, dependências e repositórios necessários)
  ↓
DESENVOLVIMENTO (Fase ativa de construção e integração)
  ↓
FUNCIONAL (Software operando em ambiente de staging / homologação)
  ↓
ATIVO (Em produção plena, monitorado pelo Neural Observatory)
  ↓
PAUSADO (Congelado temporariamente por decisão estratégica do CEO)
  ↓
ARQUIVADO (Descontinuado ou preservado apenas como patrimônio histórico)
```

---

## 8. REGRA FUNDAMENTAL DE PRIORIDADE VS ATIVIDADE

> [!WARNING]
> **A PRIORIDADE NUNCA DEVE SER DEDUZIDA DE TELEMETRIA.**  
> Quantidade de commits, linhas de código alteradas, número de tarefas fechadas no PDL ou volume de eventos em fila de agentes NÃO definem prioridade estratégica.

### O Diagnóstico de Alinhamento Estratégico

A prioridade é definida **exclusivamente por decisão soberana** (`holding_projects.strategic_priority` $\in$ `{CRITICA, ALTA, PADRAO, BAIXA}`). O PUB Neural compara a **Prioridade Declarada** com a **Atividade Observada** (derivada de `observation_sync_runs` e `neural_events`) para revelar quatro quadrantes diagnósticos objetivos:

```text
                      ATIVIDADE OBSERVADA (Telemetria)
                           BAIXA                      ALTA
                 ┌─────────────────────────┬─────────────────────────┐
                 │  PRIORIDADE SUBEXECUTADA│    EXECUÇÃO ALINHADA    │
            ALTA │  Risco de abandono ou   │  Foco e recursos        │
PRIORIDADE       │  bloqueio estrutural    │  correspondendo à       │
DECLARADA        │  (Demanda atenção CEO)  │  decisão do comando     │
(Governança)     ├─────────────────────────┼─────────────────────────┤
                 │ OPORTUNIDADE ADORMECIDA │   POSSÍVEL DESVIO DE    │
           BAIXA │ Ideia de baixo impacto  │        RECURSOS         │
                 │ sem gasto de recursos   │ Muita energia gasta     │
                 │ (Normal)                │ onde o valor é baixo    │
                 └─────────────────────────┴─────────────────────────┘
```

Estes estados são **diagnósticos sistêmicos consultivos**, nunca métricas punitivas de time.

---

## 9. PROJETO NÃO É EXECUÇÃO (DISSOCIAÇÃO CANÔNICA)

O modelo V1 preserva com rigor a separação conceitual:

```text
PROJETO = Objeto organizacional, institucional e de negócio (Dura anos).
EXECUÇÃO = Atividade física e temporal observada sobre os repositórios (Dura horas/dias).
```

* **Repositórios Git**, **Tasks do PDL** e **Runs do ACP** produzem sinais de execução.
* A telemetria física **não pode alterar silenciosamente** a governança, a prioridade ou os marcos estratégicos de um projeto.
* Se um projeto ficar 6 meses sem commits, ele não deixa de ser um projeto institucional prioritário; ele passa a ser um projeto em estado `PRIORIDADE_SUBEXECUTADA`.

---

## 10. INTELIGÊNCIA E CONSCIÊNCIA ORGANIZACIONAL

Generalizando a auditoria do PDL para o nível da Holding:

### 10.1 Inteligência Organizacional (Motor Analítico)
O motor de inteligência do Neural processa o grafo e as evidências para extrair:
* **Gargalos Estruturais:** Múltiplos projetos dependendo de um único repositório sem releases recentes.
* **Riscos de Regressão:** Projetos críticos com alta taxa de contradição epistêmica (`CONTRADICTORY`).
* **Tendências Operacionais:** Desvio de esforço entre unidades de negócio.
* **Dependências Circulares:** Bloqueios de dependência mútua entre projetos.

### 10.2 Consciência Organizacional (Visão Executiva)
Camada de síntese apresentada ao tomador de decisão humano:
* Relatórios consolidados de saúde da holding (`neural_community_reports`).
* Notificação de desvios estratégicos sem ruído microscópico de código.
* Exibição clara de fatos observados, premissas assumidas e opções disponíveis.

---

## 11. HIERARQUIA DE VERDADE E PROTEÇÃO DA MEMÓRIA

Seguindo os aprendizados de integridade epistêmica:

### 11.1 Hierarquia de Autoridade
```text
RUNTIME ATUAL / TESTES EM PRODUÇÃO (Nível 5 - Máxima Autoridade)
         >
RESULTADO DE EXECUÇÃO OBSERVADA (Nível 4)
         >
REVIEW / AUDITORIA DE PROVENIÊNCIA (Nível 3)
         >
CONHECIMENTO VALIDADO E ADOTADO (Nível 2)
         >
MEMÓRIA HISTÓRICA / ANOTAÇÕES (Nível 1)
```

### 11.2 Proteção contra Memory Poisoning e Alucinação
1. **Falsificação de Autoridade Bloqueada:** A função de banco de dados `pub_neural.append_event` valida o role do ator via sessão autenticada. Um agente ou ingestor não pode registrar eventos fingindo ser `CEO`.
2. **Quarentena de Descobertas (`CANDIDATE`):** Toda descoberta advinda de tarefas ou extração automatizada de código entra no grafo como `CANDIDATE` ou `PROPOSED`. Nunca ingressa como verdade institucional sem gate humano.
3. **Contradições Explícitas:** Quando duas fontes discordam, o Neural cria uma aresta `CONTRADICTS` e marca o conflito como `CONTRADICTORY`, em vez de sobrescrever dados às cegas.

---

## 12. O ESCRITÓRIO DA PUB CORE HOLDING

O conceito de **O Escritório** evolui de um workspace de desenvolvedor no PDL para o **ambiente operacional vivo da Holding**:

* **Unidades de Negócio como Departamentos:** Empresas e iniciativas da holding agrupadas funcionalmente.
* **Projetos como Missões:** Cada projeto ativo possui objetivos delimitados, responsáveis e contexto unificado.
* **Agentes Especializados com Mandato:** Agentes atuam com escopos claros de pesquisa (`RESEARCHER`), ingestão (`INGESTOR`) ou desenvolvimento sob supervisão, sem autonomia política sobre o portfólio.
* **Visão Espacial Integrada:** Futura interface onde o CEO transita entre a visão macro do portfólio, o Grafo de Conhecimento e a Central de Operações.

---

## 13. CONQUISTAS E GAMIFICAÇÃO OPERACIONAL

> [!IMPORTANT]
> **SEM GAMIFICAÇÃO ARTIFICIAL.**  
> A auditoria no PDL comprovou que não existe um sistema de XP previamente consolidado. O PUB Neural **NÃO inventa métricas fictícias**.  
> O modelo V1 define apenas o contrato conceitual: XP e conquistas devem derivar estritamente de **marcos institucionais reais e auditáveis no log de eventos**.

### Exemplos de Conquistas Baseadas em Eventos Verificáveis:
1. `PRIMEIRO_DEPLOY`: Primeiro deploy documentado com hash Git em produção.
2. `CICLO_FECHADO`: Conclusão bem-sucedida de um ciclo: Intenção $\to$ Execução $\to$ Evidência.
3. `CACADOR_DE_GARGALOS`: Identificação e resolução de dependência bloqueante entre dois projetos.
4. `MEMORIA_INSTITUCIONAL`: Ratificação de uma decisão ou lição que preveniu uma regressão conhecida.
5. `SEM_DESVIO`: Manutenção de um projeto crítico no quadrante de execução perfeitamente alinhada por 30 dias.
6. `IDEIA_PRODUTO`: Transição completa de um nó no ciclo de vida de `IDEIA` para `PRODUTO` ativo.

---

## 14. MAPEAMENTO DETALHADO CONTRA O SCHEMA ATUAL

Auditoria exaustiva das tabelas e enums existentes no banco `pub_neural`:

| Conceito Operacional V1 | Mapeamento no Banco / Modelos Existentes | Classificação | Ação Arquitetural |
| :--- | :--- | :--- | :--- |
| **Holding / Organização** | `pub_neural.neural_nodes` (`ORGANIZATION`) | `EXISTENTE E CANÔNICO` | Reutilizar `org:pubcoreagencia`. |
| **Catálogo de Repositórios**| `pub_neural.project_registry` | `EXISTENTE E CANÔNICO` | Reutilizar para os 55 repositórios Git. |
| **Projetos Organizacionais**| `pub_neural.holding_projects` | `EXISTENTE E CANÔNICO` | Reutilizar autoridade canônica dos 34 projetos. |
| **Vínculo Projeto $\leftrightarrow$ Repo**| `pub_neural.project_repositories` | `EXISTENTE E CANÔNICO` | Reutilizar com status epistemológico e `is_primary`. |
| **Event Sourcing Imutável** | `pub_neural.neural_events`, `neural_event_parents` | `EXISTENTE E CANÔNICO` | Reutilizar como única autoridade de mutação. |
| **Preservação de Evidência**| `pub_neural.source_blobs`, `neural_evidence` | `EXISTENTE E CANÔNICO` | Reutilizar para citações de código e arquivos. |
| **Grafo Cognitivo Unificado**| `pub_neural.neural_nodes`, `neural_edges` | `EXISTENTE E CANÔNICO` | Reutilizar para projeção de conhecimento e topologia. |
| **Governança e Sessões** | `pub_neural.trusted_actors`, `active_sessions` | `EXISTENTE E CANÔNICO` | Reutilizar para controle de acesso RLS e roles. |
| **Telemetria de Observação**| `pub_neural.observation_sync_runs` | `EXISTENTE E CANÔNICO` | Reutilizar para comparar prioridade vs atividade. |
| **Ideias e Oportunidades** | `pub_neural.neural_nodes` (`entity_type = 'CONCEPT'`) | `EXISTENTE MAS ESPECÍFICO` | Generalizar semântica de `CONCEPT` com tags ontológicas. |
| **Missões da Holding** | Agrupamento lógico em `neural_nodes` / `neural_events` | `AUSENTE` | Projetar sobre eventos de tarefa sem criar tabela paralela. |
| **XP / Conquistas** | Contrato de cálculo determinístico sobre eventos | `AUSENTE` | Projetar como função de projeção, sem persistência prematura. |
| **Pipelines Microscópicos** | Filas temporárias de código do PDL | `LEGADO / ESPECÍFICO` | **NÃO CRIAR** no Neural (pertencem ao PDL). |

---

## 15. DUPLICAÇÕES EVITADAS E O QUE NÃO SERÁ IMPLEMENTADO

Para garantir pureza arquitetural e evitar retrabalho:

### O Que NÃO Foi e NÃO Será Criado no Schema:
1. **NÃO criar tabela `tasks` paralela no banco:** Tarefas de desenvolvimento continuam pertencendo ao PDL e chegam ao Neural via eventos unificados de writeback (`TASK_EXPERIENCE_RECORDED`).
2. **NÃO criar tabela `projects` alternativa:** `pub_neural.holding_projects` é a autoridade canônica definitiva de projetos.
3. **NÃO criar enums de prioridade redundantes:** Utiliza-se `strategic_priority` existente (`PADRAO`, `ALTA`, `CRITICA`, `BAIXA`).
4. **NÃO criar tabelas de gamificação vazias:** Conquistas e pontuações serão derivadas de consultas e projeções sobre eventos reais.
5. **NÃO implementar UI de Central de Comando nesta fase:** Esta fase é puramente arquitetural, garantindo a solidez dos contratos antes do código frontend.

---

## 16. LACUNAS IDENTIFICADAS E PRIORIZAÇÃO

| Lacuna | Descrição | Impacto | Prioridade para Fases Futuras |
| :--- | :--- | :--- | :--- |
| **G1: Ingestão de Ideias** | Falta de endpoint específico para submissão e triagem de ideias no funil. | Médio | Média (Fase V1.2) |
| **G2: Telemetria PDL $\to$ Neural**| O canal de writeback de experiência existe no código (`NeuralExperienceService`), mas falta automação contínua de ingestão de métricas do PDL. | Alto | Alta (Fase V1.1) |
| **G3: Painel de Alinhamento**| O cálculo de prioridade declarada vs atividade existe no backend, mas precisa de superfície visual na Central de Comando. | Alto | Alta (Fase V1.1) |
| **G4: Engine de Conquistas** | Regras determinísticas para detecção de marcos institucionais a partir do log de eventos. | Baixo | Baixa (Fase V1.3) |

---

## 17. ROADMAP OPERACIONAL V1

1. **Fase Atual (V1.0 - Concluída):**
   * Auditoria e consolidação conceitual do Modelo Operacional PUB Neural V1.
   * Validação visual e ontológica do Grafo Unificado com camada de `PROJECT` em produção.
   * Publicação do contrato arquitetural canônico (`docs/MODELO_OPERACIONAL_PUB_NEURAL_V1.md`).
2. **Próxima Fase (V1.1 - Central de Comando & Alinhamento Estratégico):**
   * Especificação da interface da Central de Comando (substituindo a visão temporária de overview).
   * Visualização da matriz de alinhamento: Prioridade Declarada vs Atividade Observada.
   * Conexão dos fluxos de governança para ratificação de decisões do CEO em interface visual.
3. **Fases Subsequentes (V1.2 / V1.3 - O Escritório & Portfólio Vivo):**
   * Interface imersiva do Escritório da Holding.
   * Trilha de conquistas verificáveis por eventos.
   * Expansão do funil de ideias e oportunidades.

---

## 18. CONCLUSÃO E CONFORMIDADE DE GOVERNANÇA

O **Modelo Operacional PUB Neural V1** consolida a identidade do PUB Neural como o cérebro cognitivo soberano da PUB Core Holding. Ele respeita a autoridade física do Git, extrai a maturidade operacional do PDL sem copiá-lo, protege a verdade institucional e assegura que a soberania estratégica permaneça onde pertence: nas mãos do CEO.
