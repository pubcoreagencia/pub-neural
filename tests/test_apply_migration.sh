#!/usr/bin/env bash
set -e

# Generate a high-entropy secret for CEO bootstrap testing
CEO_RAW_SECRET="sovereign_pub_neural_test_secret_$(date +%s)"
CEO_CRED_HASH=$(echo -n "$CEO_RAW_SECRET" | sha256sum | awk '{print $1}')

echo "CEO_CRED_HASH: $CEO_CRED_HASH"

# Apply clean migration with CEO credential hash set in session
docker exec -i pub_neural_test_runner psql -U postgres -v ON_ERROR_STOP=1 << SQL
DROP SCHEMA IF EXISTS pub_neural CASCADE;
SET pub_neural.bootstrap_ceo_credential_hash = '$CEO_CRED_HASH';
\i migrations/0001_initial_v0_schema.sql
SQL

echo "MIGRATION_APPLIED_SUCCESSFULLY"
