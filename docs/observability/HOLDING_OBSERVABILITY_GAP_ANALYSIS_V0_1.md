# PUB NEURAL — HOLDING OBSERVABILITY GAP ANALYSIS V0.1

**Status:** AUDIT REGISTERED
**Date:** 2026-09-14
**Scope:** Holding operational observability
**Nature:** Architecture / gap analysis / factual audit
**Implementation:** NONE in this document

---

## 1. Executive Verdict

PUB Neural already has a strong foundation for knowledge intelligence, but it does not yet provide operational observability of the PUB Core Holding.

Current architecture is strong in:

- append-only canonical events
- provenance
- temporal state
- deterministic projection
- graph relations
- PostgreSQL / pgvector
- FTS
- evidence
- ingestion
- extraction
- retrieval
- governance

The missing layer is the continuous operational connection:

```text
GitHub
  -> repository observation
  -> canonical events
  -> project state
  -> operational metrics
  -> historical state
  -> CEO-facing intelligence
```

The dashboard is not the product. The product is operational awareness of the Holding.

---

## 2. Current Neural State

The V0.1 foundation already contains:

```text
neural_events
neural_event_parents
source_blobs
trusted_actors
active_sessions
neural_projection_checkpoints
neural_idempotency_records
neural_schema_versions
neural_sources
neural_nodes
neural_edges
neural_evidence
neural_vectors
neural_fts
```

The architecture follows:

```text
SOURCE
  -> VERIFY_BLOB
  -> CANONICAL_EVENT_LOG
  -> PROJECTOR
  -> DETERMINISTIC_PROJECTIONS
```

`PROJECT` and `REPOSITORY` are already represented in the ontology/model.

The existing temporal model provides `valid_from`, `valid_until`, `recorded_from`, and `recorded_until`, making historical reconstruction architecturally compatible with future operational snapshots.

---

## 3. Repository Inventory

The GitHub organization/owner `pubcoreagencia` exposes 54 repositories accessible during this audit.

Known relevant repositories include, among others:

```text
pub-neural
pub-dev-loop
pub-prototype
pub-ecom
pub-machine
pub-machine-saas
pub-leads
pub-github-mcp
pub-9router-cloud
pub-core-holding-portal
pub-ops-hub
pubcore
pubecomhub
pub-ecom-catalog-worker
pub-dev-loop-prototypes
neural-os
pub-records
pub-films
pub-3d
pub-imoveis
pub-bnb
pub-food
pub-crypto
pub-trade
pub-textil
pub-media
```

Important conclusion:

```text
Repository != Project
```

A project may contain multiple repositories, and repositories may have different roles such as canonical, legacy, alias, worker, landing, prototype, archive, experiment, or infrastructure.

Therefore the future repository registry must normalize repository identity and role instead of treating every repository as an independent project.

---

## 4. Neural Knowledge Coverage

The current consolidated master context explicitly represents a small subset of the organization's repositories, including:

```text
pub-neural
pub-dev-loop
pub-ecom
pub-machine
pub-prototype
```

Against 54 repositories discovered, this is approximately:

```text
5 / 54 = 9.3%
```

This is a context-coverage estimate, not an operational synchronization metric.

Classification:

```text
Known:              PARTIAL
Repository catalog: INCOMPLETE
Operational coverage: UNVERIFIED
```

---

## 5. Synchronization State

The existing ingestion architecture is capable of receiving source information and converting it into canonical events, but no evidence was found in the current repository of a complete continuous GitHub observer with:

```text
push listener
commit watcher
pull-request observer
release observer
workflow observer
continuous repository polling
organization-wide synchronization
```

Therefore:

```text
Current sync model: MANUAL / PROGRAMMATIC INGESTION
Continuous GitHub sync: NOT EVIDENCED
```

The architecture should eventually become:

```text
GitHub
  -> Observer
  -> Normalizer
  -> Event Store
  -> Projector
  -> Project State
  -> Metrics
  -> Dashboard
```

---

## 6. Repository Registry Gap

The current ingestion allowlist contains repository identifiers that do not match the currently discovered GitHub organization namespace consistently.

This demonstrates that the Neural does not yet possess a canonical, continuously synchronized repository catalog.

The future registry should capture at minimum:

```text
repository_id
github_owner
github_repo
canonical_name
project_id
project_type
repository_role
status
visibility
default_branch
last_commit
last_sync
last_activity
current_version
environment
architecture_version
```

Do not implement blindly. First define the canonical identity contract.

---

## 7. Current Project State Model

The Neural can already represent `PROJECT` as a knowledge entity and can associate sources with repositories, branches, commits, files, and observation timestamps.

What is missing is an explicit operational state layer.

Current conceptual model:

