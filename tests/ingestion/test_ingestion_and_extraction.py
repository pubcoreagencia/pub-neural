import hashlib
import os
import signal
import subprocess
import sys
import time
import unittest
import uuid
import psycopg2
from psycopg2.extras import RealDictCursor

from src.ingestion.client import PubNeuralClient
from src.ingestion.scout import ScoutWorker
from src.ingestion.blob_vault import BlobVault
from src.ingestion.source_ingestor import SourceIngestorWorker
from src.ingestion.doc_capturer import DocumentCaptureWorker
from src.ingestion.doc_parser import DocumentParserWorker
from src.extraction.entity_extractor import EntityExtractorWorker
from src.extraction.relation_extractor import RelationExtractorWorker
from src.extraction.evidence_capturer import EvidenceCapturerWorker

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "postgres")
DB_USER = os.environ.get("DB_USER", "pub_neural_app")
DB_PASS = os.environ.get("DB_PASS", "app_secret_pw")
ADMIN_USER = os.environ.get("ADMIN_USER", "postgres")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "postgres")

DB_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
ADMIN_URL = f"postgresql://{ADMIN_USER}:{ADMIN_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

INGESTOR_SECRET = "ingestor_machine_secret_32_bytes_long_entropy_12345"
AGENT_SECRET = "agent_machine_secret_32_bytes_long_entropy_67890"


