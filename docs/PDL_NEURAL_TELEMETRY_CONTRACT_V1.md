# CONTRATO DE TELEMETRIA PDL → PUB NEURAL V1
### Especificação Formal de Ingestão de Telemetria Operacional, Proveniência e Estados Epistêmicos

**Status:** CONTRATO NORMATIVO CANÔNICO (V1.0)  
**Documento:** `docs/PDL_NEURAL_TELEMETRY_CONTRACT_V1.md`  
**Data:** 17 de Setembro de 2026  
**Autoridade:** PUB Core Holding / Governança Soberana  
**Repositório:** `pubcoreagencia/pub-neural`  
**Branch:** `feat/retrieval-abstention-v0.3`  
**Baseline Commit:** `b5a5cdd5a78bb8ef9de01d3eed34f2d3c6238edc`  

---

## 1. PROPÓSITO E OBJETIVO

Este contrato estabelece as regras normativas, imutáveis e auditáveis para o trânsito de telemetria operacional gerada durante a execução de tarefas pelo **PUB Dev Loop (PDL)** em direção ao **PUB Neural**.

O objetivo primário é garantir que a atividade de engenharia gere evidências factuais rastreáveis, sem comprometer a integridade da memória institucional perene, respeitando a soberania da prioridade declarada e impedindo auto-promoção de conhecimento não deliberado.

---

## 2. DIVISÃO DE RESPONSABILIDADES

| Subsistema | Responsabilidade Exclusiva | O que NÃO faz |
|------------|----------------------------|---------------|
| **PDL** | Executar tarefas de engenharia, rodar testes, verificar worktree, realizar commits e pushes, estruturar evidências de execução e emitir telemetria de tarefas. | Não altera prioridades de projetos, não decide o cânone da holding, não grava diretamente em tabelas internas de governança. |
| **PUB Neural** | Validar contratos de telemetria, garantir idempotência, persistir logs monotônicos (`neural_events`), projetar nós e arestas no grafo, classificar estados epistêmicos e correlacionar atividade observada com prioridade soberana. | Não orquestra compilações de software, não altera código-fonte de repositórios, não interfere no ciclo microscópico de revisão de PRs. |

---

## 3. ESQUEMA CANÔNICO DE EVENTO DE TELEMETRIA

O evento fundamental de telemetria de tarefa emitido pelo PDL é:

```json
{
  "$schema": "https://pub.holding/schemas/neural-telemetry-task-v1.json",
  "eventId": "c7a83d46-1e5f-5b8d-9c3f-2f849b4081c2",
  "streamId": "stream:task:TASK-9001",
  "eventType": "TASK_EXPERIENCE_RECORDED",
  "version": "1.0",
  "occurredAt": "2026-09-17T20:30:00.000Z",
  "actor": {
    "id": "agent:pdl-executor:v2",
    "role": "EXECUTOR",
    "executionId": "exec_20260917_001"
  },
  "context": {
    "projectId": "proj:pub-dev-loop",
    "repository": "pubcoreagencia/pub-dev-loop",
    "branch": "feat/task-telemetry-v1",
    "commitSha": "1e5efdaecbe0bfdc228fb470288c4fc434f7285c",
    "remoteSha": "1e5efdaecbe0bfdc228fb470288c4fc434f7285c",
    "correlationId": "corr_9a8b7c6d"
  },
  "execution": {
    "taskId": "TASK-9001",
    "status": "SUCCESS",
    "objective": "Implement canonical telemetry bridge in PDL executor",
    "changedFiles": [
      "src/telemetry/bridge.py",
      "tests/test_bridge.py"
    ]
  },
  "evidence": {
    "validationPassed": true,
    "worktreeClean": true,
    "pushSucceeded": true,
    "remoteVerified": true,
    "runtimeVerified": true,
    "deliveryVerified": true,
    "governanceVerified": true,
    "testSummary": {
      "total": 42,
      "passed": 42,
      "failed": 0,
      "skipped": 0,
      "durationMs": 1420
    }
  },
  "candidateFindings": [
    {
      "findingType": "LESSON",
      "title": "Strict Idempotency Derivation",
      "statement": "UUIDv5 ensures deduplication of retried delivery attempts",
      "scope": "PROJECT",
      "confidence": 0.95,
      "candidateState": "CANDIDATE"
    }
  ],
  "provenance": {
    "ingestionSource": "pdl_experience_bridge",
    "parentCommitSha": "d4a5b6c7e8f90123456789abcdef0123456789ab",
    "consumedKnowledgeIds": [
      "lesson:pdl:git-hygiene"
    ]
  }
}
```

