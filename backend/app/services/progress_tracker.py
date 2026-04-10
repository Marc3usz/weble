"""Progress tracking for Server-Sent Events streaming."""

import asyncio
from typing import Any, Callable, Dict, List, Optional
import json


class ProgressEvent:
    """A single progress event."""

    def __init__(
        self,
        stage: str,
        status: str,
        percentage: int,
        message: str = "",
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.stage = stage
        self.status = status
        self.percentage = percentage
        self.message = message
        self.data = data or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "stage": self.stage,
            "status": self.status,
            "percentage": self.percentage,
            "message": self.message,
            "data": self.data,
        }


class ProgressTracker:
    """Tracks and emits progress events for SSE streaming."""

    def __init__(self) -> None:
        self.subscribers: Dict[str, List[asyncio.Queue]] = {}  # job_id -> queue list
        self.event_history: Dict[str, List[ProgressEvent]] = {}  # job_id -> events

    async def emit(self, job_id: str, event: ProgressEvent) -> None:
        """Emit a progress event to all subscribers."""
        # Store in history
        if job_id not in self.event_history:
            self.event_history[job_id] = []
        self.event_history[job_id].append(event)

        # Send to all subscribers
        if job_id in self.subscribers:
            dead_queues = []
            for queue in self.subscribers[job_id]:
                try:
                    queue.put_nowait(event)
                except asyncio.QueueFull:
                    dead_queues.append(queue)

            # Remove dead queues
            for queue in dead_queues:
                self.subscribers[job_id].remove(queue)

    async def subscribe(self, job_id: str) -> asyncio.Queue:
        """Subscribe to progress events for a job."""
        if job_id not in self.subscribers:
            self.subscribers[job_id] = []

        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self.subscribers[job_id].append(queue)

        # Send history first
        if job_id in self.event_history:
            for event in self.event_history[job_id]:
                try:
                    queue.put_nowait(event)
                except asyncio.QueueFull:
                    pass

        return queue

    async def unsubscribe(self, job_id: str, queue: asyncio.Queue) -> None:
        """Unsubscribe from progress events."""
        if job_id in self.subscribers:
            if queue in self.subscribers[job_id]:
                self.subscribers[job_id].remove(queue)

    def get_history(self, job_id: str) -> List[ProgressEvent]:
        """Get event history for a job."""
        return self.event_history.get(job_id, [])

    async def clear(self, job_id: str) -> None:
        """Clear history and subscribers for a job."""
        self.subscribers.pop(job_id, None)
        self.event_history.pop(job_id, None)


# Global instance
_tracker: Optional[ProgressTracker] = None


async def get_progress_tracker() -> ProgressTracker:
    """Get or create the global progress tracker."""
    global _tracker
    if _tracker is None:
        _tracker = ProgressTracker()
    return _tracker