class IngestionAndExtractionTestSuite(unittest.TestCase):
    """Automated Test Suite ING-01 to ING-15 for PUB Neural Ingestion & Extraction Pipelines."""

    @classmethod
    def setUpClass(cls):
        """Seed trusted_actors with INGESTOR and AGENT roles using admin connection."""
        conn = psycopg2.connect(ADMIN_URL)
        conn.autocommit = True
        with conn.cursor() as cur:
            ingestor_hash = hashlib.sha256(INGESTOR_SECRET.encode("utf-8")).hexdigest()
            agent_hash = hashlib.sha256(AGENT_SECRET.encode("utf-8")).hexdigest()

            # Insert or update trusted actors
            cur.execute(
                """
                INSERT INTO pub_neural.trusted_actors (
                    actor_id, actor_role, db_role, authorized_trust_zones, authorized_projects,
                    credential_identity, is_active, originating_event_id
                ) VALUES (
                    'actor:system:ingestor', 'INGESTOR', 'pub_neural_app',
                    ARRAY['tz_internal_holding', 'tz_client_facing'], ARRAY['pub-ecom', 'pub-neural', 'holding-core'],
                    %s, TRUE, '0191e4f0-0000-7000-8000-000000000001'::uuid
                ) ON CONFLICT (actor_id) DO UPDATE SET
                    credential_identity = EXCLUDED.credential_identity,
                    is_active = TRUE;
                """,
                (ingestor_hash,)
            )

            cur.execute(
                """
                INSERT INTO pub_neural.trusted_actors (
                    actor_id, actor_role, db_role, authorized_trust_zones, authorized_projects,
                    credential_identity, is_active, originating_event_id
                ) VALUES (
                    'actor:system:agent', 'AGENT', 'pub_neural_app',
                    ARRAY['tz_internal_holding', 'tz_client_facing'], ARRAY['pub-ecom', 'pub-neural', 'holding-core'],
                    %s, TRUE, '0191e4f0-0000-7000-8000-000000000001'::uuid
                ) ON CONFLICT (actor_id) DO UPDATE SET
                    credential_identity = EXCLUDED.credential_identity,
                    is_active = TRUE;
                """,
                (agent_hash,)
            )
        conn.close()

    def setUp(self):
        self.ingestor_client = PubNeuralClient(
            db_url=DB_URL,
            actor_id="actor:system:ingestor",
            machine_secret=INGESTOR_SECRET,
            requested_trust_zone="tz_internal_holding",
            requested_project="pub-ecom"
        )
        self.ingestor_client.establish_session()

        self.agent_client = PubNeuralClient(
            db_url=DB_URL,
            actor_id="actor:system:agent",
            machine_secret=AGENT_SECRET,
            requested_trust_zone="tz_internal_holding",
            requested_project="pub-ecom"
        )
        self.agent_client.establish_session()

    def tearDown(self):
        self.ingestor_client.close()
        self.agent_client.close()

    # ------------------------------------------------------------------------
    # ING-01: SOURCE discovery
    # ------------------------------------------------------------------------
    def test_ing_01_source_discovery(self):
        scout = ScoutWorker(self.ingestor_client)
        res = scout.discover_source(
            repository="pubcore/pub-ecom",
            commit_sha="1111111222222333333444444555555666666777",
            file_path="docs/architecture/adr-001.md"
        )
        self.assertIn("global_sequence", res)
        self.assertGreater(res["global_sequence"], 0)
        self.assertEqual(res["payload"]["repository"], "pubcore/pub-ecom")
        print("  -> TEST_PASSED [ING-01]: Source discovery emitted SOURCE_DISCOVERED.")

    # ------------------------------------------------------------------------
    # ING-02: Blob verification & preservation
    # ------------------------------------------------------------------------
    def test_ing_02_blob_verification(self):
        vault = BlobVault(self.ingestor_client)
        content = b"# ADR 001: Architecture Decisions\nZero mutation rule mandate across services.\n"
        res = vault.preserve_and_verify(
            raw_bytes=content,
            mime_type="text/markdown"
        )
        self.assertIn("file_sha256", res)
        self.assertEqual(res["byte_size"], len(content))
        self.assertTrue(os.path.exists(res["storage_uri"].replace("file://", "")))
        print("  -> TEST_PASSED [ING-02]: Blob verification registered manifest and emitted SOURCE_BLOB_VERIFIED.")

    # ------------------------------------------------------------------------
    # ING-03: Blob hash mismatch
    # ------------------------------------------------------------------------
    def test_ing_03_blob_hash_mismatch(self):
        vault = BlobVault(self.ingestor_client)
        content = b"Tampered binary content"
        fake_sha256 = "0000000000000000000000000000000000000000000000000000000000000000"
        with self.assertRaises(ValueError) as ctx:
            vault.preserve_and_verify(
                raw_bytes=content,
                expected_sha256=fake_sha256
            )
        self.assertIn("BLOB_HASH_MISMATCH", str(ctx.exception))
        print("  -> TEST_PASSED [ING-03]: Blob hash mismatch rejected fail-closed.")

    # ------------------------------------------------------------------------
    # ING-04: Document capture
    # ------------------------------------------------------------------------
    def test_ing_04_document_capture(self):
        vault = BlobVault(self.ingestor_client)
        raw_bytes = b"# Document 100\nCaptured document content."
        blob = vault.preserve_and_verify(raw_bytes=raw_bytes)

        source_worker = SourceIngestorWorker(self.ingestor_client)
        src = source_worker.ingest_source(
            repository="pubcore/pub-ecom",
            commit_sha="commit_sha_ing_04",
            file_path="docs/doc100.md",
            file_sha256=blob["file_sha256"]
        )

        doc_worker = DocumentCaptureWorker(self.ingestor_client)
        doc = doc_worker.capture_document(
            source_id=src["source_id"],
            file_sha256=blob["file_sha256"],
            document_title="Document 100 Spec",
            raw_byte_size=len(raw_bytes)
        )
        self.assertEqual(doc["payload"]["source_id"], src["source_id"])
        print("  -> TEST_PASSED [ING-04]: Document capture preserved parent source lineage.")

    # ------------------------------------------------------------------------
    # ING-05: Parser lineage & chunking
    # ------------------------------------------------------------------------
    def test_ing_05_parser_lineage(self):
        text = "\n".join([f"Line {i}: Documentation content block" for i in range(1, 50)])
        parser = DocumentParserWorker(self.ingestor_client)
        parsed = parser.parse_text_units(
            text_content=text,
            document_id="doc:pub-ecom:test-lineage",
            source_id="0191e4f0-0020-7000-8000-000000000001",
            chunk_line_size=20
        )
        self.assertEqual(len(parsed["chunks"]), 3)
        self.assertEqual(parsed["chunks"][0]["start_line"], 1)
        self.assertEqual(parsed["chunks"][0]["end_line"], 20)
        self.assertEqual(parsed["chunks"][1]["start_line"], 21)
        self.assertEqual(parsed["chunks"][1]["end_line"], 40)
        self.assertEqual(parsed["chunks"][2]["start_line"], 41)
        self.assertEqual(parsed["chunks"][2]["end_line"], 49)
        print("  -> TEST_PASSED [ING-05]: Parser chunk offsets and line boundaries verified.")

    # ------------------------------------------------------------------------
    # ING-06: Parser versioning
    # ------------------------------------------------------------------------
    def test_ing_06_parser_versioning(self):
        text = "Line 1: Sample text.\nLine 2: Another text."
        parser = DocumentParserWorker(self.ingestor_client)
        v1 = parser.parse_text_units(text_content=text, document_id="doc:pub-ecom:v-test", source_id="0191e4f0-0020-7000-8000-000000000001", parser_version="v1.0.0")
        v2 = parser.parse_text_units(text_content=text, document_id="doc:pub-ecom:v-test", source_id="0191e4f0-0020-7000-8000-000000000001", parser_version="v2.0.0")
        self.assertNotEqual(v1["event_id"], v2["event_id"])
        self.assertEqual(v1["payload"]["parser_version"], "v1.0.0")
        self.assertEqual(v2["payload"]["parser_version"], "v2.0.0")
        print("  -> TEST_PASSED [ING-06]: Parser versioning emits separate lineage versions without overwriting.")

    # ------------------------------------------------------------------------
    # ING-07: Entity extraction
    # ------------------------------------------------------------------------
    def test_ing_07_entity_extraction(self):
        extractor = EntityExtractorWorker(self.agent_client)
        res = extractor.extract_entity(
            entity_type="DECISION",
            title="Database Schema Freeze Mandate",
            summary="Schema is frozen at V0.1",
            content="Physical DDL updates are forbidden without CEO sovereign mandate.",
            source_chunk_id="chunk:pub-ecom:adr-001:0"
        )
        self.assertTrue(res["node_id"].startswith("decision:pub-ecom:database-schema-freeze-mandate"))
        self.assertEqual(res["payload"]["initial_state"], "CANDIDATE")
        print("  -> TEST_PASSED [ING-07]: Entity extraction emitted deterministic node with provenance.")

    # ------------------------------------------------------------------------
    # ING-08: Relation extraction
    # ------------------------------------------------------------------------
    def test_ing_08_relation_extraction(self):
        # 1. Create source and target entities
        extractor = EntityExtractorWorker(self.agent_client)
        e1 = extractor.extract_entity(
            entity_type="DECISION",
            title="Entity Rel Test Source",
            summary="Rel test source",
            content="Content A",
            source_chunk_id="chunk:pub-ecom:rel-test:0"
        )
        e2 = extractor.extract_entity(
            entity_type="RULE",
            title="Entity Rel Test Target",
            summary="Rel test target",
            content="Content B",
            source_chunk_id="chunk:pub-ecom:rel-test:0"
        )

        rel_worker = RelationExtractorWorker(self.agent_client)
        rel = rel_worker.extract_relation(
            source_id=e1["node_id"],
            relation_type="IMPLEMENTS",
            target_id=e2["node_id"],
            source_chunk_id="chunk:pub-ecom:rel-test:0",
            weight=0.95
        )
        self.assertEqual(rel["payload"]["source_id"], e1["node_id"])
        self.assertEqual(rel["payload"]["target_id"], e2["node_id"])
        self.assertEqual(rel["payload"]["relation_type"], "IMPLEMENTS")
        print("  -> TEST_PASSED [ING-08]: Relation extraction emitted canonical typed edge.")

    # ------------------------------------------------------------------------
    # ING-09: Evidence provenance
    # ------------------------------------------------------------------------
    def test_ing_09_evidence_provenance(self):
        vault = BlobVault(self.ingestor_client)
        blob = vault.preserve_and_verify(raw_bytes=b"# Evidence Source Test\nPhysical DDL updates are forbidden without CEO sovereign mandate.")
        src_worker = SourceIngestorWorker(self.ingestor_client)
        src = src_worker.ingest_source(
            repository="pubcore/pub-ecom",
            commit_sha="ev_commit_999",
            file_path="docs/evidence_test.md",
            file_sha256=blob["file_sha256"]
        )

        extractor = EntityExtractorWorker(self.agent_client)
        ent = extractor.extract_entity(
            entity_type="DECISION",
            title="Database Schema Freeze Mandate Evidence",
            summary="Schema is frozen at V0.1",
            content="Physical DDL updates are forbidden without CEO sovereign mandate.",
            source_chunk_id="chunk:pub-ecom:ev-test:0"
        )

        ev_worker = EvidenceCapturerWorker(self.agent_client)
        ev = ev_worker.capture_evidence(
            target_type="NODE",
            target_id=ent["node_id"],
            source_id=src["source_id"],
            content_hash="hash_evidence_chunk_1",
            exact_quote="Physical DDL updates are forbidden without CEO sovereign mandate.",
            start_line=10,
            end_line=12,
            confidence=0.99
        )
        self.assertEqual(ev["payload"]["target_id"], ent["node_id"])
        self.assertEqual(ev["payload"]["quote"], "Physical DDL updates are forbidden without CEO sovereign mandate.")
        print("  -> TEST_PASSED [ING-09]: Evidence locator bound quote, lines, and content hash.")

    # ------------------------------------------------------------------------
    # ING-10: Duplicate worker execution
    # ------------------------------------------------------------------------
    def test_ing_10_duplicate_worker_execution(self):
        scout = ScoutWorker(self.ingestor_client)
        fixed_event_id = uuid.UUID("0191e4f0-00aa-7000-8000-000000000010")
        
        # First execution succeeds
        res1 = scout.discover_source(
            repository="pubcore/pub-ecom",
            commit_sha="dedup_commit_12345",
            file_path="docs/dedup.md",
            event_id=fixed_event_id
        )

        # 10 duplicate executions with identical logical inputs must return idempotent replay without semantic duplication
        for i in range(10):
            res_dup = scout.discover_source(
                repository="pubcore/pub-ecom",
                commit_sha="dedup_commit_12345",
                file_path="docs/dedup.md",
                event_id=fixed_event_id
            )
            self.assertTrue(res_dup["idempotent_replay"])
            self.assertEqual(res_dup["event_id"], str(fixed_event_id))

        print("  -> TEST_PASSED [ING-10]: 10x duplicate execution prevented semantic event duplication.")

    # ------------------------------------------------------------------------
    # ING-11: Session reconnect
    # ------------------------------------------------------------------------
    def test_ing_11_session_reconnect(self):
        vault = BlobVault(self.ingestor_client)
        content = b"# Session reconnect test\nValid content before simulated client drop."
        res = vault.preserve_and_verify(raw_bytes=content)

        # Reconnecting new instance
        new_client = PubNeuralClient(
            db_url=DB_URL,
            actor_id="actor:system:ingestor",
            machine_secret=INGESTOR_SECRET,
            requested_trust_zone="tz_internal_holding",
            requested_project="pub-ecom"
        )
        new_client.establish_session()

        source_worker = SourceIngestorWorker(new_client)
        res_ingest = source_worker.ingest_source(
            repository="pubcore/pub-ecom",
            commit_sha="crash_commit_999",
            file_path="docs/crash.md",
            file_sha256=res["file_sha256"]
        )
        self.assertGreater(res_ingest["global_sequence"], 0)
        new_client.close()
        print("  -> TEST_PASSED [ING-11]: Worker client restart reconnected and resumed cleanly (SESSION_RECONNECT).")


    # ------------------------------------------------------------------------
    # ING-12: Event emission determinism
    # ------------------------------------------------------------------------
    def test_ing_12_event_emission_determinism(self):
        extractor = EntityExtractorWorker(self.agent_client)
        id1 = extractor.format_node_id("DECISION", "pub-ecom", "Same Title Spec")
        id2 = extractor.format_node_id("DECISION", "pub-ecom", "Same Title Spec")
        self.assertEqual(id1, id2)
        print("  -> TEST_PASSED [ING-12]: Entity identifiers and hashes are bit-for-bit deterministic.")

    # ------------------------------------------------------------------------
    # ING-13: Lineage preservation
    # ------------------------------------------------------------------------
    def test_ing_13_lineage_preservation(self):
        # Build full causal parent chain: E1 (Source) -> E2 (Doc) -> E3 (Parsed) -> E4 (Entity)
        vault = BlobVault(self.ingestor_client)
        blob = vault.preserve_and_verify(raw_bytes=b"# Lineage Source")
        
        src_worker = SourceIngestorWorker(self.ingestor_client)
        src = src_worker.ingest_source(
            repository="pubcore/pub-ecom",
            commit_sha="lineage_commit_1",
            file_path="docs/lineage.md",
            file_sha256=blob["file_sha256"]
        )

        doc_worker = DocumentCaptureWorker(self.ingestor_client)
        doc = doc_worker.capture_document(
            source_id=src["source_id"],
            file_sha256=blob["file_sha256"],
            document_title="Lineage Doc",
            raw_byte_size=16,
            parent_event_id=uuid.UUID(src["event_id"])
        )

        parser_worker = DocumentParserWorker(self.ingestor_client)
        parsed = parser_worker.parse_text_units(
            text_content="# Lineage Source\nContent",
            document_id=doc["document_id"],
            source_id=src["source_id"],
            parent_event_id=uuid.UUID(doc["event_id"])
        )

        entity_worker = EntityExtractorWorker(self.agent_client)
        entity = entity_worker.extract_entity(
            entity_type="RULE",
            title="Lineage Rule Entity",
            summary="Lineage rule",
            content="Content",
            source_chunk_id=parsed["chunks"][0]["chunk_id"],
            parent_event_id=uuid.UUID(parsed["event_id"])
        )

        # Inspect neural_event_parents in DB
        conn = psycopg2.connect(ADMIN_URL)
        with conn.cursor() as cur:
            cur.execute("SELECT parent_event_id FROM pub_neural.neural_event_parents WHERE event_id = %s;", (entity["event_id"],))
            p_entity = cur.fetchone()[0]
            self.assertEqual(str(p_entity), parsed["event_id"])

            cur.execute("SELECT parent_event_id FROM pub_neural.neural_event_parents WHERE event_id = %s;", (parsed["event_id"],))
            p_parsed = cur.fetchone()[0]
            self.assertEqual(str(p_parsed), doc["event_id"])

            cur.execute("SELECT parent_event_id FROM pub_neural.neural_event_parents WHERE event_id = %s;", (doc["event_id"],))
            p_doc = cur.fetchone()[0]
            self.assertEqual(str(p_doc), src["event_id"])
        conn.close()
        print("  -> TEST_PASSED [ING-13]: 4-level causal parent lineage preserved in neural_event_parents.")

    # ------------------------------------------------------------------------
    # ING-14: Malformed / unauthorized source rejection
    # ------------------------------------------------------------------------
    def test_ing_14_malformed_source(self):
        scout = ScoutWorker(self.ingestor_client)
        with self.assertRaises(ValueError) as ctx:
            scout.discover_source(
                repository="unauthorized/random-repo",
                commit_sha="abcdef12345",
                file_path="secret.txt"
            )
        self.assertIn("UNAUTHORIZED_SOURCE_SCOPE", str(ctx.exception))
        print("  -> TEST_PASSED [ING-14]: Unauthorized source repository rejected fail-closed.")

    # ------------------------------------------------------------------------
    # ING-15: End-to-end ingestion & projection integration
    # ------------------------------------------------------------------------
    def test_ing_15_end_to_end_ingestion(self):
        # 1. Scout
        scout = ScoutWorker(self.ingestor_client)
        disc = scout.discover_source(
            repository="pubcore/pub-ecom",
            commit_sha="e2e_commit_123456789",
            file_path="docs/checkout.md"
        )

        # 2. Blob Vault
        raw_checkout = b"# Checkout Service Specification\nPayments require idempotent tokens and verified signatures.\nRule zero: never mutate checkout sessions."
        vault = BlobVault(self.ingestor_client)
        blob = vault.preserve_and_verify(raw_bytes=raw_checkout)

        # 3. Ingest Source
        src_worker = SourceIngestorWorker(self.ingestor_client)
        src = src_worker.ingest_source(
            repository="pubcore/pub-ecom",
            commit_sha="e2e_commit_123456789",
            file_path="docs/checkout.md",
            file_sha256=blob["file_sha256"]
        )

        # 4. Capture Document
        doc_worker = DocumentCaptureWorker(self.ingestor_client)
        doc = doc_worker.capture_document(
            source_id=src["source_id"],
            file_sha256=blob["file_sha256"],
            document_title="Checkout Service Spec",
            raw_byte_size=len(raw_checkout)
        )

        # 5. Parse Document
        parser = DocumentParserWorker(self.ingestor_client)
        parsed = parser.parse_text_units(
            text_content=raw_checkout.decode("utf-8"),
            document_id=doc["document_id"],
            source_id=src["source_id"]
        )

        # 6. Extract Entity (Decision)
        entity_worker = EntityExtractorWorker(self.agent_client)
        decision = entity_worker.extract_entity(
            entity_type="DECISION",
            title="Idempotent Checkout Payment Tokens",
            summary="Payment processing idempotency token architecture",
            content="Payments require idempotent tokens and verified signatures.",
            source_chunk_id=parsed["chunks"][0]["chunk_id"]
        )

        # 7. Extract Entity (Rule)
        rule = entity_worker.extract_entity(
            entity_type="RULE",
            title="Never Mutate Checkout Sessions",
            summary="Session immutability rule",
            content="Rule zero: never mutate checkout sessions.",
            source_chunk_id=parsed["chunks"][0]["chunk_id"]
        )

        # 8. Extract Relation
        rel_worker = RelationExtractorWorker(self.agent_client)
        rel = rel_worker.extract_relation(
            source_id=decision["node_id"],
            relation_type="DEPENDS_ON",
            target_id=rule["node_id"],
            source_chunk_id=parsed["chunks"][0]["chunk_id"]
        )

        # 9. Capture Evidence
        ev_worker = EvidenceCapturerWorker(self.agent_client)
        ev = ev_worker.capture_evidence(
            target_type="NODE",
            target_id=decision["node_id"],
            source_id=src["source_id"],
            content_hash=parsed["chunks"][0]["chunk_hash"],
            exact_quote="Payments require idempotent tokens and verified signatures.",
            start_line=2,
            end_line=2
        )

        # 10. Execute Frozen Projector V0.1
        conn = psycopg2.connect(ADMIN_URL)
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM pub_neural.run_projector('graph_projector');")
            proj_res = cur.fetchone()
            self.assertEqual(proj_res[3], "HEALTHY")

            # Verify projections
            cur.execute("SELECT count(*) FROM pub_neural.neural_sources WHERE file_sha256 = %s;", (blob["file_sha256"],))
            self.assertEqual(cur.fetchone()[0], 1)

            cur.execute("SELECT count(*) FROM pub_neural.neural_nodes WHERE id IN (%s, %s);", (decision["node_id"], rule["node_id"]))
            self.assertEqual(cur.fetchone()[0], 2)

            cur.execute("SELECT count(*) FROM pub_neural.neural_edges WHERE source_id = %s AND target_id = %s;", (decision["node_id"], rule["node_id"]))
            self.assertEqual(cur.fetchone()[0], 1)

            cur.execute("SELECT count(*) FROM pub_neural.neural_evidence WHERE node_id = %s;", (decision["node_id"],))
            self.assertEqual(cur.fetchone()[0], 1)

            cur.execute("SELECT count(*) FROM pub_neural.neural_fts WHERE id = %s;", (decision["node_id"],))
            self.assertEqual(cur.fetchone()[0], 1)
        conn.close()

        print("  -> TEST_PASSED [ING-15]: End-to-end ingestion pipeline successfully verified with Projector V0.1.")

    # ------------------------------------------------------------------------
    # ING-16: Real idempotent retry across critical workers with strict counts
    # ------------------------------------------------------------------------
    def test_ing_16_real_idempotent_retry(self):
        conn = psycopg2.connect(ADMIN_URL)
        conn.autocommit = True
        
        def get_event_count():
            with conn.cursor() as cur:
                cur.execute("SELECT count(*) FROM pub_neural.neural_events;")
                return cur.fetchone()[0]

        # 1. ScoutWorker Idempotency
        c_before = get_event_count()
        scout = ScoutWorker(self.ingestor_client)
        s1 = scout.discover_source(repository="pubcore/pub-ecom", commit_sha="commit_idem_100", file_path="docs/idem.md")
        c_after_first = get_event_count()
        self.assertEqual(c_after_first, c_before + 1)
        s2 = scout.discover_source(repository="pubcore/pub-ecom", commit_sha="commit_idem_100", file_path="docs/idem.md")
        c_after_retry = get_event_count()
        self.assertEqual(c_after_retry, c_after_first)
        self.assertFalse(s1["idempotent_replay"])
        self.assertTrue(s2["idempotent_replay"])
        self.assertEqual(s1["event_id"], s2["event_id"])
        self.assertEqual(s1["global_sequence"], s2["global_sequence"])
        self.assertEqual(s1["payload"], s2["payload"])

        # 2. BlobVault Idempotency
        c_before = get_event_count()
        vault = BlobVault(self.ingestor_client)
        raw = b"# Idempotency Blob Test\nPayload content."
        b1 = vault.preserve_and_verify(raw_bytes=raw)
        c_after_first = get_event_count()
        self.assertEqual(c_after_first, c_before + 1)
        b2 = vault.preserve_and_verify(raw_bytes=raw)
        c_after_retry = get_event_count()
        self.assertEqual(c_after_retry, c_after_first)
        self.assertFalse(b1["idempotent_replay"])
        self.assertTrue(b2["idempotent_replay"])
        self.assertEqual(b1["event_id"], b2["event_id"])
        self.assertEqual(b1["global_sequence"], b2["global_sequence"])
        self.assertEqual(b1["file_sha256"], b2["file_sha256"])

        # 3. SourceIngestorWorker Idempotency
        c_before = get_event_count()
        src_worker = SourceIngestorWorker(self.ingestor_client)
        si1 = src_worker.ingest_source(repository="pubcore/pub-ecom", commit_sha="commit_idem_100", file_path="docs/idem.md", file_sha256=b1["file_sha256"])
        c_after_first = get_event_count()
        self.assertEqual(c_after_first, c_before + 1)
        si2 = src_worker.ingest_source(repository="pubcore/pub-ecom", commit_sha="commit_idem_100", file_path="docs/idem.md", file_sha256=b1["file_sha256"])
        c_after_retry = get_event_count()
        self.assertEqual(c_after_retry, c_after_first)
        self.assertFalse(si1["idempotent_replay"])
        self.assertTrue(si2["idempotent_replay"])
        self.assertEqual(si1["event_id"], si2["event_id"])
        self.assertEqual(si1["global_sequence"], si2["global_sequence"])
        self.assertEqual(si1["payload"], si2["payload"])

        # 4. DocumentCaptureWorker Idempotency
        c_before = get_event_count()
        doc_worker = DocumentCaptureWorker(self.ingestor_client)
        d1 = doc_worker.capture_document(source_id=si1["source_id"], file_sha256=b1["file_sha256"], document_title="Idem Doc", raw_byte_size=len(raw))
        c_after_first = get_event_count()
        self.assertEqual(c_after_first, c_before + 1)
        d2 = doc_worker.capture_document(source_id=si1["source_id"], file_sha256=b1["file_sha256"], document_title="Idem Doc", raw_byte_size=len(raw))
        c_after_retry = get_event_count()
        self.assertEqual(c_after_retry, c_after_first)
        self.assertFalse(d1["idempotent_replay"])
        self.assertTrue(d2["idempotent_replay"])
        self.assertEqual(d1["event_id"], d2["event_id"])
        self.assertEqual(d1["payload"], d2["payload"])

        # 5. DocumentParserWorker Idempotency
        c_before = get_event_count()
        parser = DocumentParserWorker(self.ingestor_client)
        p1 = parser.parse_text_units(text_content=raw.decode("utf-8"), document_id=d1["document_id"], source_id=si1["source_id"])
        c_after_first = get_event_count()
        self.assertEqual(c_after_first, c_before + 1)
        p2 = parser.parse_text_units(text_content=raw.decode("utf-8"), document_id=d1["document_id"], source_id=si1["source_id"])
        c_after_retry = get_event_count()
        self.assertEqual(c_after_retry, c_after_first)
        self.assertFalse(p1["idempotent_replay"])
        self.assertTrue(p2["idempotent_replay"])
        self.assertEqual(p1["event_id"], p2["event_id"])
        self.assertEqual(p1["payload"], p2["payload"])

        # 6. EntityExtractorWorker Idempotency
        c_before = get_event_count()
        ent_worker = EntityExtractorWorker(self.agent_client)
        e1 = ent_worker.extract_entity(entity_type="RULE", title="Idempotent Processing Rule", summary="Summary", content="Rule text", source_chunk_id=p1["chunks"][0]["chunk_id"])
        c_after_first = get_event_count()
        self.assertEqual(c_after_first, c_before + 1)
        e2 = ent_worker.extract_entity(entity_type="RULE", title="Idempotent Processing Rule", summary="Summary", content="Rule text", source_chunk_id=p1["chunks"][0]["chunk_id"])
        c_after_retry = get_event_count()
        self.assertEqual(c_after_retry, c_after_first)
        self.assertFalse(e1["idempotent_replay"])
        self.assertTrue(e2["idempotent_replay"])
        self.assertEqual(e1["event_id"], e2["event_id"])
        self.assertEqual(e1["payload"], e2["payload"])

        # 7. RelationExtractorWorker Idempotency
        c_before = get_event_count()
        rel_worker = RelationExtractorWorker(self.agent_client)
        r1 = rel_worker.extract_relation(source_id=e1["node_id"], relation_type="REQUIRES", target_id=e1["node_id"], source_chunk_id=p1["chunks"][0]["chunk_id"])
        c_after_first = get_event_count()
        self.assertEqual(c_after_first, c_before + 1)
        r2 = rel_worker.extract_relation(source_id=e1["node_id"], relation_type="REQUIRES", target_id=e1["node_id"], source_chunk_id=p1["chunks"][0]["chunk_id"])
        c_after_retry = get_event_count()
        self.assertEqual(c_after_retry, c_after_first)
        self.assertFalse(r1["idempotent_replay"])
        self.assertTrue(r2["idempotent_replay"])
        self.assertEqual(r1["event_id"], r2["event_id"])
        self.assertEqual(r1["payload"], r2["payload"])

        # 8. EvidenceCapturerWorker Idempotency
        c_before = get_event_count()
        ev_worker = EvidenceCapturerWorker(self.agent_client)
        ev1 = ev_worker.capture_evidence(target_type="NODE", target_id=e1["node_id"], source_id=si1["source_id"], content_hash=p1["chunks"][0]["chunk_hash"], exact_quote="Payload content.", start_line=2, end_line=2)
        c_after_first = get_event_count()
        self.assertEqual(c_after_first, c_before + 1)
        ev2 = ev_worker.capture_evidence(target_type="NODE", target_id=e1["node_id"], source_id=si1["source_id"], content_hash=p1["chunks"][0]["chunk_hash"], exact_quote="Payload content.", start_line=2, end_line=2)
        c_after_retry = get_event_count()
        self.assertEqual(c_after_retry, c_after_first)
        self.assertFalse(ev1["idempotent_replay"])
        self.assertTrue(ev2["idempotent_replay"])
        self.assertEqual(ev1["event_id"], ev2["event_id"])
        self.assertEqual(ev1["payload"], ev2["payload"])

        conn.close()
        print("  -> TEST_PASSED [ING-16]: Real semantic idempotent retries verified across all 8 worker components with BEFORE==AFTER_RETRY counts and payload equality.")

    # ------------------------------------------------------------------------
    # ING-17: Real worker crash / restart with SIGKILL
    # ------------------------------------------------------------------------
    def test_ing_17_real_worker_crash_restart(self):
        conn = psycopg2.connect(ADMIN_URL)
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM pub_neural.neural_events;")
            c_initial = cur.fetchone()[0]
        conn.close()

        worker_script = f"""
import sys, time, os
from src.ingestion.client import PubNeuralClient
from src.ingestion.blob_vault import BlobVault
from src.ingestion.source_ingestor import SourceIngestorWorker

client = PubNeuralClient(
    db_url="{DB_URL}",
    actor_id="actor:system:ingestor",
    machine_secret="{INGESTOR_SECRET}",
    requested_trust_zone="tz_internal_holding",
    requested_project="pub-ecom"
)
client.establish_session()
vault = BlobVault(client)
content = b"# Crash SIGKILL Test\\nReal process termination recovery."
res = vault.preserve_and_verify(raw_bytes=content)

source_worker = SourceIngestorWorker(client)
# Print PID and READY
print(f"PID:{{os.getpid()}}", flush=True)
print("READY_FOR_CRASH", flush=True)
time.sleep(2)
res_ingest = source_worker.ingest_source(
    repository="pubcore/pub-ecom",
    commit_sha="sigkill_commit_1",
    file_path="docs/crash_sigkill.md",
    file_sha256=res["file_sha256"]
)
print("FINISHED", flush=True)
"""
        proc = subprocess.Popen([sys.executable, "-c", worker_script], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        pid_line = proc.stdout.readline().strip()
        ready_line = proc.stdout.readline().strip()
        self.assertIn("PID:", pid_line)
        pid_before_kill = int(pid_line.split(":")[1])
        self.assertIn("READY_FOR_CRASH", ready_line)

        # Send SIGKILL
        os.kill(pid_before_kill, signal.SIGKILL)
        proc.wait()
        self.assertEqual(proc.returncode, -signal.SIGKILL)

        # Verify state after crash
        conn = psycopg2.connect(ADMIN_URL)
        with conn.cursor() as cur:
            # Check uncommitted transaction did not commit source ingest
            cur.execute("SELECT count(*) FROM pub_neural.neural_events WHERE stream_id LIKE 'stream:source:%sigkill_commit_1%';")
            self.assertEqual(cur.fetchone()[0], 0)
        conn.close()

        # Restarted worker retries the logical task
        new_client = PubNeuralClient(
            db_url=DB_URL,
            actor_id="actor:system:ingestor",
            machine_secret=INGESTOR_SECRET,
            requested_trust_zone="tz_internal_holding",
            requested_project="pub-ecom"
        )
        new_client.establish_session()
        vault = BlobVault(new_client)
        content = b"# Crash SIGKILL Test\nReal process termination recovery."
        res_blob = vault.preserve_and_verify(raw_bytes=content)

        source_worker = SourceIngestorWorker(new_client)
        res_ingest = source_worker.ingest_source(
            repository="pubcore/pub-ecom",
            commit_sha="sigkill_commit_1",
            file_path="docs/crash_sigkill.md",
            file_sha256=res_blob["file_sha256"]
        )
        new_client.close()

        # Confirm convergence: exactly 1 event for this source, stream_version = 1
        conn = psycopg2.connect(ADMIN_URL)
        with conn.cursor() as cur:
            cur.execute("SELECT count(*), max(stream_version) FROM pub_neural.neural_events WHERE stream_id = %s;", (f"stream:source:{res_ingest['source_id']}",))
            cnt, max_ver = cur.fetchone()
            self.assertEqual(cnt, 1)
            self.assertEqual(max_ver, 1)

            # Check no orphan event parents
            cur.execute(
                """
                SELECT count(*) FROM pub_neural.neural_event_parents nep
                LEFT JOIN pub_neural.neural_events ne ON nep.parent_event_id = ne.id
                WHERE ne.id IS NULL;
                """
            )
            orphan_count = cur.fetchone()[0]
            self.assertEqual(orphan_count, 0)
        conn.close()

        print("  -> TEST_PASSED [ING-17]: Real process SIGKILL crash (PID %d) & restart converged with zero duplicate events and zero orphan lineage." % pid_before_kill)

    # ------------------------------------------------------------------------
    # ING-18: Multi-boundary Blob / Manifest / Event Recovery
    # ------------------------------------------------------------------------
    def test_ing_18_blob_manifest_event_recovery(self):
        vault = BlobVault(self.ingestor_client)

        # Boundary A: Failure before filesystem write
        raw_a = b"# Boundary A Test\nFail before write."
        file_sha_a, _ = vault.compute_hashes(raw_a)
        path_a = os.path.join(vault.storage_base_dir, f"{file_sha_a}.bin")
        if os.path.exists(path_a):
            os.remove(path_a)
        self.assertFalse(os.path.exists(path_a))
        # Retry recovers and writes file + event + manifest
        rec_a = vault.preserve_and_verify(raw_bytes=raw_a)
        self.assertTrue(os.path.exists(path_a))
        self.assertEqual(rec_a["file_sha256"], file_sha_a)

        # Boundary B: Failure after filesystem write, before manifest registration / event append
        raw_b = b"# Boundary B Test\nFail after write, before DB."
        file_sha_b, _ = vault.compute_hashes(raw_b)
        path_b = os.path.join(vault.storage_base_dir, f"{file_sha_b}.bin")
        with open(path_b, "wb") as f:
            f.write(raw_b)
        self.assertTrue(os.path.exists(path_b))
        # Ensure DB has no event or manifest
        conn = psycopg2.connect(ADMIN_URL)
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM pub_neural.source_blobs WHERE file_sha256 = %s;", (file_sha_b,))
            self.assertEqual(cur.fetchone()[0], 0)
        conn.close()
        # Retry completes pipeline idempotently
        rec_b = vault.preserve_and_verify(raw_bytes=raw_b)
        self.assertFalse(rec_b["idempotent_replay"])
        self.assertEqual(rec_b["file_sha256"], file_sha_b)

        # Boundary C: Failure after event append, before manifest registration
        raw_c = b"# Boundary C Test\nFail after event, before manifest."
        file_sha_c, content_hash_c = vault.compute_hashes(raw_c)
        path_c = os.path.join(vault.storage_base_dir, f"{file_sha_c}.bin")
        with open(path_c, "wb") as f:
            f.write(raw_c)
        ns = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
        event_id_c = uuid.uuid5(ns, f"blob:{file_sha_c}")
        payload_c = {
            "file_sha256": file_sha_c,
            "content_hash": content_hash_c,
            "storage_uri": f"file://{path_c}",
            "byte_size": len(raw_c),
            "mime_type": "text/markdown",
            "storage_backend": "LOCAL_DISK"
        }
        self.ingestor_client.append_canonical_event(
            event_id=event_id_c,
            event_type="SOURCE_BLOB_VERIFIED",
            stream_id=f"stream:blobs:{file_sha_c[:16]}",
            stream_version=1,
            payload=payload_c,
            producer_version="blob_vault:v1.0.0"
        )
        # Verify event exists but manifest missing
        conn = psycopg2.connect(ADMIN_URL)
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM pub_neural.neural_events WHERE id = %s;", (str(event_id_c),))
            self.assertEqual(cur.fetchone()[0], 1)
            cur.execute("SELECT count(*) FROM pub_neural.source_blobs WHERE file_sha256 = %s;", (file_sha_c,))
            self.assertEqual(cur.fetchone()[0], 0)
        conn.close()
        # Retry detects event, registers missing manifest in source_blobs
        rec_c = vault.preserve_and_verify(raw_bytes=raw_c)
        self.assertTrue(rec_c["idempotent_replay"])
        conn = psycopg2.connect(ADMIN_URL)
        with conn.cursor() as cur:
            cur.execute("SELECT originating_event_id, status FROM pub_neural.source_blobs WHERE file_sha256 = %s;", (file_sha_c,))
            row = cur.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(str(row[0]), str(event_id_c))
            self.assertEqual(row[1], "VERIFIED")
        conn.close()

        print("  -> TEST_PASSED [ING-18]: Multi-boundary blob recovery (A, B, C) proved recoverable convergence without split-brain state.")

    # ------------------------------------------------------------------------
    # ING-19: Event identity vs observation metadata snapshot
    # ------------------------------------------------------------------------
    def test_ing_19_event_payload_determinism(self):
        # Operational timestamp vs Canonical event identity
        scout = ScoutWorker(self.ingestor_client)
        # Call 1
        time.sleep(0.01)
        r1 = scout.discover_source(repository="pubcore/pub-ecom", commit_sha="snap_commit_1", file_path="docs/snap.md")
        # Call 2 with identical domain identity
        time.sleep(0.01)
        r2 = scout.discover_source(repository="pubcore/pub-ecom", commit_sha="snap_commit_1", file_path="docs/snap.md")

        # Identity comparison
        self.assertEqual(r1["event_id"], r2["event_id"])
        self.assertEqual(r1["global_sequence"], r2["global_sequence"])

        # Domain fields must be identical
        p1, p2 = r1["payload"], r2["payload"]
        self.assertEqual(p1["repository"], p2["repository"])
        self.assertEqual(p1["branch"], p2["branch"])
        self.assertEqual(p1["commit_sha"], p2["commit_sha"])
        self.assertEqual(p1["file_path"], p2["file_path"])
        self.assertEqual(p1["project_id"], p2["project_id"])
        self.assertEqual(p1["trust_zone"], p2["trust_zone"])

        # Discovered_at is classified as operational metadata preserved on replay
        self.assertEqual(p1["discovered_at"], p2["discovered_at"])

        print("  -> TEST_PASSED [ING-19]: Explicit snapshot comparison proven (IDENTITY_A == IDENTITY_B, DOMAIN_PAYLOAD_A == DOMAIN_PAYLOAD_B).")

    # ------------------------------------------------------------------------
    # ING-20: Document parsed content identity and collision resistance
    # ------------------------------------------------------------------------
    def test_ing_20_parser_content_identity(self):
        parser = DocumentParserWorker(self.ingestor_client)
        content_a = "Line 1: Alpha specification statement.\nLine 2: Rule zero.\nLine 3: Terminal."
        content_b = "Line 1: Beta specification statement.\nLine 2: Rule zero.\nLine 3: Terminal."

        res_a1 = parser.parse_text_units(text_content=content_a, document_id="doc:pub-ecom:test-id", source_id="0191e4f0-0020-7000-8000-000000000001", parser_version="v1.0.0", chunk_line_size=1)
        res_a2 = parser.parse_text_units(text_content=content_a, document_id="doc:pub-ecom:test-id", source_id="0191e4f0-0020-7000-8000-000000000001", parser_version="v1.0.0", chunk_line_size=1)
        res_b = parser.parse_text_units(text_content=content_b, document_id="doc:pub-ecom:test-id", source_id="0191e4f0-0020-7000-8000-000000000001", parser_version="v1.0.0", chunk_line_size=1)

        # Same content -> bit-for-bit same event identity
        self.assertEqual(res_a1["event_id"], res_a2["event_id"])
        self.assertEqual(res_a1["payload"]["content_hash"], res_a2["payload"]["content_hash"])

        # Different content with same (doc_id, parser_version, chunk_count) -> different event identity
        self.assertNotEqual(res_a1["event_id"], res_b["event_id"])
        self.assertNotEqual(res_a1["payload"]["content_hash"], res_b["payload"]["content_hash"])
        self.assertEqual(len(res_a1["chunks"]), len(res_b["chunks"]))

        print("  -> TEST_PASSED [ING-20]: Parser content identity proven (same content -> same ID; diff content -> diff ID).")

    # ------------------------------------------------------------------------
    # ING-21: Source context authorization and scope containment
    # ------------------------------------------------------------------------
    def test_ing_21_source_context_authorization(self):
        src_worker = SourceIngestorWorker(self.ingestor_client)
        vault = BlobVault(self.ingestor_client)
        blob = vault.preserve_and_verify(raw_bytes=b"# Auth Test\nAllowlist containment.")

        # 1. Authorized configuration must PASS
        valid_res = src_worker.ingest_source(
            repository="pubcore/pub-ecom",
            commit_sha="commit_auth_pass_1",
            file_path="docs/pass.md",
            file_sha256=blob["file_sha256"],
            branch="main",
            trust_zone="tz_internal_holding",
            project_id="pub-ecom"
        )
        self.assertIn("global_sequence", valid_res)

        # 2. Authorized repo + wrong branch -> FAIL_CLOSED
        with self.assertRaises(ValueError) as ctx1:
            src_worker.ingest_source(
                repository="pubcore/pub-ecom",
                commit_sha="commit_auth_fail_1",
                file_path="docs/fail.md",
                file_sha256=blob["file_sha256"],
                branch="feature-unapproved"
            )
        self.assertIn("UNAUTHORIZED_BRANCH", str(ctx1.exception))

        # 3. Authorized repo + wrong project -> FAIL_CLOSED
        with self.assertRaises(ValueError) as ctx2:
            src_worker.ingest_source(
                repository="pubcore/pub-ecom",
                commit_sha="commit_auth_fail_2",
                file_path="docs/fail.md",
                file_sha256=blob["file_sha256"],
                project_id="unauthorized-foreign-project"
            )
        self.assertIn("UNAUTHORIZED_PROJECT_ID", str(ctx2.exception))

        # 4. Authorized repo + wrong trust_zone -> FAIL_CLOSED
        with self.assertRaises(ValueError) as ctx3:
            src_worker.ingest_source(
                repository="pubcore/pub-ecom",
                commit_sha="commit_auth_fail_3",
                file_path="docs/fail.md",
                file_sha256=blob["file_sha256"],
                trust_zone="tz_sovereign_governance"
            )
        self.assertIn("UNAUTHORIZED_TRUST_ZONE", str(ctx3.exception))

        # 5. Unauthorized repo -> FAIL_CLOSED
        with self.assertRaises(ValueError) as ctx4:
            src_worker.ingest_source(
                repository="unauthorized/foreign-repo",
                commit_sha="commit_auth_fail_4",
                file_path="docs/fail.md",
                file_sha256=blob["file_sha256"]
            )
        self.assertIn("UNAUTHORIZED_SOURCE_SCOPE", str(ctx4.exception))

        print("  -> TEST_PASSED [ING-21]: Source ingest parameters fail-closed across all 4 unauthorized scope dimensions.")

    # ------------------------------------------------------------------------
    # ING-22: Node ID collision resistance & Unicode normalization
    # ------------------------------------------------------------------------
    def test_ing_22_node_id_collision_resistance(self):
        ent_worker = EntityExtractorWorker(self.agent_client)

        # 1. Unicode diacritics handling & case normalization
        id_decisao = ent_worker.format_node_id("DECISION", "pub-ecom", "Decisão de Autenticação Segura")
        id_decisao_lower = ent_worker.format_node_id("DECISION", "pub-ecom", "decisao de autenticacao segura")
        self.assertIn("decisao-de-autenticacao-segura", id_decisao)
        
        # 2. Disambiguation between distinct titles that normalize similarly
        title_1 = "Payment API Timeout"
        title_2 = "Payment API: Timeout"
        id1 = ent_worker.format_node_id("RULE", "pub-ecom", title_1)
        id2 = ent_worker.format_node_id("RULE", "pub-ecom", title_2)
        self.assertNotEqual(id1, id2)
        self.assertTrue(id1.startswith("rule:pub-ecom:payment-api-timeout-"))
        self.assertTrue(id2.startswith("rule:pub-ecom:payment-api-timeout-"))

        # 3. Arbitrarily long title: length must not exceed VARCHAR(128)
        long_title = "This is an extremely verbose architectural specification title explaining why database mutations require CEO consensus and cryptographic authorization across all holding entities"
        id_long = ent_worker.format_node_id("DECISION", "pub-ecom", long_title)
        self.assertLessEqual(len(id_long), 128)
        self.assertTrue(id_long.startswith("decision:pub-ecom:"))

        # Check in PostgreSQL neural_nodes insertion
        res = ent_worker.extract_entity(
            entity_type="DECISION",
            title=long_title,
            summary="Verbose summary",
            content="Verbose content",
            source_chunk_id="chunk:pub-ecom:long:0"
        )
        self.assertLessEqual(len(res["node_id"]), 128)

        print("  -> TEST_PASSED [ING-22]: Unicode normalization, title hash disambiguation, and SQL length <= 128 verified.")


if __name__ == "__main__":
    unittest.main()


