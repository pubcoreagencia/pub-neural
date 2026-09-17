# PUB PROTOTYPE → PUB NEURAL: INSTITUTIONAL HANDOFF — DUAL GATEWAY V1

**Identifier:** `PUB-NEURAL-HANDOFF-PP-DUAL-GATEWAY-V1`  
**Date:** 2026-09-17  
**Status:** `VALIDATED`  
**Confidence:** `HIGH`  
**Scope:** `PROJECT (pubcoreagencia/pub-prototype)`  
**Knowledge Type:** `DECISION + ARCHITECTURE + LESSON + EVIDENCE`  

---

## 1. Identidade do Marco

- **Repositório de Implementação:** `pubcoreagencia/pub-prototype`
- **Repositório de Infraestrutura:** `pubcoreagencia/pub-9router-cloud`
- **Natureza do Documento:** Handoff institucional de conhecimento consolidado no PUB Neural. O repositório `pub-prototype` permanece a autoridade soberana sobre código, testes e runtime.
- **Princípio de Fronteira:** O PUB Prototype e o PDL permanecem estritamente isolados em seus runtimes. O avanço arquitetural no PP não introduz dependência do PDL.

---

## 2. Decisão Arquitetural Validada

O PUB Prototype consolidou sua infraestrutura de inferência sobre uma arquitetura **Dual Gateway Soberana**, executada e orquestrada diretamente pelo `GatewayRouter` interno do PP Worker:

```text
PP Worker
    ↓
GatewayRouter
    ├── Gateway A: OpenRouter
    │      └── Catálogo Operacional FREE Verificado (10 modelos)
    │
    └── Gateway B: 9router Cloud (https://pub-9router-cloud.onrender.com/v1)
           └── Catálogo Operacional FREE Verificado (10 modelos)
```

### Regra Permanente de Governança
```text
PP = 100% FREE MODELS ONLY
PAID_MODEL_EXECUTION = FORBIDDEN
PAID_EXECUTION_PATH = NONE
```
- A política é um **hard gate pré-rede**: qualquer tentativa de modelo pago (seja primário, override, fallback implícito ou de emergência) é rejeitada com exceção antes de qualquer requisição HTTP.
- O saldo em conta no OpenRouter destina-se exclusivamente à liberação de limites de concorrência/throughput upstream, sem autorização para consumo pago.
- Não existem feature flags, escapes administrativos casuais ou fallbacks híbridos que autorizem consumo financeiro.

---

## 3. Estado Validado dos Gateways

| Gateway | Host Endpoint | Modelos Descobertos | Modelos Verificados | Status Smoke | Streaming SSE |
|---|---|---|---|---|---|
| **Gateway A: OpenRouter** | `https://openrouter.ai/api/v1` | Catálogo Global | **10 FREE** | `PASS` | `PASS` |
| **Gateway B: 9router Cloud** | `https://pub-9router-cloud.onrender.com/v1` | 28 FREE | **10 FREE** | `PASS` | `PASS` |
| **Total Combinado** | **Dual Gateway Ativo** | — | **20 FREE** | `PASS` | `PASS` |

> [!NOTE]
> **Distinção Crítica:** No 9router Cloud foram descobertos 28 identificadores de modelos `:free`/`/free`. Apenas os **10 modelos** comprovados por execução ao vivo via `POST /v1/chat/completions` com `stream=true` e conclusão íntegra compõem o catálogo operacional verificado.

### Catálogo Operacional Verificado (20 Candidatos)

#### Gateway A (OpenRouter)
1. `cohere/north-mini-code:free`
2. `nex-agi/nex-n2.5-pro:free`
3. `qwen/qwen3.8-27b:free`
4. `nvidia/nemotron-3-super-120b-a12b:free`
5. `nvidia/nemotron-3-ultra-550b-a55b:free`
6. `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free`
7. `nex-agi/nex-n2.5-mini:free`
8. `z-ai/glm-5.2:free`
9. `liquid/lfm-2.5-2.6b:free`
10. `openrouter/free` (Dynamic Tier 2 Pool)

#### Gateway B (9router Cloud)
1. `kc/cohere/north-mini-code:free`
2. `kc/nvidia/nemotron-3-super-120b-a12b:free`
3. `kc/kilo-auto/free`
4. `kc/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free`
5. `kc/dots-studio/dots-3-note-preview:free`
6. `kc/inclusionai/ling-3.0-flash-fin:free`
7. `kc/nvidia/nemotron-3-ultra-550b-a55b:free`
8. `kc/nvidia/nemotron-3.5-lightning:free`
9. `kc/nex-agi/nex-n2.5-pro:free`
10. `kc/nex-agi/nex-n2.5-mini:free`

---

## 4. Fallback Cross-Gateway Validado pelo Orquestrador

O mecanismo de fallback não é manual: pertence exclusivamente à máquina de estados do `GatewayRouter`.

### Fluxo Validado A → B
```text
OpenRouter (tentativa 1)
    ↓ falha simulada (HTTP 429 Rate Limit)
GatewayRouter emite GATEWAY_FALLBACK_STARTED
    ↓
9router Cloud (tentativa 2)
    ↓ modelo FREE: kc/cohere/north-mini-code:free
Streaming SSE real concluído com HTTP 200
```
- **Resultado:** `PROVE_CROSS_GATEWAY_A_TO_B_ORCHESTRATOR = PASS`

