"""
Internal Neural Experience Service for PUB Neural Knowledge Gate (Phase D).
Provides an in-process service boundary between caller experience contracts
and the underlying event sourcing and idempotency engine.
"""

from datetime import datetime, timezone
import hashlib
from typing import Any, Dict, List, Optional, Protocol, Union
import uuid

from .enums import ExperienceWritebackStatus, PromotionState, TaskExecutionStatus
from .exceptions import GateTransportError, GateValidationError
from .models import (
    CandidateFinding,
    ExperienceIngestionResult,
    NeuralExperienceRecord,
    TaskEvidence,
)


class ExperienceSink(Protocol):
    """Protocol for persisting experience events and idempotency records."""

    def check_idempotency(self, idempotency_key: str) -> Optional[Dict[str, Any]]:
        ...

    def record_idempotency(
        self,
        idempotency_key: str,
        request_hash: str,
        resulting_event_id: uuid.UUID,
        response_payload: Dict[str, Any],
        ttl_days: int = 30,
    ) -> None:
        ...

    def append_canonical_event(
        self,
        event_id: uuid.UUID,
        event_type: str,
        stream_id: str,
        stream_version: Optional[int] = None,
        payload: Optional[Dict[str, Any]] = None,
        parent_event_ids: Optional[List[uuid.UUID]] = None,
        producer_version: str = "v1.0.0",
        signature: Optional[str] = None,
    ) -> int:
        ...