---

## 4. IDEMPOTÊNCIA E DEDUPLICAÇÃO

1. **Chave de Idempotência Canônica:**  
   Toda entrega de telemetria possui uma chave determinística:
   $$\text{IdempotencyKey} = \text{"exp:"} + \text{repository} + \text{":"} + \text{taskId} + \text{":"} + \text{commitSha} + \text{":"} + \text{ingestionSource}$$
2. **Derivação de `eventId`:**  
   O identificador do evento no barramento monotônico é derivado usando UUIDv5 sobre o namespace DNS canônico:
   $$\text{eventId} = \text{UUIDv5}(\text{NAMESPACE\_DNS}, \text{"exp:"} + \text{IdempotencyKey} + \text{":"} + \text{occurredAt})$$
3. **Comportamento em Redelivery:**  
   A reapresentação de um evento com a mesma chave de idempotência retorna `ALREADY_EXISTS` com status de sucesso idempotente (`idempotent: true`), sem gerar novo nó ou disparar reindexação redundante.

---

## 5. ORDENAÇÃO E EVENTOS FORA DE ORDEM

1. **Monotonicidade por Stream:**  
   O stream `stream:task:{taskId}` impõe ordem causal estrita baseada no timestamp `occurredAt` e número sequencial de versão do stream.
2. **Eventos Tardios (Delayed Arrivals):**  
   Se um evento com `occurredAt` anterior for ingerido posteriormente devido a atrasos de rede ou fila:
   - O evento é persistido no log histórico preservando seu `occurredAt` original.
   - O cálculo da janela de atividade recente respeita o timestamp real da ocorrência do fato (`occurredAt`), não o timestamp da ingestão (`recordedAt`), garantindo auditabilidade temporal fidedigna.

---

## 6. SEMÂNTICA DE RETRY E TOLERÂNCIA A FALHAS

1. **Política de Retry do Emissor (PDL):**  
   O emissor deve implementar *exponential backoff* com *jitter* (ex: $1s, 2s, 4s, 8s$) até um máximo de 5 tentativas.
2. **Armazenamento Transitório Local (*Outbox Pattern*):**  
   Caso o PUB Neural esteja temporariamente inacessível, o PDL grava o registro no diretório local `.neural/experience/outbox/{taskId}.json`. No próximo ciclo de execução, o dispatcher reenvia os eventos pendentes.

---

## 7. CADEIA DE PROVENIÊNCIA E RASTREABILIDADE

Nenhum evento de telemetria é aceito sem proveniência verificável:
- **`commitSha` Obrigatório para Tarefas Concluídas com Código:** Tarefas em status `SUCCESS` que alteraram arquivos devem obrigatoriamente reportar `commitSha` e `remoteSha`.
- **`consumedKnowledgeIds`:** Registra explicitamente quais lições ou regras cognitivas foram lidas e aplicadas pela tarefa, criando a aresta de retroalimentação `task -> USED -> knowledge`.

---

## 8. PROPAGAÇÃO E VÍNCULO DE PROJETO (`project_id`)

1. **Resolução de Projeto:**  
   Todo evento deve conter `projectId` resolvido (ex: `proj:pub-dev-loop`).
2. **Validação contra `pub_neural.holding_projects`:**  
   Se o `projectId` fornecido for desconhecido no catálogo de governança, o evento é **rejeitado imediatamente com código `UNRESOLVED_PROJECT_ID`** (*Fail-Closed*).
3. **Casos Especiais (Projetos Sem Repositório):**  
   Projetos sem repositório de código (ex: `proj:incubacao-labs`) podem receber telemetria de tarefas puramente conceituais ou de planejamento, utilizando `repository: "none"` e `commitSha: null`.

---

## 9. CLASSIFICAÇÃO DE ESTADOS EPISTÊMICOS

O PUB Neural aplica rigorosamente a separação epistêmica:

