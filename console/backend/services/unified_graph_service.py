"""
Unified Graph Service for PUB Neural Console V0.
Provides a unified projection of Physical Source-of-Truth (Git / 55 repositories)
and Cognitive Institutional Graph (Nodes, Edges, Policies, Decisions, Rules, Lessons).

Guarantees:
1. No duplicate canonical ontology or persistence layer.
2. Evidence-First Policy:
   - Factual links (EXTRACTED) have verified source and evidence locators.
   - Heuristic / inferred links (INFERRED) carry clear confidence and reasoning.
   - Candidates (PROPOSED) remain distinct and never promoted silently.
3. Level-of-Detail (LOD):
   - Level 0: Organization -> 55 Repositories + Institutional Backbone Nodes + Bridges.
   - Lazy expansion for subtrees.
"""

from typing import Any, Dict, List, Optional, Set

from console.backend.models import (
    EdgeDetailDTO,
    EvidenceLocatorDTO,
    GraphEdgeDTO,
    GraphNodeDTO,
    GraphResponseDTO,
)
from console.backend.services.git_graph_service import (
    CANONICAL_ORG,
    get_organization_graph,
    get_git_topology,
    get_git_node_detail,
    get_git_edge_detail,
)
from console.backend.services.graph_service import (
    get_graph_backbone,
    get_entity_detail,
    get_edge_detail,
)


def get_unified_graph(
    cur,
    source: str = "all",  # "git", "cognitive", or "all"
    trust_zone: Optional[str] = None,
    project_id: Optional[str] = None,
    limit: int = 120,
    repository_filter: Optional[str] = None,
    entity_type_filter: Optional[str] = None,
    relation_type_filter: Optional[str] = None,
    epistemic_filter: Optional[str] = None,  # "EXTRACTED", "INFERRED", "PROPOSED", or None
) -> GraphResponseDTO:
    """Return a unified GraphResponseDTO connecting physical Git topology and cognitive knowledge.

    Orchestrates:
    1. Physical Git Graph (Organization + 55 Repositories).
    2. Cognitive Graph Backbone (Projects, Decisions, Rules, Lessons, Patterns, Agents).
    3. Factual Evidence Bridges:
       - REPOSITORY <-> PROJECT (evidenced in pub_neural.project_repositories).
       - REPOSITORY / SOURCE <-> COGNITIVE NODES (evidenced in pub_neural.neural_evidence and project context).
    """
    nodes: List[GraphNodeDTO] = []
    edges: List[GraphEdgeDTO] = []
    seen_node_ids: Set[str] = set()
    seen_edge_ids: Set[str] = set()

    # 1. Physical Git Topology
    if source in ("git", "all"):
        if repository_filter:
            # Subtree projection for specific repository
            git_graph = get_git_topology(
                repo=repository_filter,
                branch="main",
                base_path="",
                depth=1,
                limit=limit,
            )
        else:
            # Full holding topology (Root + 55 repositories + cross-repo consolidation)
            git_graph = get_organization_graph(
                org=CANONICAL_ORG,
                include_archived=True,
                limit=limit,
            )

        for n in git_graph.nodes:
            if n.id not in seen_node_ids:
                seen_node_ids.add(n.id)
                nodes.append(n)

        for e in git_graph.edges:
            if e.id not in seen_edge_ids:
                seen_edge_ids.add(e.id)
                edges.append(e)

    # 2. Cognitive Institutional Backbone
    if source in ("cognitive", "all"):
        cog_graph = get_graph_backbone(
            cur=cur,
            trust_zone=trust_zone,
            limit=limit,
            project_id=project_id,
        )

        for n in cog_graph.nodes:
            if n.id not in seen_node_ids:
                seen_node_ids.add(n.id)
                nodes.append(n)

        for e in cog_graph.edges:
            if e.id not in seen_edge_ids:
                seen_edge_ids.add(e.id)
                edges.append(e)

    # 3. Evidence Bridges between Physical Repositories and Cognitive Entities
    if source == "all" and cur is not None:
        _attach_evidence_bridges(
            cur=cur,
            nodes=nodes,
            edges=edges,
            seen_node_ids=seen_node_ids,
            seen_edge_ids=seen_edge_ids,
        )

    # 4. Apply Dynamic Filters if requested
    if entity_type_filter:
        allowed_types = {t.strip().upper() for t in entity_type_filter.split(",")}
        nodes = [n for n in nodes if n.entity_type.upper() in allowed_types]
        surviving_ids = {n.id for n in nodes}
        edges = [e for e in edges if e.source_id in surviving_ids and e.target_id in surviving_ids]

    if relation_type_filter:
        allowed_rels = {r.strip().upper() for r in relation_type_filter.split(",")}
        edges = [e for e in edges if e.relation_type.upper() in allowed_rels]

    if epistemic_filter:
        allowed_epistemic = {epistemic_filter.strip().upper()}
        edges = [
            e for e in edges
            if getattr(e, "epistemic_classification", None) in allowed_epistemic
            or (getattr(e, "association_status", None) == "CONFIRMED" and "EXTRACTED" in allowed_epistemic)
            or (getattr(e, "association_status", None) == "PROPOSED" and "PROPOSED" in allowed_epistemic)
        ]

    return GraphResponseDTO(
        nodes=nodes,
        edges=edges,
        center_node_id=f"org:{CANONICAL_ORG}" if f"org:{CANONICAL_ORG}" in seen_node_ids else None,
        hop_depth=1,
        total_nodes=len(nodes),
        total_edges=len(edges),
    )


