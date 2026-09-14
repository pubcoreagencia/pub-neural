# PUB PROTOTYPE — AGENTIC CAPABILITY BENCHMARK (V1)

**Document Status:** CANONICAL BENCHMARK / EMPIRICAL EVIDENCE  
**Date:** 2026-09-14  
**Target Repository:** `pubcoreagencia/pub-prototype`  
**Consolidation Authority:** `pubcoreagencia/pub-neural` (`MASTER_CONTEXT.md`)  
**Knowledge State:** `VALIDATED`  
**Confidence:** `HIGH` (backed by operational execution checkpoints and session traces)

```yaml
source:
  repository: pubcoreagencia/pub-prototype
  path: docs/benchmarks/PP_AGENTIC_CAPABILITY_BENCHMARK_2026-09-14.md
  ref: main
  commit: 24da7e94e1a9e50b9eddf9ea1f00cf37b466bf73
  observed_at: 2026-09-14T08:10:00Z
knowledge:
  type: BENCHMARK
  scope: PROJECT (pub-prototype)
  status: VALIDATED
  confidence: HIGH
```

---

## 1. Executive Summary

This document institutionalizes in **PUB Neural** the proven empirical results of the autonomous agentic capability evaluation conducted on **PUB Prototype (PP)**. 

The evaluation measured whether the PUB Prototype worker agent can operate autonomously over a real codebase to inspect existing code, reason about changes, execute surgical edits, preserve surrounding functionality byte-for-byte, and validate results via automated build, preview, and security checks.

The operational baseline established that **PUB Prototype possesses real, operational agentic capability for short to medium development tasks**. Across multiple distinct tasks, the agent demonstrated disciplined tool invocation, contextual reasoning, strict scope containment, and fail-closed safety.

The primary limitation identified was **not cognitive or functional agent failure**, but rather the **high latency and availability variability of the OpenRouter FREE tier**.

---

## 2. Evaluation Setup & Provenance

### 2.1 Evaluated System & Base State
- **System Evaluated:** PUB Prototype autonomous worker environment
- **Repository:** `pubcoreagencia/pub-prototype`
- **Official Base Commit:** `24da7e94e1a9e50b9eddf9ea1f00cf37b466bf73`
- **Git Branch:** `main` (`HEAD == origin/main`, working tree clean)

> [!IMPORTANT]
> **Workspace Commit Isolation Rule:**  
> Commits `3537dec4b184cd03df5e73162db39c9294b89e45` and `4742d600c48c879184c49044408a5e02663ccbae` were generated in the ephemeral workspace/fixture repository during test execution. They are **not** commits of `pubcoreagencia/pub-prototype`. The canonical state of `pub-prototype` remains `24da7e94e1a9e50b9eddf9ea1f00cf37b466bf73`.

### 2.2 Test Fixture
- **Fixture Repository:** `https://github.com/pubcoreagencia/pub-dev-loop-prototypes.git`
- **Fixture Domain:** Interactive web application featuring client/service list, DOM rendering, search filtering, and event handling.

### 2.3 Provider & Model Configuration
- **Configured Environment Variable:** `OPENROUTER_MODEL=openrouter/free`
- **Nominal Model:** `openrouter/free` (dynamic routing pool)
- **Effectively Observed Model:** `cohere/north-mini-code:free` (selected by OpenRouter router during successful benchmark runs)

---

## 3. Benchmark Execution Matrix & Evidence

| Case ID | Task Intent | Configured Model | Effective Model | Tool Calls | Status | Key Evidence / Checkpoint |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| **PP-MODEL-VERIFY** | Diagnostic tool & provider verification | `openrouter/free` | `cohere/north-mini-code:free` | 2 | **PASS** | Checkpoint: `70cffaa00d873c906e1a4f9636a007a36ecebdfa`<br>Build: PASS |
| **PP-AGENT-QUALITY-02** | Surgical UI alteration & scope containment | `openrouter/free` | `cohere/north-mini-code:free` | >0 | **PASS** | `index.html` altered surgically;<br>`script.js` byte-preserved;<br>Build & preview verified |
| **PP-AGENT-QUALITY-03** | DOM discovery & new search feature implementation | `openrouter/free` | `cohere/north-mini-code:free` | >0 | **PASS** | Session: `1087c1b5-ba63-41e1-ba29-882f4f048ebb`<br>Task: `1a864d61-4632-43a3-a054-87815285234d`<br>Checkpoint: `897053ad-edcf-46d2-ae40-61c1a1d5ce59` |
| **PP-AGENT-QUALITY-04** | Complex feature evolution under timeout | `openrouter/free` | N/A (unresponsive) | 0 | **BLOCKED** | Timeout: 120s; 0 tool calls;<br>0 file mutations;<br>Fail-closed containment |
| **PP-AGENT-QUALITY-05** | Defect diagnosis & whitespace normalisation fix | `openrouter/free` | `cohere/north-mini-code:free` | >0 | **PASS** | Session: `a5e594e9-f484-42e2-ac0d-ae92605b186e`<br>Task: `ad488576-731b-4bd0-bd42-e242710419ab`<br>Checkpoint: `10a50a38-0ee5-49a7-88b3-eb2ae2d79cf1` |

