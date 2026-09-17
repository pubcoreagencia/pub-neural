"""
Continuous Observation Scheduler Daemon (V0.5.1).
Single coordinated background daemon managing periodic repository synchronization.
Runs every 15 minutes (configurable via OBSERVATION_SYNC_INTERVAL_SECONDS).
Thread-safe and supports graceful termination.
"""

from datetime import datetime, timezone
import logging
import os
import threading
import time
from typing import Optional

from src.ingestion.observation_sync import RepositoryObservationSync

logger = logging.getLogger("ObservationScheduler")


class ObservationScheduler:
    """Coordinates periodic continuous observation sync execution."""

    def __init__(
        self,
        db_url: str,
        interval_seconds: int = 900,  # 15 minutes
        internal_actor: str = "actor:system:observation-scheduler",
    ):
        self.db_url = db_url
        self.interval_seconds = max(60, interval_seconds)
        self.internal_actor = internal_actor
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._sync = RepositoryObservationSync(db_url=self.db_url, internal_actor=self.internal_actor)

    def start(self) -> None:
        """Start scheduler background daemon thread."""
        if self._thread and self._thread.is_alive():
            logger.warning("ObservationScheduler daemon is already running.")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, name="ObservationSchedulerThread", daemon=True)
        self._thread.start()
        logger.info(f"ObservationScheduler started (interval={self.interval_seconds}s).")

    def stop(self, timeout: float = 10.0) -> None:
        """Signal scheduler daemon to terminate gracefully."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout)
            logger.info("ObservationScheduler stopped cleanly.")

    def run_once(self) -> None:
        """Trigger an immediate synchronous sync execution."""
        try:
            logger.info("Executing observation sync cycle...")
            res = self._sync.run_sync()
            logger.info(
                f"Observation sync cycle completed: status={res.status}, "
                f"scanned={res.repositories_scanned}, created={res.observations_created}, "
                f"deduplicated={res.observations_deduplicated}, failed={res.observations_failed}"
            )
        except Exception as e:
            logger.error(f"Error in observation sync cycle: {e}", exc_info=True)

    def _run_loop(self) -> None:
        """Periodic background execution loop."""
        # Initial small delay to let server initialize completely
        if self._stop_event.wait(timeout=5.0):
            return

        while not self._stop_event.is_set():
            self.run_once()
            # Wait for next interval or stop signal
            if self._stop_event.wait(timeout=float(self.interval_seconds)):
                break


_global_scheduler: Optional[ObservationScheduler] = None
_scheduler_lock = threading.Lock()


def get_observation_scheduler(db_url: str, interval_seconds: Optional[int] = None) -> ObservationScheduler:
    global _global_scheduler
    with _scheduler_lock:
        if _global_scheduler is None:
            interval = interval_seconds or int(os.getenv("OBSERVATION_SYNC_INTERVAL_SECONDS", "900"))
            _global_scheduler = ObservationScheduler(db_url=db_url, interval_seconds=interval)
        return _global_scheduler
