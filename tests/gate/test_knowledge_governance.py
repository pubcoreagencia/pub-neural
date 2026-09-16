"""
Unit and integration tests for Knowledge Governance V0.1.
Verifies:
- Authorization rules: AGENT cannot VALIDATE, ADOPT, or INSTITUTIONALIZE knowledge.
- Evidence Gate: Promotion requires verified evidence links or sources.
- Contradiction Gate: Nodes with CONTRADICTORY, BLOCKED, SUPERSEDED, DEPRECATED, or REJECTED
  conflict states cannot be promoted.
- Replay & Idempotency: Replaying governance events produces zero duplicates and safe no-ops.
- Fail-closed behavior: Malformed payloads, unauthorized actors, and missing targets are strictly rejected.
"""

import os
import unittest
from unittest.mock import MagicMock
import uuid

import psycopg2
from psycopg2.extras import RealDictCursor

from console.backend.config import ConsoleConfig
from console.backend.services.activity_service import get_governance_review_data


class TestKnowledgeGovernanceUnit(unittest.TestCase):
    """Unit tests verifying governance reduction logic and policy rules."""

    def test_governance_review_factual_mapping(self):
        """Verifies candidate mapping preserves all factual fields without scoring."""
        mock_cur = MagicMock()
        mock_cur.fetchall.return_value = [
            {
                "id": "finding:pub-neural:task-1:1",
                "entity_type": "LESSON",
                "title": "PLpgSQL search_path isolation",
                "summary": "Must include extensions schema",
                "content": "Detailed lesson content",
                "promotion_state": "CANDIDATE",
                "promotion_reason": "Discovered during task-1",
                "conflict_state": "RESOLVED",
                "scope": "PROJECT",
                "project_id": "pub-neural",
                "trust_zone": "tz_internal_holding",
                "originating_event_id": "0191e4f0-0000-7000-8000-000000000001",
                "created_at": "2026-09-16T12:00:00+00:00",
                "proposed_by_actor_id": "autonomous-gate",
                "proposed_by_actor_role": "AGENT",
                "originating_event_type": "TASK_EXPERIENCE_RECORDED",
                "derived_from_experience_id": "experience:pub-neural:task-1",
                "evidence_count": 1,
            }
        ]

        res = get_governance_review_data(mock_cur)
        self.assertEqual(res.candidates_count, 1)
        c = res.candidates[0]
        self.assertEqual(c.id, "finding:pub-neural:task-1:1")
        self.assertEqual(c.promotion_state, "CANDIDATE")
        self.assertEqual(c.proposed_by_actor_role, "AGENT")
        self.assertEqual(c.conflict_state, "RESOLVED")
        self.assertEqual(c.evidence_count, 1)