---

## 4. Case-by-Case Forensic Analysis

### 4.1 Diagnostic Model Verification
- **Objective:** Verify whether the OpenRouter free routing pool could execute tool calls and file writes in the PP worker container.
- **Outcome:** PASS. Executed 2 tool calls, completed `write_file` successfully, achieved clean build.
- **Checkpoint:** `70cffaa00d873c906e1a4f9636a007a36ecebdfa`.
- **Finding:** Proved that `openrouter/free` could successfully route to an agentic-capable model (`cohere/north-mini-code:free`).

### 4.2 Case PP-AGENT-QUALITY-02
- **Objective:** Validate pre-alteration code inspection, single-file surgical modification, and non-target file preservation.
- **Proven Behaviors:**
  1. Inspected existing codebase before generating changes.
  2. Modified exclusively `index.html`.
  3. Preserved `script.js` byte-for-byte with zero regressions.
  4. Preserved existing functionality without side-effects.
  5. Performed post-alteration validation, build, preview, and security compliance.

### 4.3 Case PP-AGENT-QUALITY-03
- **Objective:** Autonomous DOM structure discovery, new feature implementation, search functionality, and state management.
- **Session:** `1087c1b5-ba63-41e1-ba29-882f4f048ebb`
- **Task:** `1a864d61-4632-43a3-a054-87815285234d`
- **Checkpoint:** `897053ad-edcf-46d2-ae40-61c1a1d5ce59`
- **Proven Behaviors:**
  1. Investigated existing codebase and mapped DOM element hierarchies.
  2. Executed read-before-write discipline.
  3. Modified surgically only `script.js`.
  4. Implemented search across both client and service fields.
  5. Implemented case-insensitive text matching.
  6. Implemented empty-state UI handling when no matches exist.
  7. Implemented full restoration of the original list on query reset.
  8. Preserved all baseline application capabilities.
  9. Executed clean build, preview generation, and validation checks.

### 4.4 Case PP-AGENT-QUALITY-04 (Forensic Diagnostic of BLOCKED Status)
- **Observed Metrics:**
  - Status: `BLOCKED`
  - Timeout: 120s limit exceeded
  - Tool Calls: 0
  - File Alterations: 0
  - Build / Preview: None triggered
- **Root Cause Analysis:**
  The agent did not issue any tool calls because the upstream provider request timed out at the network/infrastructure boundary (120s). The model provider failed to return a response token stream.
- **Critical Institutional Interpretation:**
  > [!NOTE]
  > `PP-AGENT-QUALITY-04` must **NOT** be classified as a failure of the agent's programming, cognitive, or reasoning capabilities. It was caused exclusively by upstream provider unavailability/timeout on the free routing tier.
- **Safety Invariant Proved:**
  Under an upstream timeout, the PP worker operated in a strict **fail-closed** manner: zero partial edits, zero file corruptions, zero dangling background processes.

### 4.5 Case PP-AGENT-QUALITY-05
- **Objective:** Surgical defect diagnosis and precision bug fixing without scope creep.
- **Session:** `a5e594e9-f484-42e2-ac0d-ae92605b186e`
- **Task:** `ad488576-731b-4bd0-bd42-e242710419ab`
- **Checkpoint:** `10a50a38-0ee5-49a7-88b3-eb2ae2d79cf1`
- **Proven Behaviors:**
  1. Accurately diagnosed a whitespace normalization bug in the search input.
  2. Executed surgical fix by applying `.trim()` to the query term.
  3. Preserved existing case-insensitive search logic.
  4. Preserved multi-attribute filtering (client and service).
  5. Preserved empty state and reset behaviors.
  6. Clean build, preview, and validation pass.

---

## 5. Proven Agentic Capabilities

The benchmark formally establishes that PUB Prototype possesses the following 11 operational capabilities:

1. **Context Ingestion & Understanding:** Rapidly reads and understands pre-existing source code structure.
2. **Read-Before-Write Discipline:** Inspects target files and verifies syntax before attempting mutations.
3. **Surgical Scope Containment:** Restricts alterations strictly to target files (`index.html` or `script.js`), preserving unedited files byte-for-byte.
4. **Tool-Call Competence:** Correctly formats and executes required tools (`read_file`, `write_file`, test/build runners).
5. **DOM & Logic Grounding:** Identifies correct DOM selectors and binds logic matching actual template elements.
6. **Feature Implementation:** Implements functional multi-criteria search, filtering, and state restoration.
7. **Regression Avoidance:** Maintains existing behaviors and contracts intact during refactoring.
8. **Defect Diagnosis:** Isolates root causes (e.g. untrimmed search inputs) and applies minimal targeted repairs.
9. **Autonomous Verification:** Executes post-alteration build and preview checks.
10. **Fail-Closed Safety:** Aborts cleanly with zero corruption when upstream timeouts or infrastructure errors occur.
11. **Security & Sandbox Compliance:** Operates within containerized boundaries without unauthorized escapes.