```text
PROJECT
  -> knowledge entity
```

Target operational model:

```text
PROJECT
  -> identity
  -> repositories
  -> events
  -> historical snapshots
  -> operational metrics
  -> health / risk / momentum
```

No second ontology should be invented if the existing Project entity can be extended through deterministic projections.

---

## 8. Missing Operational Concepts

Existing or modelable concepts:

```text
PROJECT
REPOSITORY
EVENT
SOURCE
EVIDENCE
AGENT
```

Operational concepts still requiring formal definition include:

```text
COMMIT
PULL_REQUEST
ISSUE
RELEASE
DEPLOYMENT
MILESTONE
PROJECT_SNAPSHOT
PROJECT_METRIC
PROJECT_HEALTH
PROJECT_PRIORITY
PROJECT_RISK
PROJECT_ACTIVITY
PROJECT_PROGRESS
PROJECT_MOMENTUM
SYNC_RUN
SYNC_CURSOR
```

Not every concept necessarily requires a dedicated table. Some may remain canonical event types or derived projections.

---

## 9. Historical Model

The existing bi-temporal/event architecture is a strong foundation for historical operational intelligence.

Architecturally it should become possible to answer:

```text
How was PUB Ecom yesterday at 18:00?
What changed since then?
When did it change?
Which event caused the change?
```

Current distinction:

```text
Temporal infrastructure: GREEN
Temporal operational data: RED / YELLOW
```

The problem is not the absence of temporal primitives. The problem is the absence of a continuous stream of operational repository events.

---

## 10. Evidence-First Requirement

Operational metrics must be explainable.

A future metric such as:

```text
PUB Ecom
Progress: +14%
```

must be traceable through:

```text
Metric
  -> formula
  -> period
  -> underlying events
  -> commits / milestones / tests
  -> repository
  -> source evidence
```

The current evidence/provenance model is already aligned with this requirement.

No AI-only metric should be accepted without evidence.

---

## 11. Progress Definition

`PROJECT PROGRESS` is currently NOT IMPLEMENTED and must not be reduced to commit count.

Potential evidence signals include:

```text
commits
relevant commits
files changed
tests added
tests passing
features completed
milestones completed
issues closed
PRs merged
architecture milestones
documentation maturity
deployment status
runtime health
recent activity
knowledge updates
```

The correct sequence is:

```text
Research
  -> Benchmark
  -> Define metric model
  -> Validate
  -> Implement
```

No composite score should be introduced without an explicit specification.

---

## 12. Metric Separation

The following dimensions must remain conceptually separate:

```text
ACTIVITY
PROGRESS
GROWTH
MATURITY
READINESS
PRIORITY
IMPORTANCE
HEALTH
MOMENTUM
STAGNATION
RISK
```

In particular:

```text
IMPORTANCE != ACTIVITY
PRIORITY != ACTIVITY
```

A highly active project can be low priority, while a low-activity project can remain strategically P0.

Strategic priority remains CEO-controlled and must not be inferred or changed silently by the Neural.

---

## 13. Runtime / API Gap

The repository contains a database client and canonical event operations, but no verified operational HTTP API for project-state consumption was established during this audit.

Future dashboard consumption should therefore follow:

```text
Dashboard
  -> Operational API
  -> Neural projections
  -> Canonical event history
```

Never create a parallel dashboard database that duplicates Neural state.

---

## 14. Dashboard Readiness

A static/documentation dashboard surface exists, but it is not yet an operational dashboard.

It can represent conceptual knowledge structures, but it cannot honestly expose real values for:

```text
Development Today
Growth
Progress
Momentum
Health
Risk
Stagnation
Last Global Sync
Most Active
Most Advanced
```

because the required repository observation, project mapping, metric definitions, historical snapshots, and operational API are not yet implemented.

Estimated dashboard readiness: approximately 20%.

---

## 15. Governance / Current Freeze

The current Neural handoff freezes the retrieval/evidence architecture and records the current Evidence Gate contract.

This observability initiative should therefore be treated as a new architectural workstream, not as permission to modify the frozen retrieval contract.

Do not:

```text
relax ADR-003
replace evidence with similarity thresholds
modify frozen retrieval schemas casually
turn PARTIAL_SUPPORT into ANSWER
```

The Holding Observability workstream should remain orthogonal to the frozen retrieval safety contract.

---

## 16. Decision Gate

### Current Neural

```text
Knowledge foundation:          GREEN
Event foundation:              GREEN
Provenance:                    GREEN
Temporal model:                GREEN
Evidence model:                GREEN
Retrieval foundation:          GREEN
Governance:                    GREEN
Repository inventory:          YELLOW
Project mapping:               RED
GitHub observer:               RED
Continuous synchronization:    RED
Project state:                 RED
Operational metrics:           RED
Historical operations:         YELLOW
Operational API:               RED
Dashboard:                     RED
```