def _attach_evidence_bridges(
    cur,
    nodes: List[GraphNodeDTO],
    edges: List[GraphEdgeDTO],
    seen_node_ids: Set[str],
    seen_edge_ids: Set[str],
) -> None:
    """Connect physical repositories to cognitive entities via evidenced associations."""
    try:
        # A. Query project_repositories for confirmed / proposed bindings
        repo_assoc_sql = """
            SELECT
                project_id, repository_id, relationship_type, is_primary,
                association_status, classification_source, classification_confidence,
                classification_reason
            FROM pub_neural.project_repositories;
        """
        cur.execute(repo_assoc_sql)
        assocs = cur.fetchall()

        # Map project slug to node id in cognitive graph
        for assoc in assocs:
            proj_id_raw = assoc["project_id"]  # e.g. "proj:pub-core" or "pub-core"
            repo_name = assoc["repository_id"]  # e.g. "pubcore" or "pub-neural"
            assoc_status = assoc.get("association_status", "CONFIRMED")
            reason = assoc.get("classification_reason", "Evidenced project repository association")
            confidence = float(assoc.get("classification_confidence") or 1.0)
            class_source = assoc.get("classification_source", "DOCUMENTATION")

            # Determine epistemic state
            if assoc_status == "CONFIRMED" and confidence >= 0.9:
                epistemic_state = "EXTRACTED"
            elif assoc_status == "PROPOSED":
                epistemic_state = "PROPOSED"
            else:
                epistemic_state = "INFERRED"

            repo_node_id = f"repo:{CANONICAL_ORG}/{repo_name}"

            # Bridge to Cognitive Nodes that share this project_id
            # Clean project key (strip 'proj:')
            clean_proj_key = proj_id_raw.replace("proj:", "")

            for n in nodes:
                # If node is a cognitive entity (not git node) and belongs to this project
                if not (n.id.startswith("org:") or n.id.startswith("repo:") or n.id.startswith("dir:") or n.id.startswith("file:") or n.id.startswith("commit:")) and n.project_id == clean_proj_key:
                    bridge_edge_id = f"edge:{repo_node_id}:{n.id}"
                    if repo_node_id in seen_node_ids and bridge_edge_id not in seen_edge_ids:
                        seen_edge_ids.add(bridge_edge_id)
                        edges.append(
                            GraphEdgeDTO(
                                id=bridge_edge_id,
                                source_id=repo_node_id,
                                target_id=n.id,
                                relation_type="IMPLEMENTS" if n.entity_type in ("DECISION", "GOVERNANCE", "RULE") else "APPLIES_TO",
                                weight=confidence,
                                is_bidirectional=False,
                                trust_zone=n.trust_zone,
                                is_active=True,
                                association_status=assoc_status,
                                classification_source=class_source,
                                classification_confidence=confidence,
                                classification_reason=f"Repository {repo_name} binds to project {clean_proj_key}: {reason}",
                                epistemic_classification=epistemic_state,
                                evidence_locator={
                                    "source": class_source,
                                    "repository": repo_name,
                                    "project": clean_proj_key,
                                    "reason": reason,
                                    "confidence": confidence,
                                    "epistemic_state": epistemic_state,
                                },
                            )
                        )

        # B. Query neural_evidence for direct file / commit evidence attachments
        ev_query_sql = """
            SELECT 
                e.id AS evidence_id, e.node_id, e.edge_id, e.confidence,
                e.start_line, e.end_line, e.exact_quote,
                s.repository, s.commit_sha, s.file_path
            FROM pub_neural.neural_evidence e
            JOIN pub_neural.neural_sources s ON e.source_id = s.id
            WHERE s.repository IS NOT NULL;
        """
        cur.execute(ev_query_sql)
        ev_rows = cur.fetchall()

        for ev in ev_rows:
            node_id = ev.get("node_id")
            repo = ev.get("repository")
            file_path = ev.get("file_path")
            conf = float(ev.get("confidence") or 1.0)
            if not repo or not node_id:
                continue

            repo_node_id = f"repo:{CANONICAL_ORG}/{repo}" if "/" not in repo else f"repo:{repo}"
            bridge_edge_id = f"edge:{repo_node_id}:{node_id}"

            if repo_node_id in seen_node_ids and node_id in seen_node_ids and bridge_edge_id not in seen_edge_ids:
                seen_edge_ids.add(bridge_edge_id)
                edges.append(
                    GraphEdgeDTO(
                        id=bridge_edge_id,
                        source_id=repo_node_id,
                        target_id=node_id,
                        relation_type="VALIDATED_BY",
                        weight=conf,
                        is_bidirectional=False,
                        trust_zone="tz_internal_holding",
                        is_active=True,
                        association_status="CONFIRMED",
                        classification_source="neural_evidence",
                        classification_confidence=conf,
                        classification_reason=f"Grounded code slice evidence in {file_path}",
                        epistemic_classification="EXTRACTED",
                        evidence_locator={
                            "evidence_id": str(ev.get("evidence_id")),
                            "repository": repo,
                            "file_path": file_path,
                            "commit_sha": ev.get("commit_sha"),
                            "start_line": ev.get("start_line"),
                            "end_line": ev.get("end_line"),
                            "exact_quote": ev.get("exact_quote"),
                            "confidence": conf,
                            "epistemic_state": "EXTRACTED",
                        },
                    )
                )
    except Exception as e:
        # Fail-soft: bridge enhancement must not break base graph projection
        import logging
        logging.getLogger(__name__).warning("Error attaching evidence bridges in unified graph: %s", e)
