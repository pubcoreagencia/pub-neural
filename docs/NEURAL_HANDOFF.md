# PUB NEURAL — HANDOFF & ARCHITECTURAL FREEZE

## STATUS

PUB Neural está congelado.

O desenvolvimento ativo no repositório `pub-neural` está suspenso.
O foco operacional e de engenharia transfere-se integralmente para: **PUB PROTOTYPE**.

---

## CURRENT_STATE

**ADR-003 Experimental** formalizado e versionado em:
[`docs/adr/ADR-003-strict-tristate-evidence-gate.md`](file:///Users/user/Documents/antigravity/pub%20neural/docs/adr/ADR-003-strict-tristate-evidence-gate.md)

- **Princípio Central:** `RETRIEVAL DEPTH ≠ DECISION DEPTH`
- **Retrieval Depth ($K_{retrieval}$):** 10 candidatos
- **Verifier Depth ($K_{verifier}$):** 10 candidatos inspecionados
- **Decision Policy:** `STRICT_DIRECT_ONLY` (Aggregator B Strict)
- **Hard Negatives de Referência:** `QRY-34`, `QRY-35` (similaridade 0.677905), `QRY-36` 100% contidos.

---

## ARCHITECTURE

O pipeline arquitetural contratado opera em camadas desacopladas:

```text
QUERY
  │
  ▼
RETRIEVAL (Hybrid Dense + Lexical RRF)
  │
  ▼
TOP-K CANDIDATES (K=10)
  │
  ▼
EVIDENCE VERIFIER (Entailment / Relational Grounding)
  │
  ▼
STRICT AGGREGATOR (Decision Depth Isolation)
  │
  ▼
DECISION: [ ANSWER | ESCALATE | ABSTAIN ]
```

---

## CURRENT CONTRACT

A matriz de decisão estrita do Evidence Gate segue inviolável:

| Verifier Support Judgment | Aggregation Action | Descrição Operacional |
| :--- | :--- | :--- |
| `DIRECT_SUPPORT` | **ANSWER** | Evidência suficiente, relacional e diretamente fundamentada. |
| `PARTIAL_SUPPORT` | **ESCALATE** | Evidência parcial / incompleta; nunca emite resposta automática. |
| `INSUFFICIENT_SUPPORT` | **ESCALATE** | Evidência de baixa relevância contextual; requer escalonamento. |
| `OUT_OF_SCOPE` | **ABSTAIN** | Consulta fora do domínio ou trust zone; recusa de resposta. |
| `CONTRADICTORY` | **ESCALATE** | Evidências conflitantes detectadas entre candidatos. |

---

## IMPORTANT FINDINGS

1. **Retrieval ≠ Evidence:** Alta proximidade vetorial ou ranqueamento lexical não constitui prova factual.
2. **Dense Similarity Isolada Não É Evidência:** A distribuição de similaridade de queries supported e unsupported possui overlap maciço; threshold escalar isolado é matematicamente incapaz de separar sem degradar recall para 36%.
3. **Lexical Overlap Isolado Não É Evidência:** Coincidência de tokens e termos técnicos sem amarração relacional/sintática é fonte primária de falsos positivos.
4. **Partial Support Não Pode Gerar ANSWER:** Tratar suporte parcial como resposta automática gera alucinações e respostas incorretas por omissão de premissas cruciais.
5. **QRY-35 Permanece o Hard Negative Canônico:** Similaridade $0.677905$ rejeitada com sucesso exclusivamente pelo Evidence Gate.
6. **$K=10$ É Adequado como Retrieval Depth Experimental:** Não há razão para limitar o retrieval em $K=3$; sob a agregação strict, $K=10$ oferece cobertura máxima de recuperação ($93.94\%$) sem vazar falsos positivos.
7. **Strict Direct-Only É a Policy de Segurança Atual:** Apenas `DIRECT_SUPPORT` tem permissão de disparar `ANSWER`.

---

## EXPERIMENTAL FINDINGS

Histórico consolidado dos experimentos controlados (blind protocol, zero label leakage):

### Step 2E.3 — Blind Semantic Verifier Validation
- **Objetivo:** Avaliar se verifiers semânticos blind distinguem evidência sem vazar labels do benchmark.
- **Resultado:**
  - Verifier C alcançou $100\%$ de rejeição em unsupported ($TN=3, FP=0$).
  - Supported Acceptance no Top-1 ficou limitado a $42.42\%$ ($14/33$), provando que Top-1 é insuficiente para validação de evidência.

### Step 2E.4 — Multi-Candidate Blind Evidence Retrieval
- **Objetivo:** Avaliar candidatos além do rank 1 ($K \in \{1, 3, 5, 10\}$).
- **Resultado:**
  - Evidência comprovada de que documentos suportados residem em ranks subsequentes.
  - Sob política Lenient, $K=3$ apresentou recall de $69.70\%$ com $FP=0$, enquanto $K=5$ e $K=10$ introduziram 2 falsos positivos devido à fragilidade da agregação permissiva.

### Step 2E.5 — Retrieval vs Verifier vs Aggregation Forensic Audit
- **Objetivo:** Isolar analiticamente as perdas de Retrieval Recall, Verifier Recall e Aggregation Precision.
- **Resultado:**
  - `RETRIEVAL_RECALL@10 = 93.94%` ($31/33$)
  - `VERIFIER_EVIDENCE_RECALL@10 = 84.85%` ($28/33$)
  - Aggregator B (Strict Direct-Only) eliminou todos os falsos positivos em $K=10$:
    - `ANSWER Precision = 100%`
    - `Unsupported Containment = 100%` ($FP=0$)
  - Conclusão: O gargalo em $K=10$ não era a profundidade de busca, mas a política agregadora.

### Step 2E.6 — Adversarial Benchmark Expansion (300 Queries / 15 Classes)
- **Objetivo:** Submeter o contrato ADR-003 a estresse com 300 queries adversariais (240 unsupported, 96 supported no pool de 336).
- **Resultado:**
  - `ADR003_ROBUSTNESS = FAIL`
  - `FALSE_ANSWER_RATE = 0.1583` (38 falsos positivos)
  - `UNSUPPORTED_CONTAINMENT = 0.8417`
  - `ANSWER_PRECISION = 0.2245`
- **Diagnóstico da Causa Raiz:**
  - `PRIMARY_FAILURE_MODE = HEURISTIC_VERIFIER_OVERTRIGGERING`
  - Verifier C continha atalhos heurísticos:
    1. Regra de identificadores em maiúsculas (`UUID`, `S3`, `POSTGRESQL`, `RRF`) bypassava análise proposicional.
    2. Tolerâncias a tokens isolados de baixa informação (Classe O: tokens como `sistema`, `dados`, `pub`).
    3. Ausência de validação de entailment sujeito-predicado-objeto.

### Step 2E.7 — Propositional Entailment Verifier
- **Objetivo:** Substituir o Verifier C por verificação proposicional multi-facetada sem afrouxar o ADR-003.
- **Resultado:**
  - `Verifier D (Propositional Entailment)` reduziu drasticamente os falsos aceites:
    - Falsos positivos caíram de 31 para **apenas 1** (`ADV-078`).
    - `FALSE_ANSWER_RATE` reduziu de $0.1276$ para **$0.0041$**.
    - `UNSUPPORTED_CONTAINMENT` subiu de $0.8724$ para **$0.9959$**.
    - Falsos aceites por baixa informação (Classe O): $0.0\%$.
    - Falsos aceites por alta similaridade (Classe A, E): $0.0\%$.
  - O contrato estrito do ADR-003 foi preservado e validado.

---

## CURRENT BLOCKER

- **Regressão Restante:** Query adversarial `ADV-078` ("auditoria em tempo real no datadog"). O documento `DATABASE_SCHEMA_V0.md` contém menções a "tempo" e "real", permitindo que uma tolerância sintática de $N-1$ termos aceitasse a premissa sem aterrar a entidade proprietária externa ("datadog").
- **Experimento Planejado:** **Step 2E.8 — Named Entity & Relational Constraint Hardening**.
- **Diretriz de Congelamento:** O Step 2E.8 **NÃO** deve ser executado nesta fase. O desenvolvimento no repositório `pub-neural` está pausado.

---

## DO NOT MODIFY

Durante a pausa operacional:
1. **NÃO** afrouxar o contrato estrito do ADR-003 (`DIRECT_SUPPORT` exclusivo para `ANSWER`).
2. **NÃO** reintroduzir thresholds escalares como substitutos de evidência.
3. **NÃO** alterar códigos de produção (`src/retrieval/`, schemas, migrações, RLS).
4. **NÃO** transformar `PARTIAL_SUPPORT` em resposta direta.

---

## FUTURE NEXT STEP

Quando o desenvolvimento do PUB Neural for retomado:
1. **Executar Step 2E.8:**
   - Implementar ancoragem estrita de entidades nomeadas (*Named Entity Strict Grounding*).
   - Impedir que tolerâncias de termos descartem entidades proprietárias/externas (ex: Datadog, Snowflake, Stripe).
   - Validar suite `tests/vector/test_entity_relational_hardening.py`.
2. **Avaliar Modelo Neural de Entailment NLI:**
   - Comparar verifiers simbólicos com modelo Cross-Encoder NLI treinado para inferência factual.
3. **Integração de Produção Controlada:**
   - Apenas após 100% de contenção na suite adversarial de 336 queries.

---

## HANDOFF PRINCIPLE

> **Git é a fonte canônica e institucional de verdade do PUB Neural.**
>
> Toda decisão técnica, evidência matemática, benchmark reproduzível e contrato arquitetural estão registrados no histórico versionado do repositório `pubcoreagencia/pub-neural` na branch `main`.