### Audit scores

These are audit assessments, not current Neural metrics:

```text
Neural Foundation             85%
Repository Coverage            9.3%
Exact Sync Coverage             0% proven
Project Observability          ~15%
Historical Operational         ~20%
Dashboard Readiness            ~20%
Overall Operational Brain      ~25%
```

Overall status:

```text
YELLOW
```

The foundation is strong. Operational awareness is still largely absent.

---

## 17. Top 5 Gaps

### GAP 1 — Canonical Repository Registry

The Neural lacks a complete, canonical, continuously synchronized registry of the organization's repositories.

### GAP 2 — Continuous GitHub Observer

There is no verified continuous GitHub-to-Neural observer covering the minimum operational event stream.

### GAP 3 — Operational Project State

`PROJECT` exists semantically, but there is no mature operational state containing activity, progress, momentum, maturity, readiness, health, risk, and stagnation.

### GAP 4 — Evidence-Backed Metric Model

The formulas and evidence contracts for progress, growth, momentum, maturity, and health have not yet been formally defined.

### GAP 5 — Operational API / Projection

The future dashboard needs a projection/API layer over Neural state without creating a parallel database.

---

## 18. Top 5 Implementation Priorities

These are priorities for a future implementation phase. They are NOT authorization to implement them in this audit.

### P0.1 — Canonical Repository Registry

Normalize:

```text
GitHub Repository
  -> Project
  -> Repository Role
  -> Canonical / Legacy / Auxiliary
  -> Status
```

### P0.2 — GitHub Observation Contract

Define the minimum event surface, initially evaluating:

```text
push
commit
pull request
release
workflow / deployment
```

### P0.3 — Operational Event Model

Candidate event taxonomy:

```text
REPOSITORY_DISCOVERED
COMMIT_OBSERVED
PR_MERGED
RELEASE_CREATED
WORKFLOW_COMPLETED
DEPLOYMENT_OBSERVED
SYNC_COMPLETED
```

### P0.4 — Project State + Metrics Specification

Define formally:

```text
Activity
Progress
Growth
Momentum
Maturity
Readiness
Priority
Health
Risk
Stagnation
```

Each metric must define:

```text
formula
period
evidence
confidence
source
```

### P0.5 — Operational Projection / API

Target flow:

```text
Events
  -> Projector
  -> Project State
  -> Metrics
  -> API
  -> Dashboard
```

---

## 19. Proposed Minimal V0.1 Architecture

```text
                 GITHUB ORGANIZATION
                         |
                         v
                REPOSITORY REGISTRY
                         |
                         v
                  GITHUB OBSERVER
                         |
             +-----------+-----------+
             v           v           v
           PUSH         PR        WORKFLOW
             |           |           |
             +-----------+-----------+
                         |
                         v
                NEURAL EVENT LOG
                         |
                         v
                 DETERMINISTIC
                    PROJECTOR
                         |
                +--------+--------+
                v                 v
         PROJECT STATE       EVENT HISTORY
                |
        +-------+--------+
        v       v        v
    ACTIVITY PROGRESS MOMENTUM
        |       |        |
        +-------+--------+
                |
                v
        METRIC EXPLANATIONS
                |
                v
          OPERATIONAL API
                |
                v
          CEO DASHBOARD
```

The dashboard is only the window. Operational intelligence remains inside Neural.

---

## 20. Strategic Conclusion

The audit confirms that PUB Neural does not need a new brain.

It needs a nervous system connected to the Holding.

Current state:

```text
Knowledge Brain
```

Target state:

```text
Operational Brain
```

The transition is:

```text
GitHub
  -> observe
  -> understand
  -> measure
  -> preserve history
  -> explain change
  -> expose intelligence to CEO
```

The strategic objective is not a beautiful dashboard.

The objective is for PUB Neural to know:

```text
what projects exist
what changed
where change happened
how much meaningful progress occurred
which projects are active
which are stagnant
which are risky
which are strategically important
why each metric has its value
when the last observation occurred
```

Matheus remains the final authority for strategic priority, importance, activation, retirement, and production decisions.

The Neural observes, measures, explains, recommends, and alerts. It does not silently redefine strategy.

---

## 21. Audit Status

```text
AUDIT: COMPLETE
IMPLEMENTATION: NONE
SCHEMA CHANGES: NONE
RUNTIME CHANGES: NONE
GITHUB INTEGRATION CHANGES: NONE
DASHBOARD CHANGES: NONE
MIGRATIONS: NONE
```

This document records the factual baseline for the next Holding Observability phase.
