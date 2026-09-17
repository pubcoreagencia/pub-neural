"""
Graphify Normalizer for PUB Neural.
Transforms external Graphify nodes and edges into PUB Neural canonical events,
preserving epistemic boundaries, deterministic identifiers, and bi-temporal provenance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import re
from typing import Any, Dict, List, Optional, Tuple
import unicodedata
import uuid

# Mapping from Graphify relation strings to PUB Neural canonical neural_relation_type
RELATION_MAPPING: Dict[str, str] = {
    "imports": "DEPENDS_ON",
    "calls": "USES",
    "uses": "USES",
    "inherits": "IMPLEMENTS",
    "implements": "IMPLEMENTS",
    "references": "RELATED_TO",
    "contains": "RELATED_TO",
    "depends_on": "DEPENDS_ON",
    "related_to": "RELATED_TO",
}

DEFAULT_RELATION = "RELATED_TO"


@dataclass
class NormalizedNode:
    node_id: str
    entity_type: str  # DOCUMENT, CONCEPT
    title: str
    slug: str
    summary: str
    content: str
    file_type: str
    source_file: str
    source_location: str
    confidence_score: float
    initial_state: str  # EXTRACTED, CANDIDATE, CAPTURED
    event_id: uuid.UUID
    content_hash: str


@dataclass
class NormalizedEdge:
    edge_id: uuid.UUID
    source_id: str
    target_id: str
    relation_type: str  # USES, DEPENDS_ON, IMPLEMENTS, RELATED_TO
    weight: float
    confidence_score: float
    confidence_tier: str  # EXTRACTED, INFERRED, AMBIGUOUS
    is_bidirectional: bool
    source_file: str
    event_id: uuid.UUID


@dataclass
class NormalizedEvidence:
    evidence_id: uuid.UUID
    target_type: str  # NODE, EDGE
    target_id: str
    file_path: str
    start_line: int
    end_line: int
    exact_quote: str
    confidence: float
    content_hash: str


@dataclass
class NormalizedGraph:
    repository: str
    commit_sha: str
    project_id: str
    trust_zone: str
    nodes: List[NormalizedNode] = field(default_factory=list)
    edges: List[NormalizedEdge] = field(default_factory=list)
    evidence: List[NormalizedEvidence] = field(default_factory=list)


class GraphifyNormalizer:
    """
    Transforms Graphify raw JSON graph dict into PUB Neural canonical models.
    """

    NAMESPACE_PUB = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")

    def __init__(
        self,
        project_id: str = "pub-neural",
        repository: str = "pubcoreagencia/pub-neural",
        trust_zone: str = "tz_internal_holding",
    ):
        self.project_id = project_id
        self.repository = repository
        self.trust_zone = trust_zone

    def derive_canonical_node_id(self, entity_type: str, raw_id: str, label: str) -> str:
        """Derive deterministic, collision-resistant canonical node ID."""
        # Normalize text to ASCII slug
        nfkd = unicodedata.normalize("NFKD", (label or raw_id).strip())
        ascii_text = nfkd.encode("ASCII", "ignore").decode("ASCII").lower()
        clean_slug = re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-") or "entity"

        # Unique 8-char digest of raw_id to prevent collision between identically-named symbols across files
        id_hash = hashlib.sha256(raw_id.strip().encode("utf-8")).hexdigest()[:8]
        slug = f"{clean_slug[:40]}-{id_hash}"
        return f"{entity_type.lower()}:{self.project_id}:{slug}"

    def parse_line_range(self, loc_str: str) -> Tuple[int, int]:
        """Parse 'L10-L25' or 'L42' into (start_line, end_line)."""
        if not loc_str:
            return 1, 1
        nums = re.findall(r"\d+", loc_str)
        if len(nums) >= 2:
            s, e = int(nums[0]), int(nums[1])
            return s, max(s, e)
        if len(nums) == 1:
            s = int(nums[0])
            return s, s
        return 1, 1

    def normalize(
        self,
        raw_graph: Dict[str, Any],
        commit_sha: Optional[str] = None,
        snapshot_timestamp: Optional[str] = None,
    ) -> NormalizedGraph:
        """
        Execute normalization over raw Graphify graph dict.
        """
        active_commit = commit_sha or raw_graph.get("built_at_commit") or "HEAD"
        normalized = NormalizedGraph(
            repository=self.repository,
            commit_sha=active_commit,
            project_id=self.project_id,
            trust_zone=self.trust_zone,
        )

        node_id_map: Dict[str, str] = {}  # raw_id -> canonical_node_id

        # 1. Normalize Nodes
        for raw_node in raw_graph.get("nodes", []):
            raw_id = str(raw_node.get("id", "")).strip()
            label = str(raw_node.get("label", raw_id)).strip()
            file_type = str(raw_node.get("file_type", "code")).lower()
            source_file = str(raw_node.get("source_file", "")).strip()
            source_loc = str(raw_node.get("source_location", "L1")).strip()

            if file_type in ("document", "paper") or source_file.endswith((".md", ".txt", ".rst")):
                entity_type = "DOCUMENT"
            else:
                entity_type = "CONCEPT"

            canonical_id = self.derive_canonical_node_id(entity_type, raw_id, label)
            node_id_map[raw_id] = canonical_id

            content_text = f"{label}\nSource: {source_file} ({source_loc})"
            content_hash = hashlib.sha256(content_text.encode("utf-8")).hexdigest()

            # Deterministic event_id for node extraction
            ev_id = uuid.uuid5(
                self.NAMESPACE_PUB,
                f"graphify:entity:{self.repository}:{active_commit}:{canonical_id}",
            )

            # Nodes from AST are extracted facts
            initial_state = "EXTRACTED"
            confidence_score = 0.95

            node = NormalizedNode(
                node_id=canonical_id,
                entity_type=entity_type,
                title=label,
                slug=canonical_id.replace(":", "-"),
                summary=f"Extracted from {source_file} at {source_loc}",
                content=content_text,
                file_type=file_type,
                source_file=source_file,
                source_location=source_loc,
                confidence_score=confidence_score,
                initial_state=initial_state,
                event_id=ev_id,
                content_hash=content_hash,
            )
            normalized.nodes.append(node)

            # Generate Evidence locator for Node
            s_line, e_line = self.parse_line_range(source_loc)
            evidence_id = uuid.uuid5(
                self.NAMESPACE_PUB,
                f"graphify:evidence:node:{canonical_id}:{source_file}:{s_line}:{e_line}",
            )
            normalized.evidence.append(
                NormalizedEvidence(
                    evidence_id=evidence_id,
                    target_type="NODE",
                    target_id=canonical_id,
                    file_path=source_file,
                    start_line=s_line,
                    end_line=e_line,
                    exact_quote=label,
                    confidence=confidence_score,
                    content_hash=content_hash,
                )
            )

        # 2. Normalize Links / Edges
        links = raw_graph.get("links") or raw_graph.get("edges") or []
        for link in links:
            raw_src = str(link.get("source", "")).strip()
            raw_tgt = str(link.get("target", "")).strip()

            can_src = node_id_map.get(raw_src)
            can_tgt = node_id_map.get(raw_tgt)

            # Drop link if endpoints not recognized
            if not can_src or not can_tgt or can_src == can_tgt:
                continue

            raw_rel = str(link.get("relation", "related_to")).lower()
            canonical_rel = RELATION_MAPPING.get(raw_rel, DEFAULT_RELATION)

            # Epistemic Confidence Distinction:
            # EXTRACTED: Explicit syntax -> 0.95 - 1.00
            # INFERRED: Heuristic -> 0.65
            # AMBIGUOUS: Uncertain -> 0.20
            conf_tier = str(link.get("confidence", "EXTRACTED")).upper()
            if conf_tier == "INFERRED":
                conf_score = float(link.get("confidence_score", 0.65))
            elif conf_tier == "AMBIGUOUS":
                conf_score = float(link.get("confidence_score", 0.20))
            else:
                conf_tier = "EXTRACTED"
                conf_score = float(link.get("confidence_score", 1.0))

            edge_uuid = uuid.uuid5(
                self.NAMESPACE_PUB,
                f"graphify:rel:{self.repository}:{active_commit}:{can_src}:{canonical_rel}:{can_tgt}",
            )

            edge = NormalizedEdge(
                edge_id=edge_uuid,
                source_id=can_src,
                target_id=can_tgt,
                relation_type=canonical_rel,
                weight=float(link.get("weight", 1.0)),
                confidence_score=conf_score,
                confidence_tier=conf_tier,
                is_bidirectional=bool(link.get("is_bidirectional", False)),
                source_file=str(link.get("source_file", "")),
                event_id=edge_uuid,
            )
            normalized.edges.append(edge)

        return normalized
