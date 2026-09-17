"""
Graph exploration service for PUB Neural Console V0.
Provides bounded neighborhood traversals and entity detail inspection.
Enforces:
- Depth bounded to maximum 2 hops.
- Results bounded to maximum 150 nodes.
- Respects is_active and RLS constraints.
"""

from typing import Any, Dict, List, Optional, Set
from console.backend.models import (
    EdgeDetailDTO,
    EntityDetailDTO,
    EvidenceLocatorDTO,
    GraphEdgeDTO,
    GraphNodeDTO,
    GraphResponseDTO,
    serialize_val,
)


def get_entity_detail(cur, entity_id: str) -> Optional[EntityDetailDTO]:
    """Retrieve detailed metadata and grounded evidence for an entity."""
    sql = """
        SELECT 
            id, entity_type, title, slug, summary, content, promotion_state,
            promotion_reason, conflict_state, confidence_score, superseded_by,
            valid_from, valid_until, recorded_from, recorded_until, is_active,
            originating_event_id, last_transition_event_id, project_id, trust_zone,
            created_at, updated_at
        FROM pub_neural.neural_nodes
        WHERE id = %s AND is_active = TRUE;
    """
    cur.execute(sql, (entity_id,))
    row = cur.fetchone()
    if not row:
        return None

    # Fetch evidence locators
    ev_sql = """
        SELECT 
            e.id, e.source_id, e.start_line, e.end_line, e.exact_quote, e.confidence,
            s.repository, s.commit_sha, s.file_path
        FROM pub_neural.neural_evidence e
        LEFT JOIN pub_neural.neural_sources s ON e.source_id = s.id
        WHERE e.node_id = %s
        ORDER BY e.start_line ASC;
    """
    cur.execute(ev_sql, (entity_id,))
    ev_rows = cur.fetchall()
    evidence_list = [
        EvidenceLocatorDTO(
            id=str(r["id"]),
            source_id=str(r["source_id"]),
            repository=r.get("repository"),
            commit_sha=r.get("commit_sha"),
            file_path=r.get("file_path"),
            start_line=r["start_line"],
            end_line=r["end_line"],
            exact_quote=r["exact_quote"],
            confidence=float(r["confidence"]),
        )
        for r in ev_rows
    ]

    # Fetch relation counts
    rel_sql = """
        SELECT 
            (SELECT COUNT(*) FROM pub_neural.neural_edges WHERE target_id = %s AND is_active = TRUE) AS incoming_count,
            (SELECT COUNT(*) FROM pub_neural.neural_edges WHERE source_id = %s AND is_active = TRUE) AS outgoing_count;
    """
    cur.execute(rel_sql, (entity_id, entity_id))
    counts = cur.fetchone() or {"incoming_count": 0, "outgoing_count": 0}

    return EntityDetailDTO(
        id=str(row["id"]),
        entity_type=str(row["entity_type"]),
        title=row["title"],
        slug=row["slug"],
        summary=row.get("summary"),
        content=row.get("content"),
        promotion_state=str(row["promotion_state"]),
        promotion_reason=row.get("promotion_reason"),
        conflict_state=str(row["conflict_state"]),
        confidence_score=float(row["confidence_score"]),
        superseded_by=str(row["superseded_by"]) if row.get("superseded_by") else None,
        valid_from=serialize_val(row["valid_from"]),
        valid_until=serialize_val(row.get("valid_until")),
        recorded_from=serialize_val(row["recorded_from"]),
        recorded_until=serialize_val(row.get("recorded_until")),
        is_active=bool(row["is_active"]),
        originating_event_id=str(row["originating_event_id"]),
        last_transition_event_id=str(row["last_transition_event_id"]) if row.get("last_transition_event_id") else None,
        project_id=row.get("project_id"),
        trust_zone=row["trust_zone"],
        created_at=serialize_val(row["created_at"]),
        updated_at=serialize_val(row["updated_at"]),
        evidence=evidence_list,
        incoming_relations_count=int(counts["incoming_count"]),
        outgoing_relations_count=int(counts["outgoing_count"]),
    )


