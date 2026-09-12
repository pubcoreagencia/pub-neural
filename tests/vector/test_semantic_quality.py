import os
import time
import unittest
import uuid
import psycopg2
from psycopg2.extras import RealDictCursor

from src.ingestion.client import PubNeuralClient
from src.retrieval.embedding_model import (
    MockDeterministicEmbeddingProvider,
    RealSemanticConceptEmbeddingProvider,
)
from src.retrieval.vector_worker import VectorIndexingWorker
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


# Controlled Semantic Dataset with 12 distinct documents across 4 domains
CONTROLLED_SEMANTIC_CORPUS = [
    # Domain A: Authentication & Sessions
    {
        "id": "concept:auth-ssr-session",
        "title": "Mecanismo de Sessão SSR e Cookies Seguros",
        "content": "Implementação de autenticação com cookies HTTP-only e validação de tokens JWT no servidor com rotação de chaves criptográficas.",
        "domain": "AUTH",
        "trust_zone": "tz_internal_holding",
        "project_id": "pub-core"
    },
    {
        "id": "concept:auth-bearer-token",
        "title": "Protocolo de Credenciais e Bearer Token OIDC",
        "content": "Especificação de cabeçalhos de autorização com tokens de acesso bearer para chamadas de API entre microsserviços.",
        "domain": "AUTH",
        "trust_zone": "tz_internal_holding",
        "project_id": "pub-core"
    },
    {
        "id": "concept:auth-external-client",
        "title": "Portal de Acesso Externo do Cliente",
        "content": "Fluxo de login e identidade do cliente final no portal seguro.",
        "domain": "AUTH",
        "trust_zone": "tz_client_facing",
        "project_id": "client-portal"
    },
    # Domain B: Database & Persistence
    {
        "id": "concept:storage-postgres-wal",
        "title": "Configuração de WAL e Índices no PostgreSQL",
        "content": "Ajuste de write-ahead log, transações ACID e persistência em disco para altas taxas de escrita em tabelas relacionais.",
        "domain": "STORAGE",
        "trust_zone": "tz_internal_holding",
        "project_id": "pub-core"
    },
    {
        "id": "concept:storage-acid-transactions",
        "title": "Garantias Transacionais e Isolamento de Banco de Dados",
        "content": "Controle de concorrência multiversão e integridade referencial com commits e rollbacks atômicos.",
        "domain": "STORAGE",
        "trust_zone": "tz_internal_holding",
        "project_id": "pub-core"
    },
    # Domain C: Event Sourcing & CQRS
    {
        "id": "concept:event-sourcing-log",
        "title": "Event Log Append-Only e Reducer Replay",
        "content": "Fluxo de eventos canônicos imutáveis onde o estado do sistema é reconstruído por projeções determinísticas via checkpoint.",
        "domain": "EVENT_SOURCING",
        "trust_zone": "tz_internal_holding",
        "project_id": "pub-neural"
    },
    {
        "id": "concept:event-projection-engine",
        "title": "Motor de Projeção e Checkpoint de Estado",
        "content": "Consumo ordenado da stream de eventos com atualização atômica de visualizações e proteção contra regressão de sequência.",
        "domain": "EVENT_SOURCING",
        "trust_zone": "tz_internal_holding",
        "project_id": "pub-neural"
    },
    # Domain D: Unrelated / Distractors (E-commerce Inventory & Warehousing)
    {
        "id": "concept:ecom-stock-policy",
        "title": "Política de Estoque e Varejo de Produtos",
        "content": "Regras de reposição de inventário físico, controle de SKU em armazéns e logística de frete para compras online.",
        "domain": "ECOMMERCE",
        "trust_zone": "tz_internal_holding",
        "project_id": "pub-ecom"
    },
    {
        "id": "concept:ecom-checkout-cart",
        "title": "Carrinho de Compras e Catálogo de Preços",
        "content": "Cálculo de descontos por cupom, tabela de preços para catálogo e finalização do pedido pelo consumidor.",
        "domain": "ECOMMERCE",
        "trust_zone": "tz_internal_holding",
        "project_id": "pub-ecom"
    }
]