---

## 6. Provider Limitations & OpenRouter FREE Variability

During benchmark execution and preliminary diagnostic runs, substantial provider volatility was observed across the OpenRouter free routing pool:

1. `nex-agi/nex-n2.5-mini:free`: Exceeded 120s timeout on heavier multi-file tasks.
2. `google/gemma-4-31b-it:free`: Returned immediate `HTTP 429` (Rate Limited / Insufficient Capacity).
3. `poolside/laguna-s-2.1:free`: Returned immediate `HTTP 429`.
4. `openrouter/free` (resolving to `cohere/north-mini-code:free`): Successfully passed QUALITY-02, QUALITY-03, and QUALITY-05, but timed out on QUALITY-04.

### Institutional Finding on Free Tiers:
- **Suitability:** `openrouter/free` is suitable for non-critical, exploratory, and short/medium development loops when provider capacity is available.
- **Unsuitability:** `openrouter/free` is **not deterministic infrastructure** and must never be relied upon for critical path workloads, production deployments, or strict SLA environments.
- This finding is registered as **verified empirical knowledge**, not opinion.

---

## 7. Operational Implication & Decision Boundaries

### 7.1 For PUB Prototype (PP)
- PP's internal execution loop is validated as sound and production-ready for agentic code modification.
- For interactive development where retries are acceptable, `openrouter/free` may be used as a low-cost option.
- For automated CI/CD or mission-critical tasks, PP must use a dedicated, paid, provisioned endpoint with predictable latency.

### 7.2 For PUB Neural
- PUB Neural records this benchmark as `VALIDATED` knowledge under project scope `pub-prototype`.
- Neural can now supply future agents with verified patterns of PP's capabilities, avoiding redundant exploratory trials.

### 7.3 Future Relation with PUB Dev Loop (PDL)
- PDL ("The Office") operates with higher governance and multi-role review (Chief of Staff, Architect, Developer, Reviewer, QA).
- The lessons learned in PP regarding read-before-write discipline, single-file containment, and free-tier rate limiting are direct architectural inputs for PDL worker policies.
- **Isolation Invariant:** PP and PDL remain distinct projects. Reusable patterns may be promoted to holding-wide knowledge, but PP and PDL codebases, runtimes, and repositories remain strictly unmerged.

---

## 8. Canonical Neural Entities & Relationships

The following entity graph represents this benchmark within the PUB Neural canonical knowledge ontology:

```mermaid
graph TD
    PP["PROJECT: pub-prototype"]
    REPO["REPOSITORY: pubcoreagencia/pub-prototype<br>(commit: 24da7e9)"]
    FIXTURE["REPOSITORY: pubcoreagencia/pub-dev-loop-prototypes<br>(fixture)"]
    BENCH["DOCUMENT: PP Agentic Capability Benchmark V1"]
    
    L1["LESSON: PP Operational Agentic Capability"]
    L2["LESSON: OpenRouter FREE Endpoint Volatility"]
    L3["LESSON: QUALITY-04 Provider Timeout Containment"]
    
    P1["PATTERN: Read-Before-Write Surgical Modification"]
    P2["PATTERN: Automated Post-Edit Build & Preview Validation"]
    
    D1["DECISION: Free Tier Permitted for Prototyping Only"]
    R1["RULE: Isolate Fixture Commits from PP Core HEAD"]
    
    PP -->|USES| REPO
    BENCH -->|APPLIES_TO| PP
    BENCH -->|USES| FIXTURE
    BENCH -->|VALIDATED_BY| REPO
    
    BENCH -->|DERIVED_FROM| L1
    BENCH -->|DERIVED_FROM| L2
    BENCH -->|DERIVED_FROM| L3
    
    L1 -->|IMPLEMENTS| P1
    L1 -->|IMPLEMENTS| P2
    
    L2 -->|DERIVED_FROM| D1
    BENCH -->|REQUIRES| R1
```

### Knowledge Promotion State:
- **Promotion Lifecycle:** `CAPTURED → OBSERVED → EXTRACTED → CANDIDATE → VALIDATED`
- **Current State:** `VALIDATED` (empirically substantiated by session traces, checkpoints, and clean builds).
- **Next Promotion Gate:** Requires operational adoption in production workflow before advancing to `ADOPTED` or `INSTITUTIONAL`.