def get_graph_backbone(
    cur,
    trust_zone: Optional[str] = None,
    limit: int = 100,
    project_id: Optional[str] = None,
) -> GraphResponseDTO:
    """
    Retrieve the global backbone of PUB Neural knowledge graph.
    Focuses on institutional macro-entities:
    PROJECT, REPOSITORY, DECISION, RULE, GOVERNANCE, HOLDING, PATTERN.
    Enforces:
    - default limit: 100, max limit: 250.
    - respects trust_zone and is_active=TRUE.
    """
    bounded_limit = max(1, min(limit, 250))
    backbone_types = [
        "PROJECT",
        "REPOSITORY",
        "DECISION",
        "RULE",
        "GOVERNANCE",
        "HOLDING",
        "PATTERN",
    ]

    query_clauses = ["is_active = TRUE", "entity_type = ANY(%s)"]
    params: List[Any] = [backbone_types]

    if trust_zone:
        query_clauses.append("trust_zone = %s")
        params.append(trust_zone)

    if project_id:
        query_clauses.append("project_id = %s")
        params.append(project_id)

    node_sql = f"""
        SELECT 
            n.id, n.entity_type, n.title, n.slug, n.summary, n.promotion_state,
            n.conflict_state, n.confidence_score, n.valid_from, n.valid_until,
            n.trust_zone, n.project_id,
            COUNT(e.id) AS evidence_count
        FROM pub_neural.neural_nodes n
        LEFT JOIN pub_neural.neural_evidence e ON n.id = e.node_id
        WHERE {" AND ".join(query_clauses)}
        GROUP BY n.id, n.entity_type, n.title, n.slug, n.summary, n.promotion_state,
                 n.conflict_state, n.confidence_score, n.valid_from, n.valid_until,
                 n.trust_zone, n.project_id
        ORDER BY 
            CASE 
                WHEN n.entity_type IN ('HOLDING', 'PROJECT') THEN 1
                WHEN n.entity_type IN ('REPOSITORY', 'RULE', 'GOVERNANCE') THEN 2
                WHEN n.entity_type = 'DECISION' THEN 3
                ELSE 4
            END ASC,
            n.confidence_score DESC,
            n.created_at DESC
        LIMIT %s;
    """
    params.append(bounded_limit)
    cur.execute(node_sql, tuple(params))
    node_rows = cur.fetchall()

    nodes: List[GraphNodeDTO] = []
    node_ids: Set[str] = set()
    for r in node_rows:
        n_id = str(r["id"])
        node_ids.add(n_id)
        nodes.append(
            GraphNodeDTO(
                id=n_id,
                entity_type=str(r["entity_type"]),
                title=r["title"],
                slug=r["slug"],
                summary=r.get("summary"),
                promotion_state=str(r["promotion_state"]),
                conflict_state=str(r["conflict_state"]),
                confidence_score=float(r["confidence_score"]),
                valid_from=serialize_val(r["valid_from"]),
                valid_until=serialize_val(r.get("valid_until")),
                trust_zone=str(r["trust_zone"]),
                project_id=r.get("project_id"),
                evidence_count=int(r["evidence_count"]),
            )
        )

    edges: List[GraphEdgeDTO] = []
    if node_ids:
        edge_sql = """
            SELECT DISTINCT 
                id AS edge_id, source_id, target_id, relation_type, weight,
                is_bidirectional, trust_zone, is_active
            FROM pub_neural.neural_edges
            WHERE source_id = ANY(%s) AND target_id = ANY(%s)
              AND is_active = TRUE
            LIMIT 500;
        """
        cur.execute(edge_sql, (list(node_ids), list(node_ids)))
        edge_rows = cur.fetchall()
        for r in edge_rows:
            edges.append(
                GraphEdgeDTO(
                    id=str(r["edge_id"]),
                    source_id=str(r["source_id"]),
                    target_id=str(r["target_id"]),
                    relation_type=str(r["relation_type"]),
                    weight=float(r["weight"]),
                    is_bidirectional=bool(r["is_bidirectional"]),
                    trust_zone=str(r["trust_zone"]),
                    is_active=bool(r["is_active"]),
                )
            )

    return GraphResponseDTO(
        nodes=nodes,
        edges=edges,
        center_node_id=None,
        hop_depth=0,
        total_nodes=len(nodes),
        total_edges=len(edges),
    )