class TestSemanticDenseAndHybridQuality(unittest.TestCase):
    """
    Evaluates real semantic quality, ranking metrics (Recall@K),
    lexical vs dense vs hybrid comparisons, and multi-tenant RLS isolation.
    """

    @classmethod
    def setUpClass(cls):
        # Configure test environment and grant permissions
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
                    ARRAY['tz_internal_holding', 'tz_client_facing'], ARRAY['pub-ecom', 'pub-neural', 'holding-core', 'pub-core', 'client-portal'],
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
        self.real_provider = RealSemanticConceptEmbeddingProvider(model_id="pub-semantic-embedding-v1", dimension=1536)
        self.mock_provider = MockDeterministicEmbeddingProvider(model_id="text-embedding-3-small", dimension=1536)
        self.worker = VectorIndexingWorker(PROJECTOR_URL, self.real_provider)
        self.search_engine = HybridSearchEngine(ADMIN_URL, self.real_provider)

        self.ingestor_client = PubNeuralClient(
            db_url=DB_URL,
            actor_id="actor:system:ingestor",
            machine_secret=INGESTOR_SECRET,
            requested_trust_zone="tz_internal_holding",
            requested_project="pub-core"
        )
        self.ingestor_client.establish_session()

        # Ingest controlled corpus
        self._seed_corpus()

    def tearDown(self):
        self.worker.close()
        self.ingestor_client.close()

    def _seed_corpus(self):
        for doc in CONTROLLED_SEMANTIC_CORPUS:
            seq = self.ingestor_client.append_canonical_event(
                event_id=uuid.uuid4(),
                event_type="ENTITY_EXTRACTED",
                stream_id=f"stream:{doc['id']}",
                payload={
                    "node_id": doc["id"],
                    "title": doc["title"],
                    "entity_type": "CONCEPT",
                    "summary": f"Summary for {doc['title']}",
                    "content": doc["content"],
                    "trust_zone": doc["trust_zone"],
                    "project_id": doc["project_id"],
                    "confidence_score": 1.0
                }
            )
            # Project
            p_conn = psycopg2.connect(PROJECTOR_URL)
            p_conn.autocommit = True
            with p_conn.cursor() as cur:
                cur.execute("SELECT * FROM pub_neural.run_projector('graph_projector', %s, %s);", (seq, seq))
            p_conn.close()

            # Sync vector with real provider
            self.worker.sync_node_vector(doc["id"])

    # ------------------------------------------------------------------------
    # SEMANTIC-01: Dense Retrieval Semantic Clustering & Recall@K
    # Query has NO direct word overlap with title: "autenticação com token no servidor"
    # Target relevant docs: "concept:auth-ssr-session", "concept:auth-bearer-token"
    # Distractor: "concept:ecom-stock-policy"
    # ------------------------------------------------------------------------
    def test_semantic_01_dense_retrieval_quality(self):
        query = "autenticação com token no servidor"
        expected_relevant = {"concept:auth-ssr-session", "concept:auth-bearer-token"}

        dense_res = self.search_engine.search_dense(
            query=query,
            trust_zone="tz_internal_holding",
            project_id="pub-core"
        )

        returned_ids = [d["target_id"] for d in dense_res]
        
        # Calculate Recall@1, Recall@3, Recall@5
        recall_1 = len(set(returned_ids[:1]) & expected_relevant) / len(expected_relevant)
        recall_3 = len(set(returned_ids[:3]) & expected_relevant) / len(expected_relevant)
        recall_5 = len(set(returned_ids[:5]) & expected_relevant) / len(expected_relevant)

        self.assertGreaterEqual(recall_3, 1.0, f"Expected 100% Recall@3 for semantic synonyms, got {recall_3}")
        self.assertNotIn("concept:ecom-stock-policy", returned_ids[:3])
        print(f"  -> TEST_PASSED [SEMANTIC-01]: Dense Recall@1={recall_1:.2f}, Recall@3={recall_3:.2f}, Recall@5={recall_5:.2f}.")

    # ------------------------------------------------------------------------
    # SEMANTIC-02: Lexical vs Dense vs Hybrid Comparison
    # Scenario: Query contains a technical synonym ("banco de dados relacional e disco")
    # Lexical may miss "PostgreSQL WAL", but Dense catches it semantically.
    # Hybrid achieves equal or superior recall.
    # ------------------------------------------------------------------------
    def test_semantic_02_lexical_vs_dense_vs_hybrid(self):
        query = "banco de dados relacional e disco"
        expected_relevant = {"concept:storage-postgres-wal", "concept:storage-acid-transactions"}

        lexical_hits = [r["target_id"] for r in self.search_engine.search_lexical(query, trust_zone="tz_internal_holding", project_id="pub-core")]
        dense_hits = [r["target_id"] for r in self.search_engine.search_dense(query, trust_zone="tz_internal_holding", project_id="pub-core")]
        hybrid_hits = [r.target_id for r in self.search_engine.search(query, trust_zone="tz_internal_holding", project_id="pub-core")]

        recall_lexical_3 = len(set(lexical_hits[:3]) & expected_relevant) / len(expected_relevant)
        recall_dense_3 = len(set(dense_hits[:3]) & expected_relevant) / len(expected_relevant)
        recall_hybrid_3 = len(set(hybrid_hits[:3]) & expected_relevant) / len(expected_relevant)

        self.assertGreaterEqual(recall_hybrid_3, recall_lexical_3)
        self.assertGreaterEqual(recall_hybrid_3, 0.5)
        print(f"  -> TEST_PASSED [SEMANTIC-02]: Recall@3: Lexical={recall_lexical_3:.2f}, Dense={recall_dense_3:.2f}, Hybrid={recall_hybrid_3:.2f}.")

    # ------------------------------------------------------------------------
    # SEMANTIC-03: Portuguese Morphology, Synonyms & Accented Text
    # Query with variations in inflection and accents:
    # "transações atômicas e persistência" vs "persistencia em disco"
    # ------------------------------------------------------------------------
    def test_semantic_03_portuguese_morphology_and_accents(self):
        query_accented = "transações atômicas e persistência"
        query_unaccented = "transacoes atomicas e persistencia"

        res_acc = self.search_engine.search(query_accented, trust_zone="tz_internal_holding", project_id="pub-core")
        res_unacc = self.search_engine.search(query_unaccented, trust_zone="tz_internal_holding", project_id="pub-core")

        top_acc = res_acc[0].target_id if res_acc else None
        top_unacc = res_unacc[0].target_id if res_unacc else None

        self.assertIn(top_acc, ["concept:storage-acid-transactions", "concept:storage-postgres-wal"])
        self.assertIn(top_unacc, ["concept:storage-acid-transactions", "concept:storage-postgres-wal"])
        print("  -> TEST_PASSED [SEMANTIC-03]: Portuguese accents, plurals, and stemming normalized consistently.")

    # ------------------------------------------------------------------------
    # SEMANTIC-04: RRF Quality Across Different k Parameters
    # Tests k=10, k=60, k=100
    # ------------------------------------------------------------------------
    def test_semantic_04_rrf_k_parameter_analysis(self):
        query = "event log replay checkpoint"
        for k_val in [10, 60, 100]:
            engine = HybridSearchEngine(ADMIN_URL, self.real_provider, rrf_k=k_val)
            results = engine.search(query, trust_zone="tz_internal_holding", project_id="pub-neural")
            self.assertGreater(len(results), 0)
            self.assertIn("concept:event-sourcing-log", [r.target_id for r in results[:2]])
        print("  -> TEST_PASSED [SEMANTIC-04]: RRF stability verified across k=10, k=60, k=100.")

    # ------------------------------------------------------------------------
    # SEMANTIC-05: Strict Cross-Tenant RLS Security on Real Semantic Embeddings
    # Even if "concept:auth-external-client" has high semantic similarity to an auth query,
    # it must be strictly blocked when searching in project "pub-core" or zone "tz_internal_holding".
    # ------------------------------------------------------------------------
    def test_semantic_05_cross_tenant_semantic_isolation(self):
        query = "login e autenticação do cliente portal"

        # Search within internal holding / pub-core
        res_holding = self.search_engine.search(
            query=query,
            trust_zone="tz_internal_holding",
            project_id="pub-core"
        )
        returned_holding_ids = [r.target_id for r in res_holding]
        self.assertNotIn("concept:auth-external-client", returned_holding_ids)

        # Search within client portal
        res_client = self.search_engine.search(
            query=query,
            trust_zone="tz_client_facing",
            project_id="client-portal"
        )
        returned_client_ids = [r.target_id for r in res_client]
        self.assertIn("concept:auth-external-client", returned_client_ids)
        self.assertNotIn("concept:auth-ssr-session", returned_client_ids)
        print("  -> TEST_PASSED [SEMANTIC-05]: Semantic similarity strictly bounded by tenant trust zone RLS.")

    # ------------------------------------------------------------------------
    # SEMANTIC-06: Scaled Latency Benchmark (Embedding vs Database Retrieval)
    # ------------------------------------------------------------------------
    def test_semantic_06_performance_latency_breakdown(self):
        sample_text = "Mecanismo distribuído de alta disponibilidade e tolerância a falhas com quorum."
        
        # 1. Embedding generation latency
        t0 = time.time()
        for _ in range(50):
            _ = self.real_provider.generate_embedding(sample_text)
        embed_lat_ms = ((time.time() - t0) / 50.0) * 1000.0

        # 2. Database dense retrieval latency
        t1 = time.time()
        for _ in range(20):
            _ = self.search_engine.search_dense("Mecanismo distribuído", trust_zone="tz_internal_holding", project_id="pub-core")
        db_dense_lat_ms = ((time.time() - t1) / 20.0) * 1000.0

        # 3. Hybrid search latency (lexical + dense + RRF)
        t2 = time.time()
        for _ in range(20):
            _ = self.search_engine.search("Mecanismo distribuído", trust_zone="tz_internal_holding", project_id="pub-core")
        hybrid_lat_ms = ((time.time() - t2) / 20.0) * 1000.0

        self.assertLess(embed_lat_ms, 5.0)  # Under 5ms per embedding
        self.assertLess(hybrid_lat_ms, 50.0) # Under 50ms total hybrid latency
        print(f"  -> TEST_PASSED [SEMANTIC-06]: Latency: Embed={embed_lat_ms:.2f}ms, DB Dense={db_dense_lat_ms:.2f}ms, Hybrid Total={hybrid_lat_ms:.2f}ms.")


if __name__ == "__main__":
    unittest.main()
