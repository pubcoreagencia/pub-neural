"""
Internal Neural Query Service implementation.
Provides an in-process service boundary between caller query contracts
and the underlying retrieval engine.
"""

from typing import Any, Dict, List, Optional, Union

from .enums import ConflictState, FreshnessState, GateStatus, KnowledgeClass
from .exceptions import GateTransportError, GateValidationError
from .models import (
    AbstentionMetadata,
    ContradictionItem,
    NeuralKnowledgeItem,
    NeuralQueryRequest,
    NeuralQueryResponse,
)
from .retrieval_adapter import NeuralResultMapper, NeuralRetrievalEngine, RetrievalBatch


class NeuralQueryService:
    """
    Core application service executing knowledge queries for the Neural Knowledge Gate.
    Coordinates contract validation, retrieval delegation, domain filtering,
    abstention enforcement, and canonical response creation.
    """

    def __init__(
        self,
        retrieval_engine: NeuralRetrievalEngine,
        result_mapper: Optional[NeuralResultMapper] = None,
    ):
        if not isinstance(retrieval_engine, NeuralRetrievalEngine):
            if not hasattr(retrieval_engine, "search_knowledge") or not callable(getattr(retrieval_engine, "search_knowledge")):
                raise TypeError("retrieval_engine must implement NeuralRetrievalEngine protocol (search_knowledge)")
        self.retrieval_engine = retrieval_engine
        self.mapper = result_mapper or NeuralResultMapper()

    def query(self, request: Union[NeuralQueryRequest, Dict[str, Any]], bearer_token: Optional[str] = None) -> NeuralQueryResponse:
        """
        Execute a knowledge query against the injected retrieval engine.
        Returns a strongly-typed NeuralQueryResponse respecting all gate contracts.
        """
        # 1. Validate / Normalize Request
        if isinstance(request, dict):
            try:
                validated_req = NeuralQueryRequest.from_dict(request)
            except Exception as e:
                req_id = str(request.get("request_id", request.get("requestId", "unknown"))) if isinstance(request, dict) else "unknown"
                t_id = request.get("task_id", request.get("taskId")) if isinstance(request, dict) else None
                e_id = request.get("execution_id", request.get("executionId")) if isinstance(request, dict) else None
                c_id = request.get("correlation_id", request.get("correlationId")) if isinstance(request, dict) else None
                return NeuralQueryResponse(
                    request_id=req_id,
                    status=GateStatus.INVALID_REQUEST,
                    results=[],
                    reason=f"Structural request validation failed: {e}",
                    task_id=t_id,
                    execution_id=e_id,
                    correlation_id=c_id,
                )
        elif isinstance(request, NeuralQueryRequest):
            validated_req = request
        else:
            return NeuralQueryResponse(
                request_id="unknown",
                status=GateStatus.INVALID_REQUEST,
                results=[],
                reason=f"Invalid request type: expected NeuralQueryRequest or dict, got {type(request).__name__}",
            )

        task_id = validated_req.task_id
        execution_id = validated_req.execution_id
        correlation_id = validated_req.correlation_id

        # 2. Query Retrieval Engine
        try:
            batch = self.retrieval_engine.search_knowledge(
                query=validated_req.objective,
                trust_zone=validated_req.caller.trust_zone,
                project_id=validated_req.project_id,
                limit=validated_req.limit,
                knowledge_classes=validated_req.requested_knowledge_classes,
                bearer_token=bearer_token,
            )
        except GateTransportError as e:
            return NeuralQueryResponse(
                request_id=validated_req.request_id,
                status=GateStatus.UNAVAILABLE,
                results=[],
                reason=f"Retrieval backend unavailable: {e}",
                task_id=task_id,
                execution_id=execution_id,
                correlation_id=correlation_id,
            )
        except (ConnectionError, TimeoutError, OSError) as e:
            return NeuralQueryResponse(
                request_id=validated_req.request_id,
                status=GateStatus.UNAVAILABLE,
                results=[],
                reason=f"Retrieval network/service unreachable: {e}",
                task_id=task_id,
                execution_id=execution_id,
                correlation_id=correlation_id,
            )
        except Exception as e:
            err_name = type(e).__name__
            if "OperationalError" in err_name or "InterfaceError" in err_name:
                return NeuralQueryResponse(
                    request_id=validated_req.request_id,
                    status=GateStatus.UNAVAILABLE,
                    results=[],
                    reason=f"Database connection error: {e}",
                    task_id=task_id,
                    execution_id=execution_id,
                    correlation_id=correlation_id,
                )
            return NeuralQueryResponse(
                request_id=validated_req.request_id,
                status=GateStatus.INTERNAL_ERROR,
                results=[],
                reason=f"Internal retrieval processing error: {e}",
                task_id=task_id,
                execution_id=execution_id,
                correlation_id=correlation_id,
            )

        if not isinstance(batch, RetrievalBatch):
            return NeuralQueryResponse(
                request_id=validated_req.request_id,
                status=GateStatus.INTERNAL_ERROR,
                results=[],
                reason=f"Retrieval engine returned invalid batch type: {type(batch).__name__}",
                task_id=task_id,
                execution_id=execution_id,
                correlation_id=correlation_id,
            )

        # 3. Evaluate Abstention
        # When abstention policy triggers, status MUST be ABSTAIN with abstention metadata
        if batch.abstention_decision is not None and not batch.abstention_decision.accepted:
            decision = batch.abstention_decision
            threshold = getattr(decision, "threshold_applied", getattr(self.retrieval_engine, "min_dense_similarity", None))
            abst_meta = AbstentionMetadata(
                abstained=True,
                decision_reason=decision.reason,
                top_dense_similarity=decision.top_dense_similarity,
                top_rrf_score=decision.top_rrf_score,
                lexical_candidate_count=decision.lexical_candidate_count,
                dense_candidate_count=decision.dense_candidate_count,
                threshold_applied=threshold,
            )
            return NeuralQueryResponse(
                request_id=validated_req.request_id,
                status=GateStatus.ABSTAIN,
                results=[],
                abstention=abst_meta,
                reason=f"Retrieval abstention policy rejected low-confidence candidates: {decision.reason}",
                metadata=batch.metadata,
                task_id=task_id,
                execution_id=execution_id,
                correlation_id=correlation_id,
            )

        # 4. Map results to NeuralKnowledgeItem
        mapped_items: List[NeuralKnowledgeItem] = []
        for r in batch.results:
            mapped_items.append(self.mapper.map_result(r, default_project_id=validated_req.project_id))

        # 5. Apply requested knowledge classes filter
        if validated_req.requested_knowledge_classes:
            allowed_classes = set(validated_req.requested_knowledge_classes)
            filtered_items = [it for it in mapped_items if it.knowledge_class in allowed_classes]
        else:
            filtered_items = mapped_items

        # Apply limit
        filtered_items = filtered_items[:validated_req.limit]

        # 6. Check NO_MATCH (empty results when query is valid and not abstained)
        if len(filtered_items) == 0:
            return NeuralQueryResponse(
                request_id=validated_req.request_id,
                status=GateStatus.NO_MATCH,
                results=[],
                reason=f"No matching knowledge found for query '{validated_req.objective}'",
                metadata=batch.metadata,
                task_id=task_id,
                execution_id=execution_id,
                correlation_id=correlation_id,
            )

        # 7. Check CONFLICT (explicit contradictory state in batch or items)
        has_item_contradiction = any(it.conflict_state == ConflictState.CONTRADICTORY for it in filtered_items)
        if batch.contradictions or has_item_contradiction:
            contradictions = list(batch.contradictions)
            if not contradictions and has_item_contradiction:
                contra_items = [it for it in filtered_items if it.conflict_state == ConflictState.CONTRADICTORY]
                for c_item in contra_items:
                    contradictions.append(ContradictionItem(
                        item_a_id=c_item.id,
                        item_b_id="unknown_counterpart",
                        reason=f"Item {c_item.id} is marked in CONTRADICTORY state",
                    ))
            return NeuralQueryResponse(
                request_id=validated_req.request_id,
                status=GateStatus.CONFLICT,
                results=filtered_items,
                contradictions=contradictions,
                reason="Contradictory knowledge detected across retrieved results",
                metadata=batch.metadata,
                task_id=task_id,
                execution_id=execution_id,
                correlation_id=correlation_id,
            )

        # 8. Check STALE
        if batch.is_stale or any(it.freshness.is_stale for it in filtered_items):
            return NeuralQueryResponse(
                request_id=validated_req.request_id,
                status=GateStatus.STALE,
                results=filtered_items,
                reason="Retrieved knowledge contains stale or diverged references",
                metadata=batch.metadata,
                task_id=task_id,
                execution_id=execution_id,
                correlation_id=correlation_id,
            )

        # 9. SUCCESS
        return NeuralQueryResponse(
            request_id=validated_req.request_id,
            status=GateStatus.SUCCESS,
            results=filtered_items,
            metadata=batch.metadata,
            task_id=task_id,
            execution_id=execution_id,
            correlation_id=correlation_id,
        )