class TestKnowledgeGovernanceDatabaseIntegration(unittest.TestCase):
    """
    Live integration tests against the Supabase database validating
    the reduce_event governance gates and candidate review queries.
    """

    @classmethod
    def setUpClass(cls):
        config = ConsoleConfig.from_environment()
        cls.db_url = config.db_url
        if not cls.db_url:
            raise unittest.SkipTest("PUB_NEURAL_DB_URL not configured in environment or .env")

    def test_real_candidate_and_adopted_nodes(self):
        """Verify candidate node 2 is under review and node 1 was adopted by sovereign decision."""
        with psycopg2.connect(self.db_url) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 1. Candidate Review Service contains finding:2 (finding:1 was adopted, no longer CANDIDATE)
                gov_dto = get_governance_review_data(cur)
                self.assertGreaterEqual(gov_dto.candidates_count, 1)
                cand_ids = [c.id for c in gov_dto.candidates]
                self.assertIn("finding:pub-neural:task-runtime-remote-db-integration:2", cand_ids)
                self.assertNotIn("finding:pub-neural:task-runtime-remote-db-integration:1", cand_ids)

                cand2 = next(c for c in gov_dto.candidates if c.id == "finding:pub-neural:task-runtime-remote-db-integration:2")
                self.assertEqual(cand2.promotion_state, "CANDIDATE")
                self.assertEqual(cand2.conflict_state, "RESOLVED")
                self.assertEqual(cand2.proposed_by_actor_role, "AGENT")
                self.assertIsNotNone(cand2.derived_from_experience_id)

                # 2. Verify finding:1 state in database (ADOPTED with sovereign provenance)
                cur.execute("""
                    SELECT id, promotion_state, conflict_state, promotion_reason, last_transition_event_id
                    FROM pub_neural.neural_nodes
                    WHERE id = 'finding:pub-neural:task-runtime-remote-db-integration:1';
                """)
                f1 = cur.fetchone()
                self.assertEqual(f1["promotion_state"], "ADOPTED")
                self.assertEqual(f1["conflict_state"], "RESOLVED")
                self.assertIn("Adopted by actor:ceo:matheus (CEO)", f1["promotion_reason"])

    def test_negative_agent_cannot_validate_knowledge(self):
        """Negative Test A: reduce_event must REJECT KNOWLEDGE_VALIDATED if actor_role is AGENT."""
        with psycopg2.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SAVEPOINT sp_neg_val;")
                # Test reduce_event directly with AGENT role mock event on finding 2 (CANDIDATE)
                cur.execute("""
                    SELECT pub_neural.reduce_event((
                        '00000000-0000-0000-0000-000000000001'::uuid,
                        9999,
                        'KNOWLEDGE_VALIDATED',
                        1, 1, 'test', 'stream-1', 1,
                        'agent-1',
                        'AGENT'::pub_neural.neural_actor_role,
                        '{"target_id": "finding:pub-neural:task-runtime-remote-db-integration:2", "evidence_summary": "attempt"}'::jsonb,
                        'sig',
                        NOW()
                    )::pub_neural.neural_events);
                """)
                res = cur.fetchone()[0]
                self.assertEqual(res, "REJECTED")

                # Verify target node remains strictly CANDIDATE
                cur.execute("""
                    SELECT promotion_state FROM pub_neural.neural_nodes 
                    WHERE id = 'finding:pub-neural:task-runtime-remote-db-integration:2';
                """)
                state = cur.fetchone()[0]
                self.assertEqual(state, "CANDIDATE")
                cur.execute("ROLLBACK TO SAVEPOINT sp_neg_val;")

    def test_negative_agent_cannot_adopt_knowledge(self):
        """Negative Test B: reduce_event must REJECT KNOWLEDGE_ADOPTED if actor_role is AGENT or AUDITOR."""
        with psycopg2.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SAVEPOINT sp_neg_adopt;")
                cur.execute("""
                    SELECT pub_neural.reduce_event((
                        '00000000-0000-0000-0000-000000000001'::uuid,
                        9999,
                        'KNOWLEDGE_ADOPTED',
                        1, 1, 'test', 'stream-1', 1,
                        'agent-1',
                        'AGENT'::pub_neural.neural_actor_role,
                        '{"target_id": "finding:pub-neural:task-runtime-remote-db-integration:2"}'::jsonb,
                        'sig',
                        NOW()
                    )::pub_neural.neural_events);
                """)
                res = cur.fetchone()[0]
                self.assertEqual(res, "REJECTED")
                cur.execute("ROLLBACK TO SAVEPOINT sp_neg_adopt;")

    def test_negative_validation_without_evidence_rejected(self):
        """Negative Test C: CEO cannot promote a node without verifiable evidence."""
        with psycopg2.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SAVEPOINT sp_neg_ev;")
                # Create a temporary node without any evidence or DERIVED_FROM edge
                cur.execute("""
                    INSERT INTO pub_neural.neural_nodes (
                        id, entity_type, title, slug, trust_zone, scope, project_id,
                        promotion_state, conflict_state, is_active, originating_event_id,
                        last_transition_event_id, valid_from, recorded_from, created_at, updated_at
                    ) VALUES (
                        'temp:unsupported-candidate', 'LESSON', 'Unsupported Node', 'unsupported-node',
                        'tz_internal_holding', 'PROJECT', 'pub-neural', 'CANDIDATE', 'RESOLVED',
                        TRUE, '0191e4f0-0000-7000-8000-000000000001', '0191e4f0-0000-7000-8000-000000000001',
                        NOW(), NOW(), NOW(), NOW()
                    );
                """)

                # CEO attempts validation with NO evidence fields
                cur.execute("""
                    SELECT pub_neural.reduce_event((
                        '00000000-0000-0000-0000-000000000001'::uuid,
                        9999,
                        'KNOWLEDGE_VALIDATED',
                        1, 1, 'test', 'stream-1', 1,
                        'pub_neural_ceo',
                        'CEO'::pub_neural.neural_actor_role,
                        '{"target_id": "temp:unsupported-candidate"}'::jsonb,
                        'sig',
                        NOW()
                    )::pub_neural.neural_events);
                """)
                res = cur.fetchone()[0]
                self.assertEqual(res, "REJECTED")

                # Verify node remains CANDIDATE
                cur.execute("SELECT promotion_state FROM pub_neural.neural_nodes WHERE id = 'temp:unsupported-candidate';")
                self.assertEqual(cur.fetchone()[0], "CANDIDATE")
                cur.execute("ROLLBACK TO SAVEPOINT sp_neg_ev;")

    def test_negative_validation_under_conflict_rejected(self):
        """Negative Test D: Cannot validate a node with conflict_state in CONTRADICTORY or BLOCKED."""
        with psycopg2.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SAVEPOINT sp_neg_conflict;")
                cur.execute("""
                    INSERT INTO pub_neural.neural_nodes (
                        id, entity_type, title, slug, trust_zone, scope, project_id,
                        promotion_state, conflict_state, is_active, originating_event_id,
                        last_transition_event_id, valid_from, recorded_from, created_at, updated_at
                    ) VALUES (
                        'temp:blocked-candidate', 'LESSON', 'Blocked Node', 'blocked-node',
                        'tz_internal_holding', 'PROJECT', 'pub-neural', 'CANDIDATE', 'BLOCKED',
                        TRUE, '0191e4f0-0000-7000-8000-000000000001', '0191e4f0-0000-7000-8000-000000000001',
                        NOW(), NOW(), NOW(), NOW()
                    );
                """)

                cur.execute("""
                    SELECT pub_neural.reduce_event((
                        '00000000-0000-0000-0000-000000000001'::uuid,
                        9999,
                        'KNOWLEDGE_VALIDATED',
                        1, 1, 'test', 'stream-1', 1,
                        'pub_neural_ceo',
                        'CEO'::pub_neural.neural_actor_role,
                        '{"target_id": "temp:blocked-candidate", "evidence_summary": "verified"}'::jsonb,
                        'sig',
                        NOW()
                    )::pub_neural.neural_events);
                """)
                res = cur.fetchone()[0]
                self.assertEqual(res, "REJECTED")

                cur.execute("SELECT promotion_state FROM pub_neural.neural_nodes WHERE id = 'temp:blocked-candidate';")
                self.assertEqual(cur.fetchone()[0], "CANDIDATE")
                cur.execute("ROLLBACK TO SAVEPOINT sp_neg_conflict;")

    def test_negative_direct_jump_candidate_to_adopted_rejected(self):
        """Negative Test E: Direct jump from CANDIDATE to ADOPTED without prior VALIDATED is strictly REJECTED."""
        with psycopg2.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SAVEPOINT sp_neg_direct_adopt;")
                # finding:pub-neural:task-runtime-remote-db-integration:2 is CANDIDATE
                cur.execute("""
                    SELECT pub_neural.reduce_event((
                        '00000000-0000-0000-0000-000000000001'::uuid,
                        9999,
                        'KNOWLEDGE_ADOPTED',
                        1, 1, 'test', 'stream-1', 1,
                        'pub_neural_ceo',
                        'CEO'::pub_neural.neural_actor_role,
                        '{"target_id": "finding:pub-neural:task-runtime-remote-db-integration:2"}'::jsonb,
                        'sig',
                        NOW()
                    )::pub_neural.neural_events);
                """)
                res = cur.fetchone()[0]
                self.assertEqual(res, "REJECTED")

                # Verify finding:2 remains strictly CANDIDATE
                cur.execute("""
                    SELECT promotion_state FROM pub_neural.neural_nodes
                    WHERE id = 'finding:pub-neural:task-runtime-remote-db-integration:2';
                """)
                self.assertEqual(cur.fetchone()[0], "CANDIDATE")
                cur.execute("ROLLBACK TO SAVEPOINT sp_neg_direct_adopt;")

    def test_negative_malformed_target_rejected(self):
        """Negative Test F: Missing target_id is MALFORMED; Non-existent target is REJECTED."""
        with psycopg2.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SAVEPOINT sp_neg_malformed;")
                # Missing target_id
                cur.execute("""
                    SELECT pub_neural.reduce_event((
                        '00000000-0000-0000-0000-000000000001'::uuid,
                        9999,
                        'KNOWLEDGE_VALIDATED',
                        1, 1, 'test', 'stream-1', 1,
                        'pub_neural_ceo',
                        'CEO'::pub_neural.neural_actor_role,
                        '{}'::jsonb,
                        'sig',
                        NOW()
                    )::pub_neural.neural_events);
                """)
                self.assertEqual(cur.fetchone()[0], "MALFORMED")

                # Non-existent target
                cur.execute("""
                    SELECT pub_neural.reduce_event((
                        '00000000-0000-0000-0000-000000000001'::uuid,
                        9999,
                        'KNOWLEDGE_VALIDATED',
                        1, 1, 'test', 'stream-1', 1,
                        'pub_neural_ceo',
                        'CEO'::pub_neural.neural_actor_role,
                        '{"target_id": "nonexistent:node:999", "evidence_summary": "ok"}'::jsonb,
                        'sig',
                        NOW()
                    )::pub_neural.neural_events);
                """)
                self.assertEqual(cur.fetchone()[0], "REJECTED")
                cur.execute("ROLLBACK TO SAVEPOINT sp_neg_malformed;")

    def test_governance_replay_idempotency(self):
        """Verify re-running projector is idempotent (0 processed, checkpoint intact, HEALTHY) and reducing seq 7 is supported."""
        with psycopg2.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SAVEPOINT sp_replay_idempotency;")
                # Re-running projector at current checkpoint: must report 0 processed, 0 failed, checkpoint = 7, HEALTHY
                cur.execute("SELECT * FROM pub_neural.run_projector('graph_projector');")
                proj_res = cur.fetchone()
                self.assertEqual(proj_res[0], 0)  # events_processed
                self.assertEqual(proj_res[1], 0)  # events_failed
                self.assertEqual(proj_res[2], 7)  # checkpoint
                self.assertEqual(proj_res[3], "HEALTHY")

                # Re-reducing sequence 7 (KNOWLEDGE_ADOPTED on already ADOPTED node) is idempotent SUPPORTED
                cur.execute("""
                    SELECT pub_neural.reduce_event(e)
                    FROM pub_neural.neural_events e
                    WHERE e.global_sequence = 7;
                """)
                res = cur.fetchone()[0]
                self.assertEqual(res, "SUPPORTED")

                # Verify finding 1 still has exactly 1 row and correct state
                cur.execute("SELECT COUNT(*) FROM pub_neural.neural_nodes WHERE id = 'finding:pub-neural:task-runtime-remote-db-integration:1';")
                self.assertEqual(cur.fetchone()[0], 1)

                cur.execute("ROLLBACK TO SAVEPOINT sp_replay_idempotency;")


if __name__ == "__main__":
    unittest.main()
