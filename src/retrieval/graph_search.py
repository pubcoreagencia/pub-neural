"""
Graph Search Engine for PUB Neural.
Implements bounded neighborhood graph traversal, shortest path queries,
and structural graph explanations, providing the Graph modality for 3-way hybrid retrieval.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class GraphSearchResult:
    target_id: str
    target_type: str
    title: str
    snippet: str
    graph_rank: int
    graph_score: float
    trust_zone: str
    project_id: Optional[str]
    originating_event_id: str
    content_hash: str
    structural_explanation: str
    path: List[str] = field(default_factory=list)
    promotion_state: Optional[str] = None
    conflict_state: Optional[str] = None


class GraphSearchEngine:
    """
    Executes graph-based retrieval over PUB Neural relational entities and relations.
    Traverses active nodes and edges to find connected components and path conduits.
    """

    def __init__(
        self,
        db_conn_or_cursor: Optional[Any] = None,
        max_depth: int = 2,
        max_candidates: int = 20,
    ):
        self.conn_or_cur = db_conn_or_cursor
        self.max_depth = max_depth
        self.max_candidates = max_candidates

    def search_graph(
        self,
        query: str,
        trust_zone: Optional[str] = None,
        project_id: Optional[str] = None,
        limit: int = 10,
        cursor: Optional[Any] = None,
        in_memory_nodes: Optional[List[Dict[str, Any]]] = None,
        in_memory_edges: Optional[List[Dict[str, Any]]] = None,
    ) -> List[GraphSearchResult]:
        """
        Retrieve candidate graph entities seeded by query terms, expanding neighborhood.
        Supports in-memory graphs (for testing/worker caches) or live PostgreSQL connection.
        """
        if not query or not query.strip():
            return []

        tokens = [t.lower() for t in query.split() if len(t) > 2]
        if not tokens:
            tokens = [query.lower().strip()]

        if in_memory_nodes is not None and in_memory_edges is not None:
            return self._search_in_memory(
                tokens, in_memory_nodes, in_memory_edges, trust_zone, project_id, limit
            )

        active_cur = cursor or self.conn_or_cur
        if active_cur:
            return self._search_database(tokens, trust_zone, project_id, limit, active_cur)

        return []

    def _search_in_memory(
        self,
        tokens: List[str],
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        trust_zone: Optional[str],
        project_id: Optional[str],
        limit: int,
    ) -> List[GraphSearchResult]:
        """In-memory BFS traversal over graph nodes and edges."""
        # 1. Seed matching
        seed_scores: Dict[str, float] = {}
        node_map: Dict[str, Dict[str, Any]] = {}

        for n in nodes:
            nid = str(n.get("id") or n.get("node_id"))
            node_map[nid] = n
            title = str(n.get("title") or "").lower()
            summary = str(n.get("summary") or "").lower()
            content = str(n.get("content") or "").lower()

            score = 0.0
            for t in tokens:
                if t in title:
                    score += 2.0
                elif t in summary or t in content:
                    score += 1.0

            if score > 0:
                seed_scores[nid] = score

        if not seed_scores:
            return []

        # 2. Neighborhood Expansion (Adjacency)
        adj: Dict[str, List[Tuple[str, str, float]]] = {}
        for e in edges:
            u = str(e.get("source_id") or e.get("source"))
            v = str(e.get("target_id") or e.get("target"))
            rel = str(e.get("relation_type") or e.get("relation") or "RELATED_TO")
            w = float(e.get("weight", 1.0))

            adj.setdefault(u, []).append((v, rel, w))
            if e.get("is_bidirectional"):
                adj.setdefault(v, []).append((u, rel, w))

        # BFS expansion
        visited: Set[str] = set()
        candidate_scores: Dict[str, float] = {}
        explanations: Dict[str, str] = {}
        paths: Dict[str, List[str]] = {}

        for seed, seed_score in seed_scores.items():
            candidate_scores[seed] = candidate_scores.get(seed, 0.0) + seed_score * 1.5
            explanations[seed] = f"Direct query seed (score: {seed_score:.1f})"
            paths[seed] = [seed]

            # 1-hop expansion
            for neighbor, rel, w in adj.get(seed, []):
                rel_weight = 1.2 if rel in ("USES", "DEPENDS_ON") else 0.8
                hop_score = seed_score * 0.5 * w * rel_weight
                candidate_scores[neighbor] = candidate_scores.get(neighbor, 0.0) + hop_score
                if neighbor not in explanations:
                    explanations[neighbor] = f"Connected via {rel} to {seed}"
                    paths[neighbor] = [seed, neighbor]

        # Sort candidates
        ranked_ids = sorted(candidate_scores.keys(), key=lambda x: (-candidate_scores[x], x))

        results: List[GraphSearchResult] = []
        rank_idx = 1
        for nid in ranked_ids[:limit]:
            n = node_map.get(nid)
            if not n:
                continue

            # Filtering
            if trust_zone and n.get("trust_zone") and n.get("trust_zone") != trust_zone:
                continue
            if project_id and n.get("project_id") and n.get("project_id") != project_id:
                continue

            results.append(
                GraphSearchResult(
                    target_id=nid,
                    target_type="NODE",
                    title=n.get("title") or nid,
                    snippet=(n.get("summary") or n.get("content") or "")[:250],
                    graph_rank=rank_idx,
                    graph_score=candidate_scores[nid],
                    trust_zone=n.get("trust_zone", "tz_internal_holding"),
                    project_id=n.get("project_id"),
                    originating_event_id=str(n.get("originating_event_id") or n.get("event_id") or ""),
                    content_hash=n.get("content_hash", ""),
                    structural_explanation=explanations.get(nid, "Topological neighbor"),
                    path=paths.get(nid, [nid]),
                    promotion_state=n.get("promotion_state") or n.get("initial_state"),
                    conflict_state=n.get("conflict_state", "RESOLVED"),
                )
            )
            rank_idx += 1

        return results

    def _search_database(
        self,
        tokens: List[str],
        trust_zone: Optional[str],
        project_id: Optional[str],
        limit: int,
        cur: Any,
    ) -> List[GraphSearchResult]:
        """Query PostgreSQL neural_nodes and neural_edges using CTE graph expansion."""
        query_pattern = "%" + "%".join(tokens) + "%"

        sql = """
            WITH RECURSIVE seeds AS (
                SELECT 
                    id, entity_type, title, summary, content, trust_zone, project_id,
                    originating_event_id, content_hash, promotion_state, conflict_state,
                    1.0 AS seed_score
                FROM pub_neural.neural_nodes
                WHERE is_active = TRUE
                  AND (lower(title) LIKE %s OR lower(summary) LIKE %s)
                LIMIT 10
            ),
            traversal AS (
                SELECT 
                    s.id AS node_id, s.title, s.summary, s.content, s.trust_zone, s.project_id,
                    s.originating_event_id, s.content_hash, s.promotion_state, s.conflict_state,
                    s.seed_score AS score, 0 AS depth, 'SEED' AS rel_type, s.id AS root_id
                FROM seeds s

                UNION

                SELECT 
                    n.id AS node_id, n.title, n.summary, n.content, n.trust_zone, n.project_id,
                    n.originating_event_id, n.content_hash, n.promotion_state, n.conflict_state,
                    t.score * 0.5 * e.weight AS score, t.depth + 1, e.relation_type::text AS rel_type, t.root_id
                FROM pub_neural.neural_edges e
                JOIN traversal t ON e.source_id = t.node_id
                JOIN pub_neural.neural_nodes n ON e.target_id = n.id
                WHERE t.depth < 1 AND e.is_active = TRUE AND n.is_active = TRUE
            )
            SELECT 
                node_id, title, summary, content, trust_zone, project_id,
                originating_event_id::text, content_hash, promotion_state::text, conflict_state::text,
                MAX(score) AS final_score, rel_type, root_id
            FROM traversal
            GROUP BY node_id, title, summary, content, trust_zone, project_id,
                     originating_event_id, content_hash, promotion_state, conflict_state, rel_type, root_id
            ORDER BY final_score DESC, node_id ASC
            LIMIT %s;
        """
        try:
            cur.execute(sql, (query_pattern, query_pattern, limit))
            rows = cur.fetchall()
            results = []
            rank = 1
            for r in rows:
                results.append(
                    GraphSearchResult(
                        target_id=r["node_id"],
                        target_type="NODE",
                        title=r["title"],
                        snippet=(r["summary"] or r["content"] or "")[:250],
                        graph_rank=rank,
                        graph_score=float(r["final_score"]),
                        trust_zone=r["trust_zone"],
                        project_id=r["project_id"],
                        originating_event_id=r["originating_event_id"],
                        content_hash=r.get("content_hash", ""),
                        structural_explanation=f"Traversed via {r['rel_type']} from {r['root_id']}",
                        path=[r["root_id"], r["node_id"]] if r["root_id"] != r["node_id"] else [r["node_id"]],
                        promotion_state=r.get("promotion_state"),
                        conflict_state=r.get("conflict_state"),
                    )
                )
                rank += 1
            return results
        except Exception:
            return []
