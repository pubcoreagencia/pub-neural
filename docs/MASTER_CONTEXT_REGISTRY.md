# PUB NEURAL — MASTER CONTEXT REGISTRY

**Status:** CANONICAL REGISTRY / EVOLVING  
**Purpose:** registry of project-level Master Contexts and their consolidation state inside PUB Neural.  
**Authority:** source repositories remain authoritative for implementation state; this registry is an index and consolidation layer.

## Operating Rule

PUB Neural is the cognitive integration layer of the PUB Core Holding. Project repositories remain the primary source for code, tests, runtime state and project-specific governance. Neural consolidates reusable knowledge while preserving project scope and provenance.

Never interpret `NOT_HARVESTED` as `NOT_EXISTING`.

## Verified Master Contexts

| Repository | Role | Maturity | Priority | Master Context | Consolidation |
|---|---|---|---|---|---|
| `pubcoreagencia/pub-neural` | Cognitive brain / memory / orchestration | ONLINE / EM DEV | CRITICAL | `MASTER_CONTEXT.md` | CANONICAL |
| `pubcoreagencia/pub-dev-loop` | Autonomous engineering platform / THE OFFICE | verified by source | critical | `MASTER_CONTEXT.md` | CONSOLIDATED |
| `pubcoreagencia/pub-ecom` | Commerce operator / marketplace foundation | COMPLETE / VERIFIED / FROZEN (per source) | high | `MASTER_CONTEXT.md` | CONSOLIDATED |
| `pubcoreagencia/pub-machine` | Automated prospecting / business generation | IDEA / DESIGN | high | `MASTER_CONTEXT.md` | CONSOLIDATED |
| `pubcoreagencia/pub-prototype` | Rapid product/interface prototyping | EM DEV / GITHUB | high | `MASTER_CONTEXT.md` | CONSOLIDATED |
| `pubcoreagencia/pub-core-os` | Institutional operating system / governance | EM DEV / GITHUB | CRITICAL | `MASTER_CONTEXT.md` | CONSOLIDATED |
| `pubcoreagencia/pub-records` | Music / label / studio / beats | ONLINE / GITHUB | high | `MASTER_CONTEXT.md` | CONSOLIDATED |
| `pubcoreagencia/pub-leads` | B2B prospecting / CRM / pipeline | source verified | — | `MASTER_CONTEXT.md` | CONSOLIDATED |
| `pubcoreagencia/pub-imoveis` | Real-estate transactions / tokenization | IDEA | medium | `MASTER_CONTEXT.md` | CONSOLIDATED |
| `pubcoreagencia/pub-food` | Dark kitchens / delivery / supply | EM DEV / GITHUB | high | `MASTER_CONTEXT.md` | CONSOLIDATED |
| `pubcoreagencia/pub-3d` | Immersive 3D / WebGL / metaverse | ONLINE / GITHUB | high | `MASTER_CONTEXT.md` | CONSOLIDATED |

## Repository Inventory

The connected GitHub organization currently exposes a broader ecosystem, including:

- `PUB-CORE`
- `pubcore`
- `pub-core-holding-portal`
- `pubcoreagencia.github.io`
- `PUB-BEATS`
- `pub-ecom-landing`
- `pub-films-landing`
- `pub-agencia-landing`
- `pub-leads`
- `pub3d-landing`
- `neural-os`
- `pubfood-control-growth`
- `pubgrowthai`
- `pubgrowth-ai-evolution`
- `pub-dev-loop`
- `pub-ecom`
- `pub-dev-loop-template`
- `pub-ops-hub`
- `pubecomhub`
- `pub-ecom-catalog-worker`
- `pub-shopee-scraper`
- `pub-github-mcp`
- `pub-dev-loop-prototypes`
- `pub-9router-cloud`
- `pub-machine`
- `pub-machine-saas`
- `pub-machine-2`
- `leadcore`
- `pub-ia`
- `pub-start`
- `pub-scrapping`
- `pub-prototype`
- `pub-neural`
- `pub-core-os`
- `pub-media`
- `pub-films`
- `pub-lancamentos`
- `pub-3d`
- `pub-imoveis`
- `pub-bnb`
- `buzios-de-cima`
- `pub-records`
- `xp-audio-lab`
- `pub-games-studio`
- `pubet`
- `pub-food`
- `pub-crypto`
- `ia-pubcrypto`
- `pub-trade`
- `pub-textil`
- `eternize-seu-pinscher`
- `pub-co`

## Consolidation Semantics

### `CANONICAL`
The repository is the owner of the canonical Neural context document.

### `CONSOLIDATED`
A Master Context has been directly inspected and its durable architectural meaning has been represented in the Neural Master Context without claiming that the source implementation was copied.

### `DISCOVERED`
The repository is known to the Neural inventory but its Master Context has not yet been directly harvested.

### `NOT_HARVESTED`
No verified Master Context has yet been retrieved. This is an ingestion state, not an existence claim.

### `CONFLICT`
Multiple sources contain incompatible claims. Preserve provenance and escalate rather than silently merging them.

## Canonical Harvest Pipeline

```text
REPOSITORY INVENTORY
        ↓
MASTER_CONTEXT DISCOVERY
        ↓
SOURCE HASH / COMMIT
        ↓
EXTRACTION
        ↓
CLASSIFICATION
        ↓
NORMALIZATION
        ↓
PROVENANCE
        ↓
CONFLICT DETECTION
        ↓
CONSOLIDATION
        ↓
NEURAL KNOWLEDGE
```

## Knowledge Categories

Each harvested context should be classified into:

- `PROJECT`
- `REPOSITORY`
- `ARCHITECTURE`
- `GOVERNANCE`
- `RULE`
- `DECISION`
- `PATTERN`
- `LESSON`
- `SKILL`
- `AGENT`
- `CONCEPT`
- `SOURCE`
- `EVIDENCE`
- `EVENT`
- `ROADMAP`
- `RUNTIME_STATE`

## Provenance Contract

Every promoted knowledge item should retain, when available:

```yaml
source:
  repository: <owner/repository>
  path: <source path>
  ref: <branch/tag/commit>
  commit: <sha>
  observed_at: <timestamp>

knowledge:
  type: <category>
  scope: <project|holding|domain>
  status: <captured|observed|extracted|candidate|validated|adopted|institutional>
  confidence: <low|medium|high>
```

## Important Isolation Rule

`PDL` and `PP / PUB Prototype` are separate projects. Neural may relate them, but must preserve `project_scope` and must never merge their implementation contexts into one runtime or governance boundary.

## Next Harvest Targets

The next harvesting pass should inspect the remaining repositories for:

1. `MASTER_CONTEXT.md`
2. `docs/PUBMASTERMEGABLASTERCONTEXT.md`
3. `README.md`
4. governance documents
5. RAG definitions and memory systems
6. skills and agent definitions
7. ADRs / decisions
8. lessons and patterns
9. tests that substantiate architectural claims
10. current runtime/deployment evidence

The final objective is not a larger documentation folder. It is a queryable organizational memory with provenance, scope, confidence and evidence.
