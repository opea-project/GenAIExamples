"""
Log Manager for storing and streaming agent activity logs
Supports Server-Sent Events (SSE) for real-time streaming
"""

import asyncio
import logging
from collections import defaultdict
from typing import Dict, List, Optional
from datetime import datetime
from .schemas import AgentLog, LogType

logger = logging.getLogger(__name__)


class LogManager:
    """
    Manages agent activity logs with SSE streaming support.
    Stores logs per job_id and provides async iteration for SSE.
    """

    def __init__(self, max_logs_per_job: int = 1000):
        """
        Initialize log manager

        Args:
            max_logs_per_job: Maximum logs to keep per job (circular buffer)
        """
        self.max_logs_per_job = max_logs_per_job
        self._logs: Dict[str, List[AgentLog]] = defaultdict(list)
        self._subscribers: Dict[str, List[asyncio.Queue]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def add_log(self, log: AgentLog) -> None:
        """
        Add a log entry and notify all subscribers

        Args:
            log: Agent log entry
        """
        async with self._lock:
            # Add to storage
            job_logs = self._logs[log.job_id]
            job_logs.append(log)

            # Maintain circular buffer
            if len(job_logs) > self.max_logs_per_job:
                job_logs.pop(0)

            # Notify all subscribers for this job
            dead_queues = []
            for queue in self._subscribers[log.job_id]:
                try:
                    await asyncio.wait_for(queue.put(log), timeout=1.0)
                except (asyncio.TimeoutError, asyncio.QueueFull):
                    dead_queues.append(queue)
                    logger.warning(f"Queue full or timeout for job {log.job_id}")

            # Clean up dead queues
            for queue in dead_queues:
                self._subscribers[log.job_id].remove(queue)

            # Log to console for debugging
            logger.info(f"[{log.job_id}] {log.log_type.value}: {log.message}")

    def log_sync(
        self,
        job_id: str,
        log_type: LogType,
        message: str,
        agent_name: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Synchronous logging helper (for use in sync code)

        Args:
            job_id: Job identifier
            log_type: Type of log
            message: Log message
            agent_name: Name of the agent (if applicable)
            metadata: Additional metadata
        """
        log = AgentLog(
            job_id=job_id,
            log_type=log_type,
            message=message,
            agent_name=agent_name,
            metadata=metadata
        )
        # Schedule the async add_log in the event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.add_log(log))
            else:
                loop.run_until_complete(self.add_log(log))
        except RuntimeError:
            # No event loop, just log to console
            logger.info(f"[{job_id}] {log_type.value}: {message}")

    async def log_async(
        self,
        job_id: str,
        log_type: LogType,
        message: str,
        agent_name: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Asynchronous logging helper

        Args:
            job_id: Job identifier
            log_type: Type of log
            message: Log message
            agent_name: Name of the agent (if applicable)
            metadata: Additional metadata
        """
        log = AgentLog(
            job_id=job_id,
            log_type=log_type,
            message=message,
            agent_name=agent_name,
            metadata=metadata
        )
        await self.add_log(log)

    def get_logs(self, job_id: str, limit: Optional[int] = None) -> List[AgentLog]:
        """
        Get all logs for a job

        Args:
            job_id: Job identifier
            limit: Maximum number of logs to return (most recent)

        Returns:
            List of logs
        """
        logs = self._logs.get(job_id, [])
        if limit:
            return logs[-limit:]
        return logs

    async def subscribe(self, job_id: str) -> asyncio.Queue:
        """
        Subscribe to real-time logs for a job (for SSE)

        Args:
            job_id: Job identifier

        Returns:
            Queue that will receive new logs
        """
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        async with self._lock:
            self._subscribers[job_id].append(queue)

            # Send existing logs immediately
            for log in self._logs.get(job_id, []):
                try:
                    await queue.put(log)
                except asyncio.QueueFull:
                    logger.warning(f"Initial logs queue full for job {job_id}")
                    break

        return queue

    async def unsubscribe(self, job_id: str, queue: asyncio.Queue) -> None:
        """
        Unsubscribe from logs

        Args:
            job_id: Job identifier
            queue: Queue to remove
        """
        async with self._lock:
            if queue in self._subscribers[job_id]:
                self._subscribers[job_id].remove(queue)

    def clear_job_logs(self, job_id: str) -> None:
        """
        Clear all logs for a job

        Args:
            job_id: Job identifier
        """
        if job_id in self._logs:
            del self._logs[job_id]
        if job_id in self._subscribers:
            del self._subscribers[job_id]


# Global log manager instance
_log_manager: Optional[LogManager] = None


def get_log_manager() -> LogManager:
    """
    Get or create the global log manager instance

    Returns:
        LogManager instance
    """
    global _log_manager
    if _log_manager is None:
        _log_manager = LogManager()
    return _log_manager
