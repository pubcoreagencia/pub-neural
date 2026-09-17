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
