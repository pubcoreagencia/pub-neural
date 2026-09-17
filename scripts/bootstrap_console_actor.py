"""
PUB Neural - Out-of-band Bootstrap Script for Console Auditor/Operator Actor.
Enforces:
- Schema V0 compliance (uses existing trusted_actors table and 'AUDITOR' role).
- Zero secret hardcoding (cryptographically secure random secret generated via secrets module).
- Only SHA-256 hash stored in database.
- Secret is displayed to operator ONCE on stdout, NEVER committed to Git.
"""

import hashlib
import os
import secrets
import sys
import psycopg2


def bootstrap_console_actor():
    db_url = os.getenv("PUB_NEURAL_DB_URL")
    if not db_url:
        env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        if os.path.exists(env_file):
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith("PUB_NEURAL_DB_URL="):
                        db_url = line.strip().split("=", 1)[1].strip().strip("'\"")
                        break

    if not db_url:
        print("ERROR: PUB_NEURAL_DB_URL environment variable is required.", file=sys.stderr)
        sys.exit(1)

    actor_id = "actor:auditor:console-operator"
    actor_role = "AUDITOR"
    db_role = "postgres"  # Matches connection SESSION_USER on Supabase
    authorized_trust_zones = ["tz_internal_holding", "tz_client_facing", "tz_public"]
    authorized_projects = []  # Empty array = access to all projects under role

    # Generate 256-bit high entropy machine secret
    raw_secret = secrets.token_hex(32)
    credential_identity = hashlib.sha256(raw_secret.encode("utf-8")).hexdigest()

    conn = psycopg2.connect(db_url)
    try:
        cur = conn.cursor()

        # Find genesis event for originating_event_id FK
        cur.execute("SELECT id FROM pub_neural.neural_events ORDER BY global_sequence ASC LIMIT 1;")
        genesis_row = cur.fetchone()
        if not genesis_row:
            print("ERROR: No genesis event found in neural_events.", file=sys.stderr)
            sys.exit(1)
        originating_event_id = genesis_row[0]

        # Check if actor already exists
        cur.execute("SELECT actor_id FROM pub_neural.trusted_actors WHERE actor_id = %s;", (actor_id,))
        existing = cur.fetchone()

        if existing:
            # Update credential and ensure active
            cur.execute("""
                UPDATE pub_neural.trusted_actors
                SET credential_identity = %s,
                    is_active = TRUE,
                    db_role = %s,
                    actor_role = %s,
                    authorized_trust_zones = %s,
                    authorized_projects = %s
                WHERE actor_id = %s;
            """, (credential_identity, db_role, actor_role, authorized_trust_zones, authorized_projects, actor_id))
            action = "UPDATED"
        else:
            cur.execute("""
                INSERT INTO pub_neural.trusted_actors (
                    actor_id,
                    actor_role,
                    db_role,
                    authorized_trust_zones,
                    authorized_projects,
                    credential_identity,
                    is_active,
                    originating_event_id
                ) VALUES (%s, %s, %s, %s, %s, %s, TRUE, %s);
            """, (
                actor_id,
                actor_role,
                db_role,
                authorized_trust_zones,
                authorized_projects,
                credential_identity,
                originating_event_id
            ))
            action = "CREATED"

        conn.commit()
        print("=" * 60)
        print(f"CONSOLE ACTOR BOOTSTRAP SUCCESSFUL ({action})")
        print("=" * 60)
        print(f"ACTOR_ID:            {actor_id}")
        print(f"ACTOR_ROLE:          {actor_role}")
        print(f"TRUST_ZONES:         {authorized_trust_zones}")
        print(f"PROJECT_SCOPE:       All projects")
        print(f"DB_ROLE:             {db_role}")
        print(f"CREDENTIAL_IDENTITY: {credential_identity} (stored in DB)")
        print("-" * 60)
        print("MACHINE SECRET (SAVE THIS SECURELY - SHOWN ONCE, NEVER COMMITTED):")
        print(raw_secret)
        print("=" * 60)
    finally:
        conn.close()


if __name__ == "__main__":
    bootstrap_console_actor()
