# PUB Neural — Runtime API V0.1 Specification

## Overview

A **Runtime API** do PUB Neural constitui a primeira superfície HTTP operacional de consulta pré-tarefa e writeback pós-tarefa entre agentes (especialmente o PUB Dev Loop / PDL) e o PUB Neural.

A superfície operacional é estritamente isolada da Console API:

```text
+------------------------------------+------------------------------------+
|            Console API             |            Runtime API             |
+------------------------------------+------------------------------------+
| Observação e visualização web     | Execução operacional entre agentes |
| Endpoint: /api/v1/status, etc.     | Endpoint: /api/v1/runtime/*        |
| Métodos: GET, OPTIONS              | Métodos: POST, GET (/health)       |
| Natureza: STRICTLY READ-ONLY       | Natureza: OPERATIONAL BOUNDARY     |
| Mutações: 405 Method Not Allowed   | Autenticação: Bearer Token isolado |
+------------------------------------+------------------------------------+
```

---

## Princípios de Autoridade e Governança

> [!IMPORTANT]
> **PUB NEURAL É ESTRITAMENTE DATA-ONLY.**
> O PUB Neural e sua Runtime API:
> - NÃO decidem execução;
> - NÃO aprovam tarefas ou PRs;
> - NÃO aprovam commits ou delivery;
> - NÃO promovem automaticamente conhecimento (Candidate != Validated);
> - NÃO alteram regras de governança;
> - NÃO comandam agentes;
> - NÃO sobrepõem evidências de runtime.

Hierarquia formal de autoridade:
```text
RUNTIME_DIRECT_EVIDENCE
>
REAL_EXECUTION
>
TEST_EVIDENCE
>
VALIDATED_KNOWLEDGE
>
HISTORICAL_MEMORY
```

---

## Contrato de Identidade e Correlação

O contrato estabelece uma linhagem rastreável formal para toda execução:

```text
taskId (Identidade do trabalho ou ticket de engenharia)
  │
  └── executionId (Identidade de uma tentativa/ciclo de execução do trabalho)
        │
        └── correlationId (Fio condutor transversal entre PDL e Neural)
              ├── PRE-TASK QUERY (/api/v1/runtime/query)
              ├── retrieved evidence / abstention decision
              ├── real worker execution & verification
              ├── commit & remote delivery
              └── POST-TASK EXPERIENCE (/api/v1/runtime/experience)
```

---

## Endpoints Operacionais

### 1. PRE-TASK Query

* **Rota:** `POST /api/v1/runtime/query`
* **Finalidade:** Consulta formal de conhecimento estruturado antes do início do planejamento de uma tarefa.
* **Headers:**
  - `Content-Type: application/json`
  - `Authorization: Bearer <PUB_NEURAL_RUNTIME_TOKEN>`
* **Exemplo de Request:**
  ```json
  {
    "requestId": "req-20260914-001",
    "taskId": "task-alpha-123",
    "executionId": "exec-cycle-456",
    "correlationId": "corr-thread-789",
    "projectId": "pub-dev-loop",
    "repository": "pubcoreagencia/pub-dev-loop",
    "branch": "feat/payment-flow",
    "objective": "Retrieve checkout idempotency rules",
    "requestedKnowledgeClasses": ["RULE", "DECISION"],
    "caller": {
      "actor_id": "pdl-worker",
      "agent_role": "developer"
    },
    "timestamp": "2026-09-14T10:00:00Z",
    "limit": 5
  }
  ```
* **Status HTTP e Estados do Gate:**
  - `HTTP 200`: `SUCCESS`, `NO_MATCH`, `ABSTAIN`, `CONFLICT`, `STALE`
  - `HTTP 400`: `INVALID_REQUEST`
  - `HTTP 401`: `UNAUTHORIZED` (token ausente ou malformado)
  - `HTTP 403`: `FORBIDDEN` (token incorreto)
  - `HTTP 503`: `UNAVAILABLE` (banco ou subsistema fora do ar)
  - `HTTP 500`: `INTERNAL_ERROR` (exceção interna não tratada)

---

### 2. POST-TASK Experience Writeback

* **Rota:** `POST /api/v1/runtime/experience`
* **Finalidade:** Ingestão append-only de lições aprendidas e evidências factuais geradas após conclusão de uma tarefa.
* **Headers:**
  - `Content-Type: application/json`
  - `Authorization: Bearer <PUB_NEURAL_RUNTIME_TOKEN>`
* **Exemplo de Request:**
  ```json
  {
    "taskId": "task-alpha-123",
    "executionId": "exec-cycle-456",
    "correlationId": "corr-thread-789",
    "projectId": "pub-dev-loop",
    "repository": "pubcoreagencia/pub-dev-loop",
    "branch": "feat/payment-flow",
    "status": "COMPLETED",
    "objective": "Implemented transactional checkout gate",
    "completedAt": "2026-09-14T10:30:00Z",
    "commitSha": "c0ffee1234567890abcdef1234567890abcdef12",
    "evidence": {
      "validationPassed": true,
      "worktreeClean": true,
      "pushSucceeded": true,
      "remoteVerified": true,
      "runtimeVerified": true
    },
    "candidateFindings": [
      {
        "finding_type": "LESSON",
        "title": "Always verify worktree",
        "statement": "Dirty worktree causes delivery rollbacks.",
        "scope": "PROJECT",
        "confidence": 0.98
      }
    ]
  }
  ```
* **Status HTTP e Resultados de Ingestão:**
  - `HTTP 200`: `ACCEPTED` (primeira ingestão com sucesso)
  - `HTTP 200`: `DUPLICATE` (idempotência preservada; não duplica eventos canônicos)
  - `HTTP 400`: `INVALID_REQUEST`
  - `HTTP 401`: `UNAUTHORIZED`
  - `HTTP 403`: `FORBIDDEN`
  - `HTTP 503`: `UNAVAILABLE`
  - `HTTP 500`: `INTERNAL_ERROR`
