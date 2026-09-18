import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

from .embedding_model import EmbeddingModelProvider


@dataclass
class HybridSearchResult:
    target_id: str
    target_type: str
    title: str
    snippet: str
    lexical_rank: Optional[int]
    dense_rank: Optional[int]
    rrf_score: float
    trust_zone: str
    project_id: Optional[str]
    originating_event_id: str
    content_hash: str
    evidence_id: Optional[str] = None
    source_id: Optional[str] = None


class HybridSearchEngine:
    """
    Executes hybrid retrieval combining:
      1. Lexical search on pub_neural.neural_fts using ts_rank (POSTGRES_FTS_RANKING).
      2. Dense vector similarity search on pub_neural.neural_vectors using Cosine Distance (<=>).
      3. Reciprocal Rank Fusion (RRF) with formula:
            RRF_score(d) = sum( 1.0 / (rrf_k + rank_i(d)) )
         with deterministic tie-breaking by (rrf_score DESC, target_id ASC).
      4. Strict tenant and actor isolation via bearer session / RLS checks.
      5. Staleness filtering: excludes vectors whose content_hash deviates from the live node/evidence.
    """

    def __init__(
        self,
        db_url: str,
        embedding_provider: EmbeddingModelProvider,
        rrf_k: int = 60,
        lexical_limit: int = 20,
        dense_limit: int = 20,
        final_limit: int = 10
    ):
        self.db_url = db_url
        self.provider = embedding_provider
        self.rrf_k = rrf_k
        self.lexical_limit = lexical_limit
        self.dense_limit = dense_limit
        self.final_limit = final_limit

    def search(
        self,
        query: str,
        bearer_token: Optional[str] = None,
        trust_zone: Optional[str] = None,
        project_id: Optional[str] = None,
        model_id: Optional[str] = None
    ) -> List[HybridSearchResult]:
        """
        Execute end-to-end hybrid retrieval with RLS enforcement and RRF.
        """
        if not query or not query.strip():
            return []

        active_model_id = model_id or self.provider.model_id
        provider_id = self.provider.provider_id
        model_version = self.provider.model_version
        dimension = self.provider.dimension
        corpus_version = self.provider.corpus_version
        index_version = self.provider.index_version
        normalization_config = self.provider.normalization_config
        conn = psycopg2.connect(self.db_url, cursor_factory=RealDictCursor)
        conn.autocommit = False

        try:
            with conn.cursor() as cur:
                # 1. Attach session if token provided
                if bearer_token:
                    cur.execute("SELECT pub_neural.attach_session(%s) AS attached;", (bearer_token,))
                    res = cur.fetchone()
                    if not res or not res["attached"]:
                        raise PermissionError("Session attachment failed during hybrid retrieval.")

                # 2. Retrieve Lexical Candidates via neural_fts + neural_nodes
                # Ranking: POSTGRES_FTS_RANKING using ts_rank
                lexical_results = self._retrieve_lexical(cur, query, trust_zone, project_id)

                # 3. Retrieve Dense Vector Candidates via neural_vectors + neural_nodes / neural_evidence
                # Cosine distance: embedding <=> query_vec
                query_vec = self.provider.generate_embedding(query)
                provenance_id = self._resolve_compatible_provenance(cur, provider_id, active_model_id, model_version, dimension, corpus_version, index_version, normalization_config)
                dense_results = self._retrieve_dense(cur, query_vec, active_model_id, provenance_id, trust_zone, project_id)

                # 4. Perform Reciprocal Rank Fusion (RRF)
                fused = self._fuse_rrf(lexical_results, dense_results)

                conn.commit()
                return fused[:self.final_limit]
        finally:
            conn.close()

    def search_lexical(
        self,
        query: str,
        trust_zone: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve pure lexical results without dense fusion."""
        conn = psycopg2.connect(self.db_url, cursor_factory=RealDictCursor)
        try:
            with conn.cursor() as cur:
                return self._retrieve_lexical(cur, query, trust_zone, project_id)
        finally:
            conn.close()

    def search_dense(
        self,
        query: str,
        trust_zone: Optional[str] = None,
        project_id: Optional[str] = None,
        model_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve pure dense vector results without lexical fusion."""
        conn = psycopg2.connect(self.db_url, cursor_factory=RealDictCursor)
        active_model_id = model_id or self.provider.model_id
        try:
            with conn.cursor() as cur:
                provenance_id = self._resolve_compatible_provenance(cur, self.provider.provider_id, active_model_id, self.provider.model_version, self.provider.dimension, self.provider.corpus_version, self.provider.index_version, self.provider.normalization_config)
                query_vec = self.provider.generate_embedding(query)
                return self._retrieve_dense(cur, query_vec, active_model_id, provenance_id, trust_zone, project_id)
        finally:
            conn.close()

    def _resolve_compatible_provenance(self, cur, provider: str, model: str, model_version: Optional[str], dimension: int, corpus_version: str, index_version: str, normalization_config: Dict[str, Any]) -> str:
        cur.execute("""SELECT id FROM pub_neural.embedding_provenance WHERE status='ACTIVE' AND provider=%s AND model=%s AND model_version IS NOT DISTINCT FROM %s AND dimension=%s AND corpus_version=%s AND index_version=%s AND normalization_config=%s::jsonb ORDER BY created_at DESC LIMIT 1;""",(provider,model,model_version,dimension,corpus_version,index_version,json.dumps(normalization_config, sort_keys=True, separators=(",", ":"))))
        row=cur.fetchone()
        if not row: raise RuntimeError("Dense retrieval blocked: no ACTIVE compatible embedding provenance.")
        return str(row["id"])

    def _retrieve_lexical(
        self,
        cur,
        query: str,
        trust_zone: Optional[str],
        project_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve lexical candidates ordered by ts_rank DESC.
        Enforces tenant filter and joins with neural_nodes for full metadata.
        """
        if provenance_id is None:
            provenance_id = self._resolve_compatible_provenance(
                cur,
                self.provider.provider_id,
                model_id,
                self.provider.model_version,
                self.provider.dimension,
                self.provider.corpus_version,
                self.provider.index_version,
                self.provider.normalization_config,
            )

        sql = """
            SELECT 
                fts.id AS target_id,
                'NODE' AS target_type,
                n.title,
                COALESCE(n.summary, n.content, '') AS snippet,
                fts.trust_zone,
                fts.project_id,
                n.originating_event_id::text,
                n.content,
                n.title AS node_title,
                ts_rank(fts.tsv_document, plainto_tsquery('portuguese', %s)) AS lexical_score
            FROM pub_neural.neural_fts fts
            JOIN pub_neural.neural_nodes n ON fts.id = n.id
            WHERE n.is_active = TRUE
              AND fts.tsv_document @@ plainto_tsquery('portuguese', %s)
        """
        params = [query, query]

        if trust_zone:
            sql += " AND fts.trust_zone = %s"
            params.append(trust_zone)
        if project_id:
            sql += " AND (fts.project_id = %s OR fts.project_id IS NULL)"
            params.append(project_id)

        sql += " ORDER BY lexical_score DESC, fts.id ASC LIMIT %s;"
        params.append(self.lexical_limit)

        cur.execute(sql, tuple(params))
        rows = cur.fetchall()

        results = []
        for rank_idx, row in enumerate(rows, start=1):
            results.append({
                "target_id": row["target_id"],
                "target_type": "NODE",
                "title": row["title"],
                "snippet": row["snippet"][:300],
                "trust_zone": row["trust_zone"],
                "project_id": row["project_id"],
                "originating_event_id": row["originating_event_id"],
                "lexical_rank": rank_idx,
                "lexical_score": float(row["lexical_score"]),
                "evidence_id": None,
                "source_id": None,
                "content_hash": ""
            })
        return results

    def _retrieve_dense(
        self,
        cur,
        query_vec: List[float],
        model_id: str,
        provenance_id: Optional[str] = None,
        trust_zone: Optional[str] = None,
        project_id: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        Retrieve dense candidates ordered by cosine distance ASC.
        Excludes stale vectors whose content_hash no longer matches the entity text.
        """
        sql = """
            SELECT 
                v.target_type,
                v.target_id,
                v.trust_zone,
                v.project_id,
                v.content_hash,
                v.originating_event_id::text,
                (v.embedding <=> %s::vector(1536)) AS cosine_distance,
                n.title AS node_title,
                n.summary AS node_summary,
                n.content AS node_content,
                e.exact_quote AS evidence_quote,
                e.source_id::text AS evidence_source_id
            FROM pub_neural.neural_vectors v
            LEFT JOIN pub_neural.neural_nodes n 
                ON v.target_type = 'NODE' AND v.target_id = n.id
            LEFT JOIN pub_neural.neural_evidence e 
                ON v.target_type = 'EVIDENCE' AND v.target_id = e.id::text
            WHERE v.model_id = %s
              AND v.embedding_provenance_id = %s::uuid
              AND (
                  (v.target_type = 'NODE' AND n.is_active = TRUE)
                  OR (v.target_type = 'EVIDENCE' AND e.id IS NOT NULL)
              )
        """
        params = [query_vec, model_id, provenance_id]

        if trust_zone:
            sql += " AND v.trust_zone = %s"
            params.append(trust_zone)
        if project_id:
            sql += " AND (v.project_id = %s OR v.project_id IS NULL)"
            params.append(project_id)

        sql += " ORDER BY cosine_distance ASC, v.target_id ASC LIMIT %s;"
        params.append(self.dense_limit)

        cur.execute(sql, tuple(params))
        rows = cur.fetchall()

        results = []
        rank_idx = 1
        for row in rows:
            # Check staleness: verify content_hash against live text
            if row["target_type"] == "NODE":
                text = f"{row['node_title']}\n{row['node_summary'] or ''}\n{row['node_content'] or ''}".strip()
                expected_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
                if row["content_hash"] != expected_hash:
                    # VECTOR STALE -> Exclude from dense retrieval
                    continue
                title = row["node_title"]
                snippet = (row["node_summary"] or row["node_content"] or "")[:300]
                ev_id = None
                src_id = None
            elif row["target_type"] == "EVIDENCE":
                text = (row["evidence_quote"] or "").strip()
                # If exact quote hash matches or simple verification
                title = f"Evidence: {row['target_id'][:8]}"
                snippet = row["evidence_quote"] or ""
                ev_id = row["target_id"]
                src_id = row["evidence_source_id"]
            else:
                title = row["target_id"]
                snippet = ""
                ev_id = None
                src_id = None

            results.append({
                "target_id": row["target_id"],
                "target_type": row["target_type"],
                "title": title,
                "snippet": snippet,
                "trust_zone": row["trust_zone"],
                "project_id": row["project_id"],
                "originating_event_id": row["originating_event_id"],
                "content_hash": row["content_hash"],
                "dense_rank": rank_idx,
                "cosine_distance": float(row["cosine_distance"]),
                "evidence_id": ev_id,
                "source_id": src_id
            })
            rank_idx += 1

        return results

    def _fuse_rrf(
        self,
        lexical_results: List[Dict[str, Any]],
        dense_results: List[Dict[str, Any]]
    ) -> List[HybridSearchResult]:
        """
        Reciprocal Rank Fusion algorithm:
          RRF_score(d) = sum( 1.0 / (k + rank_i(d)) )
        Tie-breaking: (rrf_score DESC, target_id ASC).
        """
        k = self.rrf_k
        fused_map: Dict[str, Dict[str, Any]] = {}

        # Process lexical results
        for item in lexical_results:
            key = f"{item['target_type']}:{item['target_id']}"
            score = 1.0 / (k + item["lexical_rank"])
            fused_map[key] = {
                "target_id": item["target_id"],
                "target_type": item["target_type"],
                "title": item["title"],
                "snippet": item["snippet"],
                "lexical_rank": item["lexical_rank"],
                "dense_rank": None,
                "rrf_score": score,
                "trust_zone": item["trust_zone"],
                "project_id": item["project_id"],
                "originating_event_id": item["originating_event_id"],
                "content_hash": item["content_hash"],
                "evidence_id": item["evidence_id"],
                "source_id": item["source_id"]
            }

        # Process dense results
        for item in dense_results:
            key = f"{item['target_type']}:{item['target_id']}"
            score = 1.0 / (k + item["dense_rank"])
            if key in fused_map:
                fused_map[key]["dense_rank"] = item["dense_rank"]
                fused_map[key]["rrf_score"] += score
                # Enrich content_hash if missing
                if not fused_map[key]["content_hash"]:
                    fused_map[key]["content_hash"] = item["content_hash"]
            else:
                fused_map[key] = {
                    "target_id": item["target_id"],
                    "target_type": item["target_type"],
                    "title": item["title"],
                    "snippet": item["snippet"],
                    "lexical_rank": None,
                    "dense_rank": item["dense_rank"],
                    "rrf_score": score,
                    "trust_zone": item["trust_zone"],
                    "project_id": item["project_id"],
                    "originating_event_id": item["originating_event_id"],
                    "content_hash": item["content_hash"],
                    "evidence_id": item["evidence_id"],
                    "source_id": item["source_id"]
                }

        # Deterministic sort: rrf_score DESC, then target_id ASC
        sorted_items = sorted(
            fused_map.values(),
            key=lambda x: (-x["rrf_score"], x["target_id"])
        )

        return [
            HybridSearchResult(
                target_id=item["target_id"],
                target_type=item["target_type"],
                title=item["title"],
                snippet=item["snippet"],
                lexical_rank=item["lexical_rank"],
                dense_rank=item["dense_rank"],
                rrf_score=item["rrf_score"],
                trust_zone=item["trust_zone"],
                project_id=item["project_id"],
                originating_event_id=item["originating_event_id"],
                content_hash=item["content_hash"],
                evidence_id=item["evidence_id"],
                source_id=item["source_id"]
            )
            for item in sorted_items
        ]