def get_neighborhood(
    cur,
    entity_id: str,
    depth: int = 1,
    limit: int = 50,
    entity_types: Optional[List[str]] = None,
    relation_types: Optional[List[str]] = None,
    epistemic_state: Optional[str] = None,
    trust_zone: Optional[str] = None,
    project_id: Optional[str] = None,
) -> GraphResponseDTO:
    """
    Execute bounded neighborhood expansion starting from entity_id with optional filters.
    Guarantees:
    - depth bounded to [1, 2].
    - limit bounded to [1, 100].
    """
    bounded_depth = max(1, min(depth, 2))
    bounded_limit = max(1, min(limit, 100))

    edge_conditions = ["is_active = TRUE"]
    edge_params: List[Any] = []

    if relation_types:
        edge_conditions.append("relation_type = ANY(%s)")
        edge_params.append([rt.strip().upper() for rt in relation_types])

    if trust_zone:
        edge_conditions.append("trust_zone = %s")
        edge_params.append(trust_zone)

    if bounded_depth == 1:
        where_clause = " AND ".join(["(source_id = %s OR target_id = %s)"] + edge_conditions)
        sql = f"""
            SELECT DISTINCT 
                id AS edge_id, source_id, target_id, relation_type, weight,
                is_bidirectional, trust_zone, is_active
            FROM pub_neural.neural_edges
            WHERE {where_clause}
            LIMIT %s;
        """
        cur.execute(sql, tuple([entity_id, entity_id] + edge_params + [bounded_limit]))
    else:
        where_init = " AND ".join(["(e.source_id = %s OR e.target_id = %s)"] + [f"e.{c}" for c in edge_conditions])
        sql = f"""
            WITH RECURSIVE neighborhood AS (
                SELECT 
                    e.id AS edge_id, e.source_id, e.target_id, e.relation_type, e.weight,
                    e.is_bidirectional, e.trust_zone, e.is_active, 1 AS depth
                FROM pub_neural.neural_edges e
                WHERE {where_init}

                UNION

                SELECT 
                    e2.id AS edge_id, e2.source_id, e2.target_id, e2.relation_type, e2.weight,
                    e2.is_bidirectional, e2.trust_zone, e2.is_active, n.depth + 1
                FROM pub_neural.neural_edges e2
                JOIN neighborhood n ON (e2.source_id = n.target_id OR e2.target_id = n.source_id)
                WHERE n.depth < 2
                  AND e2.is_active = TRUE
            )
            SELECT DISTINCT 
                edge_id, source_id, target_id, relation_type, weight,
                is_bidirectional, trust_zone, is_active
            FROM neighborhood
            LIMIT %s;
        """
        cur.execute(sql, tuple([entity_id, entity_id] + edge_params + [bounded_limit]))

    edge_rows = cur.fetchall()

    node_ids: Set[str] = {entity_id}
    edges: List[GraphEdgeDTO] = []
    for r in edge_rows:
        node_ids.add(str(r["source_id"]))
        node_ids.add(str(r["target_id"]))
        edges.append(
            GraphEdgeDTO(
                id=str(r["edge_id"]),
                source_id=str(r["source_id"]),
                target_id=str(r["target_id"]),
                relation_type=str(r["relation_type"]),
                weight=float(r["weight"]),
                is_bidirectional=bool(r["is_bidirectional"]),
                trust_zone=str(r["trust_zone"]),
                is_active=bool(r["is_active"]),
            )
        )

    nodes: List[GraphNodeDTO] = []
    if node_ids:
        node_conditions = ["n.id = ANY(%s)", "n.is_active = TRUE"]
        node_params: List[Any] = [list(node_ids)]

        if entity_types:
            node_conditions.append("n.entity_type = ANY(%s)")
            node_params.append([et.strip().upper() for et in entity_types])

        if epistemic_state and epistemic_state.upper() != "ALL":
            if epistemic_state.upper() in ("CONFIRMED", "VALIDATED", "ADOPTED", "INSTITUTIONAL"):
                node_conditions.append("n.promotion_state = ANY(%s)")
                node_params.append(["VALIDATED", "ADOPTED", "INSTITUTIONAL", "CONFIRMED"])
            elif epistemic_state.upper() in ("PROPOSED", "CANDIDATE", "CAPTURED", "EXTRACTED"):
                node_conditions.append("n.promotion_state = ANY(%s)")
                node_params.append(["CANDIDATE", "CAPTURED", "EXTRACTED", "PROPOSED"])

        if project_id:
            node_conditions.append("n.project_id = %s")
            node_params.append(project_id)

        node_sql = f"""
            SELECT 
                n.id, n.entity_type, n.title, n.slug, n.summary, n.promotion_state,
                n.conflict_state, n.confidence_score, n.valid_from, n.valid_until,
                n.trust_zone, n.project_id,
                COUNT(e.id) AS evidence_count
            FROM pub_neural.neural_nodes n
            LEFT JOIN pub_neural.neural_evidence e ON n.id = e.node_id
            WHERE {" AND ".join(node_conditions)}
            GROUP BY n.id, n.entity_type, n.title, n.slug, n.summary, n.promotion_state,
                     n.conflict_state, n.confidence_score, n.valid_from, n.valid_until,
                     n.trust_zone, n.project_id;
        """
        cur.execute(node_sql, tuple(node_params))
        node_rows = cur.fetchall()

        # Build set of matched node ids
        matched_node_ids = set()
        for r in node_rows:
            n_id = str(r["id"])
            matched_node_ids.add(n_id)
            nodes.append(
                GraphNodeDTO(
                    id=n_id,
                    entity_type=str(r["entity_type"]),
                    title=r["title"],
                    slug=r["slug"],
                    summary=r.get("summary"),
                    promotion_state=str(r["promotion_state"]),
                    conflict_state=str(r["conflict_state"]),
                    confidence_score=float(r["confidence_score"]),
                    valid_from=serialize_val(r["valid_from"]),
                    valid_until=serialize_val(r.get("valid_until")),
                    trust_zone=str(r["trust_zone"]),
                    project_id=r.get("project_id"),
                    evidence_count=int(r["evidence_count"]),
                )
            )

        # Filter edges to only connect nodes that survived the node filtering
        edges = [e for e in edges if e.source_id in matched_node_ids and e.target_id in matched_node_ids]

    return GraphResponseDTO(
        nodes=nodes,
        edges=edges,
        center_node_id=entity_id,
        hop_depth=bounded_depth,
        total_nodes=len(nodes),
        total_edges=len(edges),
    )


