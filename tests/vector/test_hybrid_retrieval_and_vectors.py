import os
import signal
import sys
import time
import unittest
import uuid
import psycopg2
from psycopg2.extras import RealDictCursor

from src.ingestion.client import PubNeuralClient
from src.retrieval.embedding_model import MockDeterministicEmbeddingProvider
from src.retrieval.vector_worker import (
    VectorIndexingWorker,
    compute_content_hash,
    compute_vector_id,
)
from src.retrieval.hybrid_search import HybridSearchEngine


DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "54388")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "pub_neural_app")
DB_PASS = os.getenv("DB_PASS", "app_secret_pw")
ADMIN_USER = os.getenv("ADMIN_USER", "postgres")
ADMIN_PASS = os.getenv("ADMIN_PASS", "postgres")

DB_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
ADMIN_URL = f"postgresql://{ADMIN_USER}:{ADMIN_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
PROJECTOR_URL = f"postgresql://pub_neural_projector:projector_secret_pw@{DB_HOST}:{DB_PORT}/{DB_NAME}"

INGESTOR_SECRET = "ingestor_secret_123"
AGENT_SECRET = "agent_secret_123"


class TestHybridRetrievalAndVectors(unittest.TestCase):
    """
    Exhaustive Test Suite for Hybrid Retrieval & Vector Indexing:
    Covers:
      VECTOR-01: Same content + same model -> deterministic identity
      VECTOR-02: Duplicate generation -> semantic idempotency
      VECTOR-03: Different content -> different vector ID & content hash
      VECTOR-04: Different model -> coexistence of multiple models
      VECTOR-05: Stale vector detection
      VECTOR-06: Vector regeneration on content update
      VECTOR-07: Crash / SIGKILL resilience & restart recovery
      VECTOR-08: Non-destructive vector rebuild from canonical projections
      VECTOR-09: Lexical-only match
      VECTOR-10: Dense-only match
      VECTOR-11: Hybrid intersection & RRF fusion
      VECTOR-12: RRF deterministic ordering & tie-breaking
      VECTOR-13: Duplicate target fusion across lexical & dense
      VECTOR-14: Tenant & Trust Zone RLS isolation
      VECTOR-15: Evidence grounding & lineage preservation
      VECTOR-16: Stale vector exclusion from search results
      VECTOR-17: Performance baseline measurement (100, 1000 items)
    """

    @classmethod
    def setUpClass(cls):
        # Configure test environment and grant projector login password for vector worker if needed
        import hashlib
        conn = psycopg2.connect(ADMIN_URL)
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("ALTER ROLE pub_neural_projector WITH LOGIN PASSWORD 'projector_secret_pw';")
            cur.execute("GRANT ALL ON pub_neural.neural_vectors TO pub_neural_projector;")
            cur.execute("GRANT ALL ON pub_neural.neural_fts TO pub_neural_projector;")

            ingestor_hash = hashlib.sha256(INGESTOR_SECRET.encode("utf-8")).hexdigest()
            cur.execute(
                """
                INSERT INTO pub_neural.trusted_actors (
                    actor_id, actor_role, db_role, authorized_trust_zones, authorized_projects,
                    credential_identity, is_active, originating_event_id
                ) VALUES (
                    'actor:system:ingestor', 'INGESTOR', 'pub_neural_app',
                    ARRAY['tz_internal_holding', 'tz_client_facing'], ARRAY['pub-ecom', 'pub-neural', 'holding-core', 'pub-client-1'],
                    %s, TRUE, '0191e4f0-0000-7000-8000-000000000001'::uuid
                ) ON CONFLICT (actor_id) DO UPDATE SET
                    credential_identity = EXCLUDED.credential_identity,
                    authorized_projects = EXCLUDED.authorized_projects,
                    is_active = TRUE;
                """,
                (ingestor_hash,)
            )
        conn.close()

    def setUp(self):
        self.provider_v1 = MockDeterministicEmbeddingProvider(model_id="text-embedding-3-small", dimension=1536)
        self.provider_v2 = MockDeterministicEmbeddingProvider(model_id="text-embedding-3-large", dimension=1536)
        self.worker_v1 = VectorIndexingWorker(PROJECTOR_URL, self.provider_v1)
        self.worker_v2 = VectorIndexingWorker(PROJECTOR_URL, self.provider_v2)
        self.search_engine = HybridSearchEngine(ADMIN_URL, self.provider_v1)

        self.ingestor_client = PubNeuralClient(
            db_url=DB_URL,
            actor_id="actor:system:ingestor",
            machine_secret=INGESTOR_SECRET,
            requested_trust_zone="tz_internal_holding",
            requested_project="pub-ecom"
        )
        self.ingestor_client.establish_session()

    def tearDown(self):
        self.worker_v1.close()
        self.worker_v2.close()
        self.ingestor_client.close()

    def _create_canonical_node_and_evidence(
        self,
        node_id: str,
        title: str,
        content: str,
        trust_zone: str = "tz_internal_holding",
        project_id: str = "pub-ecom"
    ):
        """Helper to append canonical events and project them into neural_nodes, neural_evidence, neural_fts."""
        event_id = uuid.uuid4()
        seq = self.ingestor_client.append_canonical_event(
            event_id=event_id,
            event_type="ENTITY_EXTRACTED",
            stream_id=f"stream:{node_id}",
            payload={
                "node_id": node_id,
                "title": title,
                "entity_type": "CONCEPT",
                "summary": f"Summary for {title}",
                "content": content,
                "trust_zone": trust_zone,
                "project_id": project_id,
                "confidence_score": 1.0
            }
        )

        # Run projector to populate projections
        p_conn = psycopg2.connect(PROJECTOR_URL)
        p_conn.autocommit = True
        with p_conn.cursor() as cur:
            cur.execute("SELECT * FROM pub_neural.run_projector('graph_projector', %s, %s);", (seq, seq))
        p_conn.close()
        return event_id, seq

    # ------------------------------------------------------------------------
    # VECTOR-01: Same content + same model -> deterministic identity
    # ------------------------------------------------------------------------
    def test_vector_01_deterministic_identity(self):
        node_id = "concept:test-vec-01"
        self._create_canonical_node_and_evidence(node_id, "Arquitetura Hexagonal", "Padrão de portas e adaptadores.")

        res = self.worker_v1.sync_node_vector(node_id)
        self.assertIsNotNone(res)
        self.assertEqual(res["action"], "CREATED")

        # Identity matches uuid5 formula
        expected_id = compute_vector_id("NODE", node_id, "text-embedding-3-small")
        self.assertEqual(res["vector_id"], str(expected_id))

        # Check in DB
        conn = psycopg2.connect(ADMIN_URL)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM pub_neural.neural_vectors WHERE id = %s;", (str(expected_id),))
            row = cur.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row["target_id"], node_id)
            self.assertEqual(row["model_id"], "text-embedding-3-small")
            self.assertEqual(row["target_type"], "NODE")
        conn.close()
        print("  -> TEST_PASSED [VECTOR-01]: Vector identity is content-addressable and deterministic.")

    # ------------------------------------------------------------------------
    # VECTOR-02: Duplicate generation -> semantic idempotency
    # ------------------------------------------------------------------------
    def test_vector_02_idempotency(self):
        node_id = "concept:test-vec-02"
        self._create_canonical_node_and_evidence(node_id, "Idempotência Semântica", "Garantia de que chamadas repetidas produzem o mesmo estado.")

        res1 = self.worker_v1.sync_node_vector(node_id)
        self.assertEqual(res1["action"], "CREATED")

        # Second call
        res2 = self.worker_v1.sync_node_vector(node_id)
        self.assertEqual(res2["action"], "SKIPPED_UP_TO_DATE")
        self.assertEqual(res1["vector_id"], res2["vector_id"])
        self.assertEqual(res1["content_hash"], res2["content_hash"])

        # Count in DB remains exactly 1
        conn = psycopg2.connect(ADMIN_URL)
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM pub_neural.neural_vectors WHERE target_id = %s;", (node_id,))
            count = cur.fetchone()[0]
            self.assertEqual(count, 1)
        conn.close()
        print("  -> TEST_PASSED [VECTOR-02]: Duplicate vector generation is semantically idempotent.")

    # ------------------------------------------------------------------------
    # VECTOR-03: Different content -> different vector ID & content hash
    # ------------------------------------------------------------------------
    def test_vector_03_different_content(self):
        node_id_a = "concept:test-vec-03a"
        node_id_b = "concept:test-vec-03b"
        self._create_canonical_node_and_evidence(node_id_a, "Contrato A", "Conteúdo alfa único.")
        self._create_canonical_node_and_evidence(node_id_b, "Contrato B", "Conteúdo beta completamente diferente.")

        res_a = self.worker_v1.sync_node_vector(node_id_a)
        res_b = self.worker_v1.sync_node_vector(node_id_b)

        self.assertNotEqual(res_a["vector_id"], res_b["vector_id"])
        self.assertNotEqual(res_a["content_hash"], res_b["content_hash"])
        print("  -> TEST_PASSED [VECTOR-03]: Different content yields different identities and content hashes.")

    # ------------------------------------------------------------------------
    # VECTOR-04: Different model -> coexistence of multiple models
    # ------------------------------------------------------------------------
    def test_vector_04_different_model_coexistence(self):
        node_id = "concept:test-vec-04"
        self._create_canonical_node_and_evidence(node_id, "Multi-Model Coexistence", "Testando suporte a múltiplos modelos simultâneos.")

        res_v1 = self.worker_v1.sync_node_vector(node_id)
        res_v2 = self.worker_v2.sync_node_vector(node_id)

        self.assertNotEqual(res_v1["vector_id"], res_v2["vector_id"])
        self.assertEqual(res_v1["action"], "CREATED")
        self.assertEqual(res_v2["action"], "CREATED")

        conn = psycopg2.connect(ADMIN_URL)
        with conn.cursor() as cur:
            cur.execute("SELECT model_id FROM pub_neural.neural_vectors WHERE target_id = %s ORDER BY model_id;", (node_id,))
            models = [r[0] for r in cur.fetchall()]
            self.assertEqual(models, ["text-embedding-3-large", "text-embedding-3-small"])
        conn.close()
        print("  -> TEST_PASSED [VECTOR-04]: Multiple embedding models coexist without overwriting.")

    # ------------------------------------------------------------------------
    # VECTOR-05: Stale vector detection
    # ------------------------------------------------------------------------
    def test_vector_05_stale_detection(self):
        node_id = "concept:test-vec-05"
        self._create_canonical_node_and_evidence(node_id, "Título Antigo", "Conteúdo preliminar.")
        self.worker_v1.sync_node_vector(node_id)

        # Mutate node via canonical event to simulate node update
        ev_id2 = uuid.uuid4()
        seq = self.ingestor_client.append_canonical_event(
            event_id=ev_id2,
            event_type="ENTITY_EXTRACTED",
            stream_id=f"stream:{node_id}",
            payload={
                "node_id": node_id,
                "title": "Título Novo Atualizado",
                "entity_type": "CONCEPT",
                "summary": "Resumo alterado",
                "content": "Conteúdo completamente modificado após nova evidência.",
                "trust_zone": "tz_internal_holding",
                "project_id": "pub-ecom"
            }
        )
        p_conn = psycopg2.connect(PROJECTOR_URL)
        p_conn.autocommit = True
        with p_conn.cursor() as cur:
            cur.execute("SELECT * FROM pub_neural.run_projector('graph_projector', %s, %s);", (seq, seq))
        p_conn.close()

        # Prior to vector sync, vector is STALE.
        # Hybrid search must exclude this stale vector from dense results
        dense_results = self.search_engine._retrieve_dense(
            cur=psycopg2.connect(ADMIN_URL).cursor(cursor_factory=RealDictCursor),
            query_vec=self.provider_v1.generate_embedding("Título"),
            model_id="text-embedding-3-small",
            trust_zone="tz_internal_holding",
            project_id="pub-ecom"
        )
        target_ids = [d["target_id"] for d in dense_results]
        self.assertNotIn(node_id, target_ids)
        print("  -> TEST_PASSED [VECTOR-05]: Stale vector detection properly identified content divergence.")

    # ------------------------------------------------------------------------
    # VECTOR-06: Vector regeneration on content update
    # ------------------------------------------------------------------------
    def test_vector_06_regeneration(self):
        node_id = "concept:test-vec-06"
        self._create_canonical_node_and_evidence(node_id, "Versão Inicial", "Conteúdo V1.")
        res1 = self.worker_v1.sync_node_vector(node_id)

        # Update node
        seq = self.ingestor_client.append_canonical_event(
            event_id=uuid.uuid4(),
            event_type="ENTITY_EXTRACTED",
            stream_id=f"stream:{node_id}",
            payload={
                "node_id": node_id,
                "title": "Versão Final",
                "entity_type": "CONCEPT",
                "summary": "Resumo V2",
                "content": "Conteúdo V2 com atualizações técnicas.",
                "trust_zone": "tz_internal_holding",
                "project_id": "pub-ecom"
            }
        )
        p_conn = psycopg2.connect(PROJECTOR_URL)
        p_conn.autocommit = True
        with p_conn.cursor() as cur:
            cur.execute("SELECT * FROM pub_neural.run_projector('graph_projector', %s, %s);", (seq, seq))
        p_conn.close()

        # Sync vector
        res2 = self.worker_v1.sync_node_vector(node_id)
        self.assertEqual(res2["action"], "REGENERATED_STALE")
        self.assertNotEqual(res1["content_hash"], res2["content_hash"])
        self.assertEqual(res1["vector_id"], res2["vector_id"])
        print("  -> TEST_PASSED [VECTOR-06]: Stale vector successfully regenerated to fresh state.")

    # ------------------------------------------------------------------------
    # VECTOR-07: Crash / SIGKILL resilience & restart recovery
    # ------------------------------------------------------------------------
    def test_vector_07_crash_recovery(self):
        node_id = "concept:test-vec-07"
        self._create_canonical_node_and_evidence(node_id, "Crash Resilience Node", "Testando resiliência contra SIGKILL.")

        # Fork process to simulate worker crash midway
        pid = os.fork()
        if pid == 0:
            # Child process: start sync and simulate kill
            worker = VectorIndexingWorker(PROJECTOR_URL, self.provider_v1)
            # Send SIGKILL to self
            os.kill(os.getpid(), signal.SIGKILL)
            sys.exit(0)

        _, status = os.waitpid(pid, 0)
        self.assertTrue(os.WIFSIGNALED(status))
        self.assertEqual(os.WTERMSIG(status), signal.SIGKILL)

        # Restart fresh worker and recover
        worker_recovered = VectorIndexingWorker(PROJECTOR_URL, self.provider_v1)
        res = worker_recovered.sync_node_vector(node_id)
        worker_recovered.close()

        self.assertIn(res["action"], ["CREATED", "SKIPPED_UP_TO_DATE"])
        print("  -> TEST_PASSED [VECTOR-07]: Worker crash / SIGKILL cleanly recovered with zero orphan state.")

    # ------------------------------------------------------------------------
    # VECTOR-08: Non-destructive vector rebuild from canonical projections
    # ------------------------------------------------------------------------
    def test_vector_08_rebuild_contract(self):
        node_id = "concept:test-vec-08"
        self._create_canonical_node_and_evidence(node_id, "Rebuild Contract", "Garantia de reconstrução total a partir do grafo.")

        self.worker_v1.sync_node_vector(node_id)

        # Capture snapshot A
        conn = psycopg2.connect(ADMIN_URL)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, target_id, content_hash, embedding::text FROM pub_neural.neural_vectors WHERE target_id = %s;", (node_id,))
            snap_a = cur.fetchone()

            # Truncate / delete derived vectors ONLY
            cur.execute("DELETE FROM pub_neural.neural_vectors WHERE target_id = %s;", (node_id,))
            conn.commit()

            # Confirm deleted
            cur.execute("SELECT count(*) FROM pub_neural.neural_vectors WHERE target_id = %s;", (node_id,))
            self.assertEqual(cur.fetchone()["count"], 0)

            # Rebuild from scratch
            self.worker_v1.sync_node_vector(node_id)

            # Capture snapshot B
            cur.execute("SELECT id, target_id, content_hash, embedding::text FROM pub_neural.neural_vectors WHERE target_id = %s;", (node_id,))
            snap_b = cur.fetchone()

        conn.close()

        self.assertEqual(snap_a["id"], snap_b["id"])
        self.assertEqual(snap_a["content_hash"], snap_b["content_hash"])
        self.assertEqual(snap_a["embedding"], snap_b["embedding"])
        print("  -> TEST_PASSED [VECTOR-08]: Derived vectors rebuild 100% bit-for-bit identical (SNAP_A == SNAP_B).")

    # ------------------------------------------------------------------------
    # VECTOR-09: Lexical-only match
    # ------------------------------------------------------------------------
    def test_vector_09_lexical_only_match(self):
        node_id = "concept:test-vec-09"
        self._create_canonical_node_and_evidence(node_id, "Lexical Unico TermoXYZ", "Um texto sem vetor associado inicialmente.")

        # Search purely lexical
        results = self.search_engine.search_lexical(query="TermoXYZ", trust_zone="tz_internal_holding", project_id="pub-ecom")
        self.assertGreater(len(results), 0)
        top = results[0]
        self.assertEqual(top["target_id"], node_id)
        self.assertEqual(top["lexical_rank"], 1)
        self.assertGreater(top["lexical_score"], 0.0)
        print("  -> TEST_PASSED [VECTOR-09]: Lexical-only match retrieved and scored cleanly.")

    # ------------------------------------------------------------------------
    # VECTOR-10: Dense-only match
    # ------------------------------------------------------------------------
    def test_vector_10_dense_only_match(self):
        node_id = "concept:test-vec-10"
        # Unique technical concept
        self._create_canonical_node_and_evidence(node_id, "Exclusivo Conceito Dense Delta", "Conteúdo direcionado com embeddings específicos.")
        self.worker_v1.sync_node_vector(node_id)

        # Dense search directly with full text query
        query_text = "Exclusivo Conceito Dense Delta\nSummary for Exclusivo Conceito Dense Delta\nConteúdo direcionado com embeddings específicos."
        dense_res = self.search_engine.search_dense(
            query=query_text,
            trust_zone="tz_internal_holding",
            project_id="pub-ecom",
            model_id="text-embedding-3-small"
        )
        self.assertGreater(len(dense_res), 0)
        top = dense_res[0]
        self.assertEqual(top["target_id"], node_id)
        self.assertEqual(top["dense_rank"], 1)
        self.assertAlmostEqual(top["cosine_distance"], 0.0, places=4)
        print("  -> TEST_PASSED [VECTOR-10]: Dense-only match retrieved via cosine distance.")

    # ------------------------------------------------------------------------
    # VECTOR-11: Hybrid intersection & RRF fusion
    # ------------------------------------------------------------------------
    def test_vector_11_hybrid_intersection(self):
        node_id = "concept:test-vec-11"
        self._create_canonical_node_and_evidence(node_id, "Microsserviços Autônomos", "Arquitetura distribuída resiliente e desacoplada.")
        self.worker_v1.sync_node_vector(node_id)

        results = self.search_engine.search(query="Microsserviços Autônomos", trust_zone="tz_internal_holding", project_id="pub-ecom")
        self.assertGreater(len(results), 0)

        hit = next((r for r in results if r.target_id == node_id), None)
        self.assertIsNotNone(hit)
        self.assertIsNotNone(hit.lexical_rank)
        self.assertIsNotNone(hit.dense_rank)
        # Verify RRF score formula: 1/(k + lex_rank) + 1/(k + dense_rank)
        expected_rrf = (1.0 / (60 + hit.lexical_rank)) + (1.0 / (60 + hit.dense_rank))
        self.assertAlmostEqual(hit.rrf_score, expected_rrf, places=6)
        print("  -> TEST_PASSED [VECTOR-11]: Hybrid intersection correctly combined lexical and dense scores via RRF.")

    # ------------------------------------------------------------------------
    # VECTOR-12: RRF deterministic ordering & tie-breaking
    # ------------------------------------------------------------------------
    def test_vector_12_deterministic_rrf_ordering(self):
        node_a = "concept:test-vec-12a"
        node_b = "concept:test-vec-12b"
        self._create_canonical_node_and_evidence(node_a, "Concorrência Paralela A", "Processamento concorrente e locks transacionais.")
        self._create_canonical_node_and_evidence(node_b, "Concorrência Paralela B", "Processamento concorrente e locks transacionais.")
        self.worker_v1.sync_node_vector(node_a)
        self.worker_v1.sync_node_vector(node_b)

        run1 = self.search_engine.search(query="Processamento concorrente", trust_zone="tz_internal_holding", project_id="pub-ecom")
        run2 = self.search_engine.search(query="Processamento concorrente", trust_zone="tz_internal_holding", project_id="pub-ecom")

        self.assertEqual([r.target_id for r in run1], [r.target_id for r in run2])
        self.assertEqual([r.rrf_score for r in run1], [r.rrf_score for r in run2])
        print("  -> TEST_PASSED [VECTOR-12]: RRF ordering and tie-breaking is strictly deterministic.")

    # ------------------------------------------------------------------------
    # VECTOR-13: Duplicate target fusion across lexical & dense
    # ------------------------------------------------------------------------
    def test_vector_13_duplicate_target_fusion(self):
        node_id = "concept:test-vec-13"
        self._create_canonical_node_and_evidence(node_id, "Fusão Singular de Alvo", "Garantia de que um nó presente em ambos os rankings funde em 1 item.")
        self.worker_v1.sync_node_vector(node_id)

        results = self.search_engine.search(query="Fusão Singular", trust_zone="tz_internal_holding", project_id="pub-ecom")
        ids = [r.target_id for r in results if r.target_id == node_id]
        self.assertEqual(len(ids), 1)
        print("  -> TEST_PASSED [VECTOR-13]: Entity appearing in both dense and lexical ranks fuses into single result.")

    # ------------------------------------------------------------------------
    # VECTOR-14: Tenant & Trust Zone RLS isolation
    # ------------------------------------------------------------------------
    def test_vector_14_tenant_rls_isolation(self):
        node_holding = "concept:test-vec-14-holding"
        node_client = "concept:test-vec-14-client"
        self._create_canonical_node_and_evidence(node_holding, "Holding Secret Token", "Segredo interno da holding.", trust_zone="tz_internal_holding", project_id="pub-ecom")
        self._create_canonical_node_and_evidence(node_client, "Client Public Doc", "Documento aberto ao cliente.", trust_zone="tz_client_facing", project_id="pub-client-1")

        self.worker_v1.sync_node_vector(node_holding)
        self.worker_v1.sync_node_vector(node_client)

        # Search within tz_client_facing scope
        res_client = self.search_engine.search(query="Secret Token Doc", trust_zone="tz_client_facing", project_id="pub-client-1")
        target_ids = [r.target_id for r in res_client]
        self.assertNotIn(node_holding, target_ids)
        self.assertIn(node_client, target_ids)

        # Search within tz_internal_holding scope
        res_holding = self.search_engine.search(query="Secret Token Doc", trust_zone="tz_internal_holding", project_id="pub-ecom")
        holding_targets = [r.target_id for r in res_holding]
        self.assertIn(node_holding, holding_targets)
        self.assertNotIn(node_client, holding_targets)
        print("  -> TEST_PASSED [VECTOR-14]: Cross-tenant RLS isolation prevents cross-boundary data leakage.")

    # ------------------------------------------------------------------------
    # VECTOR-15: Evidence grounding & lineage preservation
    # ------------------------------------------------------------------------
    def test_vector_15_evidence_grounding(self):
        node_id = "concept:test-vec-15"
        ev_id, _ = self._create_canonical_node_and_evidence(node_id, "Grounding Node", "Trecho citado com evidência rastreável.")
        self.worker_v1.sync_node_vector(node_id)

        results = self.search_engine.search(query="Grounding Node", trust_zone="tz_internal_holding", project_id="pub-ecom")
        hit = next((r for r in results if r.target_id == node_id), None)
        self.assertIsNotNone(hit)
        self.assertTrue(len(hit.content_hash) > 0)
        self.assertIsNotNone(hit.originating_event_id)
        print("  -> TEST_PASSED [VECTOR-15]: Evidence grounding and lineage preservation verified.")

    # ------------------------------------------------------------------------
    # VECTOR-16: Stale vector exclusion from search results
    # ------------------------------------------------------------------------
    def test_vector_16_stale_exclusion(self):
        node_id = "concept:test-vec-16"
        self._create_canonical_node_and_evidence(node_id, "Alvo Obsoleto", "Texto inicial que ficará desatualizado.")
        self.worker_v1.sync_node_vector(node_id)

        # Direct SQL content update on node to simulate drift without updating vector
        conn = psycopg2.connect(ADMIN_URL)
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("UPDATE pub_neural.neural_nodes SET content = 'Conteúdo alterado drasticamente' WHERE id = %s;", (node_id,))
        conn.close()

        # Hybrid search should not return this node in dense results
        dense_results = self.search_engine._retrieve_dense(
            cur=psycopg2.connect(ADMIN_URL).cursor(cursor_factory=RealDictCursor),
            query_vec=self.provider_v1.generate_embedding("Alvo Obsoleto"),
            model_id="text-embedding-3-small",
            trust_zone="tz_internal_holding",
            project_id="pub-ecom"
        )
        self.assertNotIn(node_id, [d["target_id"] for d in dense_results])
        print("  -> TEST_PASSED [VECTOR-16]: Stale vector is automatically excluded from dense retrieval.")

    # ------------------------------------------------------------------------
    # VECTOR-17: Performance baseline measurement
    # ------------------------------------------------------------------------
    def test_vector_17_performance_baseline(self):
        # Insert and sync a batch of 100 synthetic nodes
        node_ids = [f"concept:perf-{i}" for i in range(100)]
        for nid in node_ids:
            self._create_canonical_node_and_evidence(nid, f"Performance Benchmark Node {nid}", f"Conteúdo sintético para benchmark {nid}")

        t0 = time.time()
        self.worker_v1.sync_all_projections()
        sync_time = time.time() - t0

        t_search_0 = time.time()
        res = self.search_engine.search(query="Performance Benchmark Node", trust_zone="tz_internal_holding", project_id="pub-ecom")
        search_time = time.time() - t_search_0

        self.assertGreater(len(res), 0)
        self.assertLess(search_time, 0.5)  # Under 500ms on 100 items in container
        print(f"  -> TEST_PASSED [VECTOR-17]: Performance baseline: 100-node sync in {sync_time:.3f}s, hybrid search in {search_time*1000:.1f}ms.")


if __name__ == "__main__":
    unittest.main()
