import threading
import unittest
from src.gate.experience_service import InMemoryExperienceSink, NeuralExperienceService
from src.gate.models import NeuralExperienceRecord, TaskEvidence
from src.gate.enums import TaskExecutionStatus, ExperienceWritebackStatus

class TestAtomicIdempotencyConcurrency(unittest.TestCase):
    def test_same_key_concurrent_requests_yield_one_acceptance(self):
        sink = InMemoryExperienceSink()
        service = NeuralExperienceService(sink=sink)
        record = NeuralExperienceRecord(
            task_id="CONCURRENT-001",
            project_id="pub-dev-loop",
            repository="pubcoreagencia/pub-dev-loop",
            branch="main",
            status=TaskExecutionStatus.COMPLETED,
            objective="Concurrency proof",
            completed_at="2026-09-17T20:00:00Z",
            evidence=TaskEvidence(validation_passed=True, worktree_clean=True, push_succeeded=True, remote_verified=True, runtime_verified=True),
        )
        results = []
        lock = threading.Lock()

        def worker():
            result = service.record(record)
            with lock:
                results.append(result)

        threads = [threading.Thread(target=worker) for _ in range(16)]
        for t in threads: t.start()
        for t in threads: t.join()

        self.assertEqual(len(results), 16)
        self.assertEqual(sum(r.status == ExperienceWritebackStatus.ACCEPTED for r in results), 1)
        self.assertEqual(sum(r.status == ExperienceWritebackStatus.DUPLICATE for r in results), 15)
        self.assertEqual(len(sink.events), 1)
        self.assertEqual(len(sink.idempotency_records), 1)
        event_ids = {r.event_id for r in results}
        self.assertEqual(len(event_ids), 1)

if __name__ == "__main__":
    unittest.main()
