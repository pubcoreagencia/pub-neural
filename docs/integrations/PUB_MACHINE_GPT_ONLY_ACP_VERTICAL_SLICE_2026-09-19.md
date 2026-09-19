# VERIFIED PUB MACHINE GPT-ONLY ACP VERTICAL SLICE — 2026-09-19

**Knowledge class:** EPISODIC + SEMANTIC + PROCEDURAL + LESSON + EVIDENCE
**Scope:** PUB MACHINE / ACP GPT-ONLY RUNTIME
**Status:** VALIDATED
**Confidence:** HIGH

## 1. Provenance

### PUB MACHINE
- Repository: pubcoreagencia/pub-machine
- Branch: feat/acp-pub-machine-e2e
- Verified execution checkpoint: b8c97d8

### ACP Standalone
- Repository: pubcoreagencia/pub-acp-standalone
- Branch: fix/gpt-runtime-correction-loop
- Verified code checkpoint used for the correction-loop runtime: 5ccb362a48bd0cc4a0e7f6808e1af1d5b6d8a884

### GPT Free transport POC
- Repository: pubcoreagencia/PUB-ACP-POC
- Branch: main
- Transport/runtime checkpoint referenced by the experiment: 09f1cb7

## 2. Proven runtime path

ChatGPT Free
    ↓
Chrome / CDP :9555
    ↓
PUB-ACP-POC transport :5127
    ↓
pub-acp-standalone
    ↓
GptRuntimeAdapter
    ↓
ClosedLoopEngine
    ↓
authorized workspace
    ↓
PUB MACHINE

This entry records the GPT-only path. Antigravity is not part of the active execution path for this proof.

## 3. Runtime behaviors verified

### GPT Free transport
Two isolated prompts were executed against the real local transport:

TESTE_ACP_1 → TESTE_ACP_1
TESTE_ACP_2 → TESTE_ACP_2

The responses were distinct and the corresponding session identifiers were distinct. This disproved the earlier hypothesis that the transport was globally reusing one stale response across independent calls.

### Residual concurrency incident
An earlier E2E run encountered:

Transport is currently processing another request
(standalone-e2e-session-...)

The local transport reported multiple pending sessions. A clean restart of the resident transport removed this residual state.

After restart:
- transport health returned to ok;
- the isolated prompt tests remained correct and distinct;
- the same concurrency error did not recur during the successful E2E reproduction.

Interpretation: the original git status --short repetition was not established as a deterministic response-cache/session-continuity defect. The observed blocking condition was residual concurrent transport state from the previous run.

## 4. Correction-loop proof

The real E2E flow demonstrated runtime failure followed by correction instead of immediate terminal failure.

Observed sequence:

TURN 1
git status --short
→ shell failure

CORRECTION

TURN 2
git status --short;
→ shell failure

CORRECTION

TURN 4
E2E
→ successful execution

TURN 5
[[ACP_COMPLETE]]

This validates the runtime correction behavior: a failed shell action can return diagnostics to the GPT runtime and continue within the configured turn budget.

## 5. PUB MACHINE causal vertical slice

The PUB MACHINE implementation checkpoint b8c97d8 materialized the missing causal links and contracts.

Canonical chain:

RAW SIGNAL
→ AUDIENCE PROFILE
→ SEGMENTATION
→ INTENT
→ LEAD INTENT
→ LEAD SCORING
→ DECISION
→ ACTIVATION
→ CONVERSION / RECOVERY
→ FEEDBACK

Important domain boundary:
RAW SIGNAL ≠ AUDIENCE PROFILE ≠ INTENT ≠ LEAD

The implementation introduced explicit contracts for:
- Activation: activation.contract.ts
- Feedback: feedback.contract.ts

Conversion/recovery behavior is part of the verified causal slice rather than an external-provider simulation.

No fake WhatsApp, Meta, Google or CRM provider was introduced. In-memory doubles remain test-only infrastructure.

## 6. Validation evidence

The PUB MACHINE checkpoint was reported with:
- npm test: PASS
- npm run build: PASS
- git diff --check: PASS / zero findings
- worktree: clean
- commit: b8c97d8
- no push performed

The ACP standalone correction-loop checkpoint was independently verified with:
- npm test: 148 pass / 0 fail
- contract tests: 25 pass / 0 fail
- build: PASS

The live integration/e2e tests that require the local transport were intentionally skipped when the transport was offline; the later physical run used the resident GPT Free transport on :5127.

## 7. Lessons

### Lesson A — completion must be evidence-backed
A GPT complete action is not, by itself, sufficient evidence that a project task is complete. The PUB MACHINE run initially reached [[ACP_COMPLETE]] while the workspace itself had not yet been changed.

Therefore:

GPT says complete ≠ task proven complete

A future governed completion gate should validate repository state, required tests/builds and task-specific acceptance criteria before accepting terminal completion.

### Lesson B — transient runtime state must be separated from product defects

A stale concurrent transport state can manifest as a misleading application symptom. Recovery should first establish a clean runtime state before changing application code.

### Lesson C — preserve causal domain boundaries

The PUB MACHINE vertical slice must keep RAW SIGNAL, AUDIENCE PROFILE, INTENT and LEAD as distinct domain objects. Adapters may connect them, but must not collapse them into a single overloaded model.

### Lesson D — validation belongs to the causal proof

The implementation is not considered complete merely because the final action is complete. The repository state, tests, build and diff must corroborate the claim.

## 8. Reusable architectural patterns

### GPT-only autonomous execution
GPT Free → local transport → governed workspace executor → correction loop

### Evidence-backed completion
agent completion signal
    ↓
workspace verification
    ↓
tests
    ↓
build
    ↓
git evidence
    ↓
terminal completion

### Causal business execution
signal → audience → intent → lead → scoring → decision → activation → conversion/recovery → feedback

## 9. Promotion boundary

Current promotion state:
CAPTURED → OBSERVED → EXTRACTED → CANDIDATE → VALIDATED

This entry is VALIDATED because the referenced repositories and checkpoints exist and the runtime/validation evidence was produced in the local execution environment.

Do not yet promote the runtime pattern to holding-wide mandatory infrastructure. Future promotion to ADOPTED or INSTITUTIONAL requires repeated use beyond this single proof and explicit governance ratification.

## 10. Source-of-truth rule

PUB MACHINE = authority for its implementation
PUB ACP / transport = authority for runtime implementation
PUB NEURAL = authority for consolidated institutional knowledge
RUNTIME / TESTS / GIT = evidence hierarchy above historical memory

Neural records the knowledge and provenance. It does not replace either project repository.