class InMemoryExperienceSink:
    """
    Hermetic in-memory sink for unit testing and offline execution.
    Maintains append-only event log and idempotency registry.
    """

    def __init__(self) -> None:
        self.events: Dict[str, Dict[str, Any]] = {}
        self.idempotency_records: Dict[str, Dict[str, Any]] = {}
        self.global_sequence_counter: int = 0

    def check_idempotency(self, idempotency_key: str) -> Optional[Dict[str, Any]]:
        return self.idempotency_records.get(idempotency_key)

    def record_idempotency(
        self,
        idempotency_key: str,
        request_hash: str,
        resulting_event_id: uuid.UUID,
        response_payload: Dict[str, Any],
        ttl_days: int = 30,
    ) -> None:
        self.idempotency_records[idempotency_key] = {
            "idempotency_key": idempotency_key,
            "request_hash": request_hash,
            "resulting_event_id": str(resulting_event_id),
            "response_payload": response_payload,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    def append_canonical_event(
        self,
        event_id: uuid.UUID,
        event_type: str,
        stream_id: str,
        stream_version: Optional[int] = None,
        payload: Optional[Dict[str, Any]] = None,
        parent_event_ids: Optional[List[uuid.UUID]] = None,
        producer_version: str = "v1.0.0",
        signature: Optional[str] = None,
    ) -> int:
        self.global_sequence_counter += 1
        seq = self.global_sequence_counter
        self.events[str(event_id)] = {
            "id": str(event_id),
            "global_sequence": seq,
            "event_type": event_type,
            "stream_id": stream_id,
            "stream_version": stream_version or seq,
            "producer_version": producer_version,
            "payload": payload or {},
            "parent_event_ids": [str(pid) for pid in (parent_event_ids or [])],
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
        return seq


class NeuralExperienceService:
    """
    Core application service executing experience writeback for the Neural Knowledge Gate.
    Enforces:
      - Contract validation
      - Provenance, evidence, and trace preservation
      - Candidate findings retention (Candidate != Validated)
      - Idempotency protection against duplicate ingestion
      - Event sourcing integration
    """

    def __init__(self, sink: Optional[ExperienceSink] = None) -> None:
        self.sink = sink or InMemoryExperienceSink()

    def generate_idempotency_key(self, record: NeuralExperienceRecord) -> str:
        """Derive a deterministic idempotency key for task experience."""
        commit_part = record.commit_sha or "no-commit"
        raw_key = f"exp:{record.repository}:{record.task_id}:{commit_part}:{record.ingestion_source}"
        return raw_key

    def record(
        self, experience: Union[NeuralExperienceRecord, Dict[str, Any]]
    ) -> ExperienceIngestionResult:
        """
        Ingest a task experience record into PUB Neural.
        Returns a strongly-typed ExperienceIngestionResult respecting all gate contracts.
        """
        # 1. Structural Contract Validation
        if isinstance(experience, dict):
            try:
                validated_record = NeuralExperienceRecord.from_dict(experience)
            except Exception as e:
                task_id = str(experience.get("taskId", experience.get("task_id", "unknown")))
                e_id = experience.get("executionId", experience.get("execution_id"))
                c_id = experience.get("correlationId", experience.get("correlation_id"))
                return ExperienceIngestionResult(
                    status=ExperienceWritebackStatus.INVALID_REQUEST,
                    task_id=task_id,
                    reason=f"Structural experience validation failed: {e}",
                    execution_id=e_id,
                    correlation_id=c_id,
                )
        elif isinstance(experience, NeuralExperienceRecord):
            validated_record = experience
        else:
            return ExperienceIngestionResult(
                status=ExperienceWritebackStatus.INVALID_REQUEST,
                task_id="unknown",
                reason=f"Invalid experience type: expected NeuralExperienceRecord or dict, got {type(experience).__name__}",
            )

        execution_id = validated_record.execution_id
        correlation_id = validated_record.correlation_id

        # 2. Invariant: Candidate findings must remain strictly CANDIDATE
        # Never promote automatically to VALIDATED or ADOPTED
        candidate_count = len(validated_record.candidate_findings)

        # 3. Idempotency Check
        idempotency_key = self.generate_idempotency_key(validated_record)
        request_hash = hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest()

        try:
            existing = self.sink.check_idempotency(idempotency_key)
            if existing:
                resulting_event_id = str(existing.get("resulting_event_id", ""))
                return ExperienceIngestionResult(
                    status=ExperienceWritebackStatus.DUPLICATE,
                    task_id=validated_record.task_id,
                    event_id=resulting_event_id,
                    idempotency_key=idempotency_key,
                    is_duplicate=True,
                    candidate_findings_count=candidate_count,
                    recorded_at=existing.get("created_at"),
                    reason="Duplicate experience record acknowledged (idempotent)",
                    metadata={"idempotent_replay": True},
                    execution_id=execution_id,
                    correlation_id=correlation_id,
                )
        except GateTransportError as e:
            return ExperienceIngestionResult(
                status=ExperienceWritebackStatus.UNAVAILABLE,
                task_id=validated_record.task_id,
                reason=f"Idempotency storage backend unavailable: {e}",
                execution_id=execution_id,
                correlation_id=correlation_id,
            )
        except (ConnectionError, TimeoutError, OSError) as e:
            return ExperienceIngestionResult(
                status=ExperienceWritebackStatus.UNAVAILABLE,
                task_id=validated_record.task_id,
                reason=f"Idempotency backend unreachable: {e}",
                execution_id=execution_id,
                correlation_id=correlation_id,
            )
        except Exception as e:
            err_name = type(e).__name__
            if "OperationalError" in err_name or "InterfaceError" in err_name:
                return ExperienceIngestionResult(
                    status=ExperienceWritebackStatus.UNAVAILABLE,
                    task_id=validated_record.task_id,
                    reason=f"Database connection error during idempotency check: {e}",
                    execution_id=execution_id,
                    correlation_id=correlation_id,
                )
            return ExperienceIngestionResult(
                status=ExperienceWritebackStatus.INTERNAL_ERROR,
                task_id=validated_record.task_id,
                reason=f"Unexpected error during idempotency evaluation: {e}",
                execution_id=execution_id,
                correlation_id=correlation_id,
            )

        # 4. Event Generation and Persistence
        ns = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
        event_id = uuid.uuid5(ns, f"exp:{idempotency_key}:{validated_record.completed_at}")
        stream_id = f"stream:task:{validated_record.task_id}"

        # Preserve canonical execution payload ensuring Candidate != Validated
        event_payload = validated_record.to_dict()
        event_payload["candidateState"] = PromotionState.CANDIDATE.value
        event_payload["executionId"] = execution_id
        event_payload["correlationId"] = correlation_id

        try:
            seq = self.sink.append_canonical_event(
                event_id=event_id,
                event_type="TASK_EXPERIENCE_RECORDED",
                stream_id=stream_id,
                payload=event_payload,
                producer_version="v1.0.0",
            )

            result_obj = ExperienceIngestionResult(
                status=ExperienceWritebackStatus.ACCEPTED,
                task_id=validated_record.task_id,
                event_id=str(event_id),
                idempotency_key=idempotency_key,
                is_duplicate=False,
                candidate_findings_count=candidate_count,
                recorded_at=datetime.now(timezone.utc).isoformat(),
                metadata={"global_sequence": seq},
                execution_id=execution_id,
                correlation_id=correlation_id,
            )

            # Record idempotency record
            self.sink.record_idempotency(
                idempotency_key=idempotency_key,
                request_hash=request_hash,
                resulting_event_id=event_id,
                response_payload=result_obj.to_dict(),
            )

            return result_obj

        except GateTransportError as e:
            return ExperienceIngestionResult(
                status=ExperienceWritebackStatus.UNAVAILABLE,
                task_id=validated_record.task_id,
                reason=f"Event sourcing backend unavailable: {e}",
                execution_id=execution_id,
                correlation_id=correlation_id,
            )
        except (ConnectionError, TimeoutError, OSError) as e:
            return ExperienceIngestionResult(
                status=ExperienceWritebackStatus.UNAVAILABLE,
                task_id=validated_record.task_id,
                reason=f"Event sourcing backend connection failed: {e}",
                execution_id=execution_id,
                correlation_id=correlation_id,
            )
        except Exception as e:
            err_name = type(e).__name__
            if "OperationalError" in err_name or "InterfaceError" in err_name:
                return ExperienceIngestionResult(
                    status=ExperienceWritebackStatus.UNAVAILABLE,
                    task_id=validated_record.task_id,
                    reason=f"Database operational failure during event append: {e}",
                    execution_id=execution_id,
                    correlation_id=correlation_id,
                )
            return ExperienceIngestionResult(
                status=ExperienceWritebackStatus.INTERNAL_ERROR,
                task_id=validated_record.task_id,
                reason=f"Unexpected internal error during experience persistence: {e}",
                execution_id=execution_id,
                correlation_id=correlation_id,
            )