```text
       ┌───────────────────────────────┐
       │   TELEMETRIA DE EXECUÇÃO      │
       │    (FATO OBSERVADO/EXTRAÍDO)  │
       └──────────────┬────────────────┘
                      │
                      ▼
       ┌───────────────────────────────┐
       │  pub_neural.neural_events     │
       │  (TASK_EXPERIENCE_RECORDED)   │
       └──────────────┬────────────────┘
                      │
                      ▼
       ┌───────────────────────────────┐
       │  pub_neural.neural_nodes      │
       │  entity_type: EVENT           │
       │  promotion_state: CAPTURED    │
       └──────────────┬────────────────┘
                      │
       ┌──────────────┴───────────────┐
       ▼                              ▼
┌─────────────────────────┐    ┌─────────────────────────┐
│ CandidateFinding        │    │ Knowledge Governance    │
│ promotion_state:        │    │ Human Deliberation      │
│ CANDIDATE               │    │                         │
│ (NUNCA AUTO-PROMOVIDO)  │    │ requiresHumanDecision   │
└─────────────────────────┘    └────────────┬────────────┘
                                            │ (Decisão Soberana)
                                            ▼
                               ┌─────────────────────────┐
                               │ promotion_state:        │
                               │ PROMOTED (CANÔNICO)     │
                               └─────────────────────────┘
```

- **Fato Observado (`CAPTURED`):** O evento de tarefa e suas evidências físicas são imutáveis e factuais.
- **Conhecimento Candidato (`CANDIDATE`):** Descobertas e lições aprendidas sugeridas pelo executor são registradas exclusivamente como candidatas.
- **Invariante de Auto-Promoção:** Nenhum componente automatizado tem permissão para alterar `promotion_state` de `CANDIDATE` para `PROMOTED`. A promoção exige deliberação humana soberana.

---

## 10. COMPORTAMENTO FAIL-CLOSED

- **Validação de Payload:** Falha em campos obrigatórios (`taskId`, `projectId`, `status`, `evidence`) resulta em rejeição síncrona com `GateValidationError`.
- **Tentativa de Escalação de Privilégio:** Caso o emissor tente enviar `candidateState: "PROMOTED"`, o serviço sanitiza e rebaixa forçadamente para `"CANDIDATE"`, registrando log de segurança.
- **Transação Atômica:** A gravação do evento e a atualização dos índices são executadas em bloco transacional; se houver falha, o estado reverte integralmente (*all-or-nothing*).

---

## 11. CONTRATO DE ATIVIDADE OPERACIONAL

A atividade operacional de um projeto é calculada pelas agregações:
1. **Atividade Hoje:** Pelo menos 1 evento ou observação com timestamp dentro do dia corrente UTC (`observed_at >= CURRENT_DATE`).
2. **Atividade Recente:** Pelo menos 1 sinal nos últimos 7 dias.
3. **Sem Atividade no Período:** Zero sinais nos últimos 7 dias, com histórico comprovado.
4. **Dados Insuficientes:** Zero sinais registrados na base.

---

## 12. MATRIZ DE PRIORIDADE SOBERANA VS ATIVIDADE OBSERVADA

| Prioridade Declarada (`strategic_priority`) | Estado de Atividade Observada | Diagnóstico Cognitivo do Neural | Ação Recomendada do Sistema |
|---|---|---|---|
| `CRITICA` | `ATIVIDADE_HOJE` ou `ATIVIDADE_RECENTE` | **Alinhamento Saudável:** Projeto crítico com execução operacional ativa. | Manter monitoramento contínuo. |
| `CRITICA` | `SEM_ATIVIDADE_NO_PERIODO` | **Desalinhamento Severo:** Projeto de prioridade máxima paralisado ou sem telemetria. | Emitir Alerta de Desatenção para o Governante. |
| `CRITICA` | `DADOS_INSUFICIENTES` | **Risco Crítico de Blindagem:** Projeto prioritário sem telemetria configurada. | Recomendar auditoria imediata de infraestrutura. |
| `ALTA` | `SEM_ATIVIDADE_NO_PERIODO` | **Atenção Operacional:** Projeto relevante com declínio de execução. | Recomendar verificação de impedimentos. |
| `PADRAO` | Qualquer estado | **Operação Normal:** Execução em cadência esperada. | Monitoramento passivo. |
| `BAIXA` | `ATIVIDADE_HOJE` (Intensa) | **Risco de Dispersão:** Esforço operacional alocado em projeto não prioritário. | Notificar Governante sobre possível desalinhamento de recursos. |

---

## 13. INVIOLABILIDADE DA PRIORIDADE SOBERANA

> [!CAUTION]
> **REGRA FUNDAMENTAL DE SOBERANIA:**  
> Sob nenhuma hipótese o PUB Neural ou o PDL alterará automaticamente o campo `strategic_priority`. A prioridade é uma prerrogativa exclusiva e soberana da governança humana. Alta atividade não torna um projeto crítico; baixa atividade não rebaixa um projeto prioritário.