def get_edge_detail(cur, edge_id: str) -> Optional[EdgeDetailDTO]:
    """Retrieve detailed metadata, provenance, and grounded evidence for an edge."""
    sql = """
        SELECT 
            id, source_id, target_id, relation_type, weight, is_bidirectional,
            trust_zone, is_active, valid_from, valid_until, recorded_from,
            recorded_until, originating_event_id, last_transition_event_id,
            created_at, updated_at
        FROM pub_neural.neural_edges
        WHERE id = %s AND is_active = TRUE;
    """
    cur.execute(sql, (edge_id,))
    row = cur.fetchone()
    if not row:
        return None

    # Fetch edge-linked evidence if any
    ev_sql = """
        SELECT 
            e.id, e.source_id, e.start_line, e.end_line, e.exact_quote, e.confidence,
            e.validation_state, e.extractor_version,
            s.repository, s.commit_sha, s.file_path
        FROM pub_neural.neural_evidence e
        LEFT JOIN pub_neural.neural_sources s ON e.source_id = s.id
        WHERE e.edge_id = %s
        ORDER BY e.start_line ASC;
    """
    cur.execute(ev_sql, (edge_id,))
    ev_rows = cur.fetchall()
    evidence_list = [
        EvidenceLocatorDTO(
            id=str(r["id"]),
            source_id=str(r["source_id"]),
            repository=r.get("repository"),
            commit_sha=r.get("commit_sha"),
            file_path=r.get("file_path"),
            start_line=r["start_line"],
            end_line=r["end_line"],
            exact_quote=r["exact_quote"],
            confidence=float(r["confidence"]),
        )
        for r in ev_rows
    ]

    # Derive extractor and epistemic classification
    extractor = "canonical-extractor"
    epistemic_classification = "EXTRACTED"
    confidence = float(row.get("weight", 1.0))

    if ev_rows:
        first_ev = ev_rows[0]
        if first_ev.get("extractor_version"):
            extractor = str(first_ev["extractor_version"])
        if float(first_ev.get("confidence", 1.0)) < 0.8:
            epistemic_classification = "INFERRED"
    elif row.get("relation_type") in ("RELATED_TO", "APPLIES_TO"):
        epistemic_classification = "INFERRED"

    return EdgeDetailDTO(
        id=str(row["id"]),
        source_id=str(row["source_id"]),
        target_id=str(row["target_id"]),
        relation_type=str(row["relation_type"]),
        weight=float(row["weight"]),
        is_bidirectional=bool(row["is_bidirectional"]),
        trust_zone=row["trust_zone"],
        is_active=bool(row["is_active"]),
        confidence=confidence,
        epistemic_classification=epistemic_classification,
        extractor=extractor,
        valid_from=serialize_val(row["valid_from"]),
        valid_until=serialize_val(row.get("valid_until")),
        recorded_from=serialize_val(row["recorded_from"]),
        recorded_until=serialize_val(row.get("recorded_until")),
        created_at=serialize_val(row["created_at"]),
        updated_at=serialize_val(row["updated_at"]),
        originating_event_id=str(row["originating_event_id"]),
        last_transition_event_id=str(row["last_transition_event_id"]) if row.get("last_transition_event_id") else None,
        evidence=evidence_list,
    )
