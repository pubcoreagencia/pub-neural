# PUB Crypto Validation Ingestion Contract V0

## Status

The concrete runtime path has now been verified in PUB Neural source.

## Verified runtime path

PUB Crypto must use a database connection with an active PUB Neural trusted actor and execute the following calls **inside one transaction**:

1. `pub_neural.establish_session_context(actor_id, machine_secret, trust_zone, project_id)`
2. `pub_neural.attach_session(bearer_token)`
3. `pub_neural.append_event(... event_type = 'TRADING_VALIDATION' ...)`
4. insert/check `pub_neural.neural_idempotency_records`

The single-transaction requirement is material because `attach_session` stores the bearer-session hash in a transaction-local setting used by `append_event`.

## Payload lineage

Every `TRADING_VALIDATION` event from PUB Crypto must preserve:

- source repository: `pubcoreagencia/pub-crypto`;
- source commit;
- strategy version;
- dataset version;
- observation timestamp;
- validation status;
- trade count;
- regime attribution;
- Monte Carlo summary when present;
- producer version.

The event is evidence. It is not automatically an institutional lesson, rule, skill, decision, or live-trading authorization.

## Idempotency

The canonical idempotency key is:

`trading_validation:pubcoreagencia/pub-crypto:<sourceCommit>:<strategyVersion>:<datasetVersion>`

The event ID is deterministically derived from this key.

Retries must:

1. check `neural_idempotency_records`;
2. check the deterministic event ID;
3. replay the existing event instead of appending a duplicate;
4. record the idempotency result if an event already exists but its idempotency record is missing.

## Authority prerequisite

The runtime actor must be an active PUB Neural `trusted_actor` compatible with `pub_neural_app`, with:

- actor role authorized to append `TRADING_VALIDATION` events;
- `tz_internal_holding` authorization;
- `pub-crypto` project clearance when project-scoped;
- machine secret provisioned out-of-band.

The repository source confirms that `TRADING_VALIDATION` itself is not a privileged event type. The actor/session authorization remains the security boundary.

## Fail-closed rules

Reject before database access when:

1. source commit is missing or invalid;
2. artifact source is not `PUB_CRYPTO`;
3. strategy version is missing;
4. dataset version is missing.

Reject at the database boundary when the actor, trust zone, project, or machine secret is not authorized.

## Promotion boundary

`CAPTURED → OBSERVED → EXTRACTED → CANDIDATE → VALIDATED → ADOPTED → INSTITUTIONAL`

PUB Crypto produces validation evidence.

PUB Neural owns knowledge promotion.

## Security

No exchange credentials, private keys, machine secrets, or real-capital authorization belong in Git, artifacts, prompts, or logs.

## Current state

The PUB Crypto adapter now targets this verified contract.

Actual production persistence still requires a provisioned trusted actor and a reachable PUB Neural PostgreSQL runtime. Code publication alone does not claim a live database write.


## Live proof status — 2026-09-17

The live PUB Neural Supabase project was inspected directly. The `pub-crypto` holding project exists and is active.

A direct disposable actor registration was rejected because `trusted_actors.originating_event_id` is NOT NULL. This confirms the database enforces the governed actor-registration boundary instead of allowing an unanchored INGESTOR identity to be created.

No test `TRADING_VALIDATION` event was persisted. The event count remains unchanged at 39 and `neural_idempotency_records` remains at 0.

The graph projector reports HEALTHY but its checkpoint is global sequence 7. No PUB Crypto validation event has therefore been observed by the projector yet.

The next production-grade gate is a governed actor-registration event followed by out-of-band machine-secret provisioning. Do not bypass this with a direct `trusted_actors` insert.


## Projector gate result — 2026-09-17

A live projector execution was attempted for `graph_projector`, sequences 8 through 39. The projector remained at sequence 7 and transitioned to `STALLED` on sequence 8 with `MALFORMED`.

Sequence 8 is a legacy `REPOSITORY_OBSERVED` event whose payload shape does not satisfy the current reducer contract. The reducer requires `provenance.delivery_id`, `provenance.payload_hash`, and nested payload fields, while sequence 8 stores those observation fields in the event payload at the top level. This blocks the graph projector before any PUB Crypto event can be consumed.

This is a PUB Neural ingestion/projector contract issue, not a PUB Crypto validation issue. It must be corrected or explicitly migrated before the first PUB Crypto E2E projection proof.


## PUB Neural Repair Proof — 2026-09-17

The legacy `REPOSITORY_OBSERVED` contract was repaired at the reducer boundary without mutating the append-only `neural_events` log.

Repair:

- legacy top-level `delivery_id`, `ref`, `sha`, and `details` are normalized in-memory into the canonical `provenance` + `payload` shape;
- when a legacy event has no source payload hash, the reducer derives a deterministic SHA-256 hash from the immutable event payload;
- existing projection hashes are preserved on replay;
- malformed events that lack the minimum repository/project/delivery contract remain rejected;
- the event log itself is not rewritten.

Live proof against the PUB Neural Supabase project:

- replay range: global sequence `8 → 39`;
- events processed: `32`;
- events failed: `0`;
- projector: `HEALTHY`;
- checkpoint: global sequence `39`;
- `neural_repository_observations`: `33` rows / `33` distinct event IDs;
- missing repository observation projections: `0`;
- `neural_events`: `39` rows;
- `neural_idempotency_records`: `0` rows;
- trusted actors: `2`, unchanged;
- second projector run: `0` events processed, `0` failed, checkpoint remained `39`.

The PUB Crypto gate remains closed. No `TRADING_VALIDATION` event was created by this repair.