### Fluxo Validado B → A
```text
9router Cloud (tentativa 1)
    ↓ falha simulada (HTTP 503 Provider Unavailable)
GatewayRouter emite GATEWAY_FALLBACK_STARTED
    ↓
OpenRouter (tentativa 2)
    ↓ modelo FREE: nex-agi/nex-n2.5-pro:free
Streaming concluído com sucesso
```
- **Resultado:** `PROVE_CROSS_GATEWAY_B_TO_A_ORCHESTRATOR = PASS`
- **Conclusão:** `CROSS_GATEWAY_REAL = PASS`

---

## 5. Classificação de Falhas e Circuit Breaker

### Condições Retryable (Disparam Fallback)
- `TIMEOUT` / `IDLE_TIMEOUT` / `EXECUTION_TIMEOUT`
- `HTTP 429` (Rate Limited upstream)
- `HTTP 5xx` (`500`, `502`, `503` Provider Unavailable)
- `CONNECTION_ERROR` / `ECONNRESET`
- `HTTP 404` / `MODEL_UNAVAILABLE` (Descomissionamento upstream)

### Condições Não-Retryable (Fail-Closed Imediato)
- `HTTP 401` / `HTTP 403` (Erros de autenticação determinísticos interrompem imediatamente o orquestrador para evitar loops e banimentos)
- Tentativa de modelo pago (`PAID_MODEL_FORBIDDEN` aborta pré-rede)
- Violações determinísticas de política

### Comportamento de Circuit Breaker
- Erros de modelo (ex: `HTTP 404`) acionam cooldown determinístico (`CIRCUIT_OPEN`).
- Requisições subsequentes ignoram o candidato em falha durante a janela de cooldown, preservando a latência do pipeline.

---

## 6. Saneamento de Segurança da Infraestrutura (9router Cloud)

O repositório `pubcoreagencia/pub-9router-cloud` passou por auditoria e saneamento estrito:
- **Commit:** `4d73331cf628932dcf3db2cbd910950a6079768d`
- **Mudanças Validadas:**
  1. Remoção de senha em texto claro (`INITIAL_PASSWORD=pubdevloop2026`) de Dockerfile e render.yaml.
  2. Remoção do fallback `DB_SECRET || "pubdevloop2026"` em `restore-db.js`.
  3. Adição de guarda fail-closed no startup: `MISSING_REQUIRED_SECRET: DB_SECRET environment variable is required`.
  4. Alinhamento da porta nativa para `20128` (bind `0.0.0.0:20128`).
  5. Saneamento remoto verificado diretamente no GitHub.

---

## 7. Proveniência e Evidência de Produção

### Mapeamento de Fontes
```yaml
sources:
  - repository: pubcoreagencia/pub-prototype
    commit: 61b91cdd9baa8d848ecf9222a3a8fd36e7769ca
    role: implementation
    branch: main
    parity: LOCAL_REMOTE_PARITY_VERIFIED

  - repository: pubcoreagencia/pub-9router-cloud
    commit: 4d73331cf628932dcf3db2cbd910950a6079768d
    role: gateway-infrastructure
    branch: main
    parity: LOCAL_REMOTE_PARITY_VERIFIED
```

### Prova Operacional em Produção (Railway)
A versão do PP Worker com o Dual Gateway ativo executou uma tarefa real de prototipagem ponta a ponta:
- **Task ID:** `f1476a4c-d0a5-4667-931f-be7b33bb830d`
- **Modelo Utilizado:** `nex-agi/nex-n2.5-pro:free`
- **Fluxo:** Lease de tarefa $\to$ Seleção do candidato $\to$ Execução via streaming SSE $\to$ Geração de `index.html` $\to$ Commit Git (`9d10f93583157189d195a6939cb4173b1854d36a`) $\to$ Persistência de Checkpoint (`29430343-ab3e-4a22-9c60-7c9efa6de08d`) $\to$ Status `COMPLETED`.

---

## 8. Lições Institucionais Extraídas

1. **Catálogo Arquitetural $\neq$ Catálogo Verificado:** Listar modelos em documentações ou configs não garante capacidade operacional; apenas sondas com streaming real legitimam um candidato.
2. **Discovery $\neq$ Execução:** A presença de um ID em `GET /v1/models` não assegura sucesso em geração; a requisição real `POST /v1/chat/completions` é o único teste válido.
3. **Mock $\neq$ Evidência Operacional:** Fallbacks simulados por script não comprovam a interoperabilidade dos adaptadores e timers de produção.
4. **Orquestração Centralizada:** O fallback cross-gateway deve ser executado deterministicamente pelo orquestrador (`GatewayRouter`), encapsulando a complexidade sem intervenção manual.
5. **Políticas como Invariantes Pré-Rede:** Regras de negócio (ex: proibição de modelos pagos) devem ser bloqueadas no nível estrutural de código antes de qualquer chamada HTTP para eliminar riscos de vazamento financeiro.
6. **Soberania e Isolamento de Fronteiras:** O ecossistema compartilha inteligência via PUB Neural, mantendo os runtimes do PP e PDL desacoplados.
