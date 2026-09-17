"""
Research Graph Intelligence for PUB Neural.
Enables developers, agents, and researchers to traverse and query the codebase graph:
- Component dependencies and callers/callees.
- Path discovery between arbitrary concepts.
- Hub / God-node detection.
- Change impact and affected components analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class PathResult:
    source: str
    target: str
    length: int
    path: List[str]
    relations: List[str]
    explanation: str


@dataclass
class ComponentDependencySummary:
    component_id: str
    dependencies: List[str]
    dependents: List[str]
    total_degree: int
    is_hub: bool


@dataclass
class AffectedAnalysisResult:
    changed_nodes: List[str]
    affected_nodes: List[str]
    depth: int
    propagation_paths: Dict[str, List[str]]


class ResearchGraphIntelligence:
    """
    Cognitive intelligence service operating over the PUB Neural knowledge graph.
    Translates structural topological queries into grounded research findings.
    Works with native pure-Python graph representation with zero mandatory external C-deps.
    """

    def __init__(self):
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.out_edges: Dict[str, List[Tuple[str, str, float]]] = {}  # u -> [(v, rel, weight)]
        self.in_edges: Dict[str, List[Tuple[str, str, float]]] = {}   # v -> [(u, rel, weight)]

    @classmethod
    def from_database(
        cls,
        cursor: Any,
        project_id: Optional[str] = None,
        trust_zone: Optional[str] = None,
        limit: int = 500,
    ) -> ResearchGraphIntelligence:
        """Construct research intelligence from live canonical PostgreSQL neural_nodes and neural_edges."""
        intel = cls()

        node_sql = """
            SELECT id, title, entity_type, summary, content, trust_zone, project_id, confidence_score
            FROM pub_neural.neural_nodes
            WHERE is_active = TRUE
        """
        node_params = []
        if trust_zone:
            node_sql += " AND trust_zone = %s"
            node_params.append(trust_zone)
        if project_id:
            node_sql += " AND (project_id = %s OR project_id IS NULL)"
            node_params.append(project_id)
        node_sql += " LIMIT %s;"
        node_params.append(limit)

        cursor.execute(node_sql, tuple(node_params))
        node_rows = cursor.fetchall()

        node_ids = set()
        for r in node_rows:
            nid = str(r["id"])
            node_ids.add(nid)
            intel.nodes[nid] = {
                "title": r["title"],
                "entity_type": str(r["entity_type"]),
                "summary": r.get("summary"),
                "content": r.get("content"),
                "confidence_score": float(r.get("confidence_score", 1.0)),
                "project_id": r.get("project_id"),
                "trust_zone": r.get("trust_zone"),
            }
            intel.out_edges[nid] = []
            intel.in_edges[nid] = []

        if node_ids:
            edge_sql = """
                SELECT source_id, target_id, relation_type, weight
                FROM pub_neural.neural_edges
                WHERE is_active = TRUE
                  AND source_id = ANY(%s)
                  AND target_id = ANY(%s);
            """
            cursor.execute(edge_sql, (list(node_ids), list(node_ids)))
            edge_rows = cursor.fetchall()
            for er in edge_rows:
                u, v = str(er["source_id"]), str(er["target_id"])
                rel = str(er["relation_type"])
                w = float(er.get("weight", 1.0))
                intel.out_edges.setdefault(u, []).append((v, rel, w))
                intel.in_edges.setdefault(v, []).append((u, rel, w))

        return intel

    @classmethod
    def from_normalized_graph(cls, normalized_graph: Any) -> ResearchGraphIntelligence:
        """Construct research intelligence directly from NormalizedGraph."""
        intel = cls()
        for node in normalized_graph.nodes:
            intel.nodes[node.node_id] = {
                "title": node.title,
                "entity_type": node.entity_type,
                "source_file": node.source_file,
                "confidence_score": node.confidence_score,
            }
            intel.out_edges[node.node_id] = []
            intel.in_edges[node.node_id] = []

        for edge in normalized_graph.edges:
            u, v = edge.source_id, edge.target_id
            intel.out_edges.setdefault(u, []).append((v, edge.relation_type, edge.weight))
            intel.in_edges.setdefault(v, []).append((u, edge.relation_type, edge.weight))

        return intel

    def find_shortest_path(self, source_id: str, target_id: str) -> Optional[PathResult]:
        """Find the shortest structural path between two nodes via BFS."""
        if source_id not in self.nodes or target_id not in self.nodes:
            return None

        if source_id == target_id:
            return PathResult(
                source=source_id,
                target=target_id,
                length=0,
                path=[source_id],
                relations=[],
                explanation=f"{source_id} (identity)",
            )

        # BFS queue: (current_node, [path_nodes], [relations])
        visited = {source_id}
        queue = [(source_id, [source_id], [])]

        while queue:
            curr, curr_path, curr_rels = queue.pop(0)

            for nxt, rel, _ in self.out_edges.get(curr, []):
                if nxt == target_id:
                    final_path = curr_path + [nxt]
                    final_rels = curr_rels + [rel]
                    explanation = " -> ".join(
                        f"{final_path[i]} -[{final_rels[i]}]->" for i in range(len(final_rels))
                    ) + f" {target_id}"

                    return PathResult(
                        source=source_id,
                        target=target_id,
                        length=len(final_rels),
                        path=final_path,
                        relations=final_rels,
                        explanation=explanation,
                    )

                if nxt not in visited:
                    visited.add(nxt)
                    queue.append((nxt, curr_path + [nxt], curr_rels + [rel]))

        return None

    def analyze_dependencies(self, component_id: str) -> Optional[ComponentDependencySummary]:
        """Analyze outbound dependencies and inbound dependents of a component."""
        if component_id not in self.nodes:
            return None

        deps = [v for v, _, _ in self.out_edges.get(component_id, [])]
        dependents = [u for u, _, _ in self.in_edges.get(component_id, [])]
        total_deg = len(deps) + len(dependents)

        return ComponentDependencySummary(
            component_id=component_id,
            dependencies=deps,
            dependents=dependents,
            total_degree=total_deg,
            is_hub=total_deg >= 10,
        )

    def detect_god_nodes(self, top_n: int = 5) -> List[Tuple[str, int]]:
        """Identify high-degree hub nodes in the architecture."""
        degrees = [
            (nid, len(self.out_edges.get(nid, [])) + len(self.in_edges.get(nid, [])))
            for nid in self.nodes
        ]
        degrees.sort(key=lambda x: (-x[1], x[0]))
        return degrees[:top_n]

    def analyze_affected_components(
        self, changed_nodes: List[str], max_depth: int = 2
    ) -> AffectedAnalysisResult:
        """
        Compute ripple effect: which components depend on or are affected by changed nodes.
        Follows predecessor (inbound caller) links backwards from changed nodes.
        """
        affected: Set[str] = set()
        paths: Dict[str, List[str]] = {}

        for root in changed_nodes:
            if root not in self.nodes:
                continue

            # BFS upstream through predecessors
            visited = {root}
            queue = [(root, 0, [root])]
            while queue:
                curr, d, curr_path = queue.pop(0)
                if d > 0:
                    affected.add(curr)
                    if curr not in paths or len(curr_path) < len(paths[curr]):
                        paths[curr] = curr_path

                if d < max_depth:
                    for pred, _, _ in self.in_edges.get(curr, []):
                        if pred not in visited:
                            visited.add(pred)
                            queue.append((pred, d + 1, curr_path + [pred]))

        return AffectedAnalysisResult(
            changed_nodes=changed_nodes,
            affected_nodes=sorted(list(affected)),
            depth=max_depth,
            propagation_paths=paths,
        )
