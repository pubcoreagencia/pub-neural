"""
Search service for PUB Neural Console V0.
Integrates with the existing HybridSearchEngine to provide unified FTS + Dense RRF retrieval
while preserving explicit abstention semantics and staleness checks.
"""

from typing import Any, Dict, List, Optional
from console.backend.models import (
    AbstentionDecisionDTO,
    SearchResponseDTO,
    SearchResultItemDTO,
)
from src.retrieval.embedding_model import (
    EmbeddingModelProvider,
    RealSemanticConceptEmbeddingProvider,
)
from src.retrieval.hybrid_search import HybridSearchEngine


def execute_console_search(
    db_url: str,
    bearer_token: str,
    query: str,
    entity_type: Optional[str] = None,
    limit: int = 10,
    embedding_provider: Optional[EmbeddingModelProvider] = None,
) -> SearchResponseDTO:
    """
    Execute search via HybridSearchEngine with session bearer attachment.
    Preserves:
    - RRF ranking formula and tie-breaking.
    - Abstention decision metadata.
    - Vector staleness exclusion.
    """
    provider = embedding_provider or RealSemanticConceptEmbeddingProvider()
    bounded_limit = max(1, min(limit, 50))

    engine = HybridSearchEngine(
        db_url=db_url,
        embedding_provider=provider,
        final_limit=bounded_limit,
    )

    detailed_res = engine.search_detailed(
        query=query,
        bearer_token=bearer_token,
    )

    abstention_obj = detailed_res["abstention_decision"]
    abstention_dto = AbstentionDecisionDTO(
        accepted=bool(abstention_obj.accepted),
        reason=abstention_obj.reason,
        top_dense_similarity=abstention_obj.top_dense_similarity,
        top_rrf_score=abstention_obj.top_rrf_score,
        lexical_candidate_count=int(abstention_obj.lexical_candidate_count),
        dense_candidate_count=int(abstention_obj.dense_candidate_count),
    )

    raw_results = detailed_res.get("results", [])

    # Filter by entity_type if requested
    if entity_type:
        filtered_results = []
        for item in raw_results:
            target_type = getattr(item, "target_type", "") if not isinstance(item, dict) else item.get("target_type")
            if target_type == "NODE":
                filtered_results.append(item)
        raw_results = filtered_results

    result_items: List[SearchResultItemDTO] = []
    for r in raw_results:
        if isinstance(r, dict):
            item_dto = SearchResultItemDTO(
                target_id=r["target_id"],
                target_type=r.get("target_type", "NODE"),
                title=r.get("title", ""),
                snippet=r.get("snippet", ""),
                lexical_rank=r.get("lexical_rank"),
                dense_rank=r.get("dense_rank"),
                rrf_score=float(r.get("rrf_score", 0.0)),
                trust_zone=r.get("trust_zone", ""),
                project_id=r.get("project_id"),
                originating_event_id=str(r.get("originating_event_id", "")),
            )
        else:
            item_dto = SearchResultItemDTO(
                target_id=r.target_id,
                target_type=r.target_type,
                title=r.title,
                snippet=r.snippet,
                lexical_rank=r.lexical_rank,
                dense_rank=r.dense_rank,
                rrf_score=float(r.rrf_score),
                trust_zone=r.trust_zone,
                project_id=r.project_id,
                originating_event_id=str(r.originating_event_id),
            )
        result_items.append(item_dto)

    if not abstention_dto.accepted:
        status = "ABSTAINED"
        result_items = []
    elif len(result_items) == 0:
        status = "NO_MATCH"
    else:
        status = "SUCCESS"

    return SearchResponseDTO(
        query=query,
        status=status,
        results=result_items,
        abstention_decision=abstention_dto,
        lexical_count=int(detailed_res.get("lexical_count", 0)),
        dense_count=int(detailed_res.get("dense_count", 0)),
    )
