"""
Retrieval adapter and result mapping boundary for the Neural Query Service.
Translates between raw search outputs (HybridSearchResult / DB projections)
and strongly-typed NeuralKnowledgeItem contracts.
"""

from dataclasses import dataclass, field
import re
from typing import Any, Dict, List, Optional, Protocol, Union, runtime_checkable

from src.retrieval.abstention import AbstentionDecision
from src.retrieval.hybrid_search import HybridSearchEngine, HybridSearchResult
from .enums import (
    AuthorityLevel,
    ConflictState,
    FreshnessState,
    KnowledgeClass,
    PromotionState,
)
from .exceptions import GateTransportError, GateValidationError
from .models import (
    AuthorityMetadata,
    ContradictionItem,
    FreshnessMetadata,
    NeuralKnowledgeItem,
    ProvenanceMetadata,
)


@dataclass
class RetrievalBatch:
    """
    Standardized container for raw retrieval outputs, abstention status, and metadata.
    Decouples NeuralQueryService from underlying database or search engine implementations.
    """
    results: List[Any] = field(default_factory=list)
    abstention_decision: Optional[AbstentionDecision] = None
    contradictions: List[ContradictionItem] = field(default_factory=list)
    is_stale: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class NeuralRetrievalEngine(Protocol):
    """
    Protocol defining the retrieval interface consumed by NeuralQueryService.
    Supports dependency injection of HybridSearchAdapter or deterministic test doubles.
    """
    def search_knowledge(
        self,
        query: str,
        trust_zone: Optional[str] = None,
        project_id: Optional[str] = None,
        limit: int = 5,
        knowledge_classes: Optional[List[KnowledgeClass]] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> RetrievalBatch:
        ...


class NeuralResultMapper:
    """
    Maps raw retrieval results (HybridSearchResult, dicts, or DB rows)
    to the canonical NeuralKnowledgeItem contract.
    Ensures provenance and authority boundaries are strictly preserved without fabricating data.
    """

    @staticmethod
    def _extract_attr(obj: Any, key: str, default: Any = None) -> Any:
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    @classmethod
    def infer_knowledge_class(cls, raw: Any, default_class: KnowledgeClass = KnowledgeClass.DECISION) -> KnowledgeClass:
        """
        Deterministically infer the KnowledgeClass from raw metadata, target_type, or slug prefix.
        """
        # 1. Explicit knowledge_class attribute
        explicit = cls._extract_attr(raw, "knowledge_class")
        if explicit:
            try:
                return KnowledgeClass.from_str(explicit)
            except ValueError:
                pass

        # 2. Check target_type
        target_type = cls._extract_attr(raw, "target_type")
        if target_type:
            try:
                return KnowledgeClass.from_str(target_type)
            except ValueError:
                pass

        # 3. Check target_id / id prefix convention (e.g. 'rule:pub-core:zero-mutation')
        target_id = str(cls._extract_attr(raw, "target_id", cls._extract_attr(raw, "id", "")))
        prefix_mapping = {
            "decision": KnowledgeClass.DECISION,
            "rule": KnowledgeClass.RULE,
            "gov": KnowledgeClass.GOVERNANCE,
            "governance": KnowledgeClass.GOVERNANCE,
            "pattern": KnowledgeClass.PATTERN,
            "lesson": KnowledgeClass.LESSON,
            "skill": KnowledgeClass.SKILL,
            "project": KnowledgeClass.PROJECT,
            "repo": KnowledgeClass.REPOSITORY,
            "repository": KnowledgeClass.REPOSITORY,
        }
        for prefix, k_class in prefix_mapping.items():
            if target_id.lower().startswith(f"{prefix}:"):
                return k_class

        return default_class

    def map_result(self, raw: Any, default_project_id: Optional[str] = None) -> NeuralKnowledgeItem:
        """
        Transform a single raw retrieval result into a canonical NeuralKnowledgeItem.
        """
        if isinstance(raw, NeuralKnowledgeItem):
            return raw

        target_id = str(self._extract_attr(raw, "target_id", self._extract_attr(raw, "id", "item-unknown")))
        title = self._extract_attr(raw, "title", self._extract_attr(raw, "node_title", target_id))
        content = self._extract_attr(
            raw,
            "snippet",
            self._extract_attr(raw, "content", self._extract_attr(raw, "node_content", "No content available")),
        )
        if not content or not str(content).strip():
            content = f"Item {target_id}"

        k_class = self.infer_knowledge_class(raw)

        project_id = self._extract_attr(raw, "project_id", default_project_id)
        raw_scope = self._extract_attr(raw, "scope")
        if raw_scope and str(raw_scope).upper() in ("GLOBAL", "PROJECT"):
            scope = str(raw_scope).upper()
        else:
            scope = "PROJECT" if project_id else "GLOBAL"

        relevance = float(self._extract_attr(raw, "rrf_score", self._extract_attr(raw, "relevance_score", 0.0)))
        confidence = float(self._extract_attr(raw, "confidence_score", 1.0))

        # Provenance: preserve only factual evidence without inventing IDs
        prov = ProvenanceMetadata(
            source_id=self._extract_attr(raw, "source_id"),
            originating_event_id=self._extract_attr(raw, "originating_event_id"),
            evidence_id=self._extract_attr(raw, "evidence_id"),
            content_hash=self._extract_attr(raw, "content_hash"),
            repository=self._extract_attr(raw, "repository"),
            commit_sha=self._extract_attr(raw, "commit_sha"),
            file_path=self._extract_attr(raw, "file_path"),
            start_line=self._extract_attr(raw, "start_line"),
            end_line=self._extract_attr(raw, "end_line"),
            exact_quote=self._extract_attr(raw, "exact_quote"),
            captured_at=self._extract_attr(raw, "captured_at"),
            observed_at=self._extract_attr(raw, "observed_at"),
            storage_uri=self._extract_attr(raw, "storage_uri"),
        )

        # Authority: strictly data_only
        raw_auth_level = self._extract_attr(raw, "authority_level", AuthorityLevel.VALIDATED_KNOWLEDGE)
        auth = AuthorityMetadata(
            level=AuthorityLevel.from_str(raw_auth_level),
            is_data_only=True,
            description="Neural knowledge data item",
        )

        # Freshness
        is_stale = bool(self._extract_attr(raw, "is_stale", False))
        freshness_state = FreshnessState.STALE if is_stale else FreshnessState.VALID
        fresh = FreshnessMetadata(
            state=freshness_state,
            is_stale=is_stale,
            checked_at=self._extract_attr(raw, "checked_at"),
            diverged_commit_sha=self._extract_attr(raw, "diverged_commit_sha"),
            reason=self._extract_attr(raw, "freshness_reason"),
        )

        raw_conflict = self._extract_attr(raw, "conflict_state", ConflictState.RESOLVED)
        raw_promotion = self._extract_attr(raw, "promotion_state", PromotionState.VALIDATED)

        return NeuralKnowledgeItem(
            id=target_id,
            knowledge_class=k_class,
            title=title,
            content=content,
            scope=scope,
            project_id=project_id,
            relevance_score=relevance,
            confidence_score=confidence,
            promotion_state=PromotionState.from_str(raw_promotion),
            conflict_state=ConflictState.from_str(raw_conflict),
            authority=auth,
            provenance=prov,
            freshness=fresh,
        )


class HybridSearchAdapter:
    """
    Concrete adapter wrapping the existing HybridSearchEngine to fulfill NeuralRetrievalEngine.
    Preserves existing FTS, pgvector, RRF, and abstention capabilities without duplication.
    """

    def __init__(self, engine: HybridSearchEngine):
        self.engine = engine

    def search_knowledge(
        self,
        query: str,
        trust_zone: Optional[str] = None,
        project_id: Optional[str] = None,
        limit: int = 5,
        knowledge_classes: Optional[List[KnowledgeClass]] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> RetrievalBatch:
        """
        Execute search using the wrapped HybridSearchEngine.
        Catches database connection errors and converts them to GateTransportError.
        """
        try:
            # Reuses search_detailed on the existing engine
            batch_data = self.engine.search_detailed(
                query=query,
                trust_zone=trust_zone,
                project_id=project_id,
            )
            raw_results = batch_data.get("results", [])[:limit]
            decision = batch_data.get("abstention_decision")

            return RetrievalBatch(
                results=raw_results,
                abstention_decision=decision,
                metadata={
                    "lexical_count": batch_data.get("lexical_count", 0),
                    "dense_count": batch_data.get("dense_count", 0),
                    "query": query,
                },
            )
        except Exception as e:
            err_type = type(e).__name__
            if "OperationalError" in err_type or "InterfaceError" in err_type:
                raise GateTransportError(f"Database connection unavailable during hybrid search: {e}") from e
            raise e
