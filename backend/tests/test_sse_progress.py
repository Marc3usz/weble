"""Tests for Server-Sent Events progress tracking."""

import pytest
import asyncio
from app.services.progress_tracker import ProgressTracker, ProgressEvent


@pytest.fixture
async def progress_tracker() -> ProgressTracker:
    """Create a progress tracker for testing."""
    return ProgressTracker()


class TestProgressTracker:
    """Test ProgressTracker implementation."""

    @pytest.mark.asyncio
    async def test_emit_and_subscribe(self, progress_tracker: ProgressTracker):
        """Test emitting events and subscribing to them."""
        job_id = "job-123"
        queue = await progress_tracker.subscribe(job_id)

        # Emit an event
        event = ProgressEvent(
            stage="loading",
            status="processing",
            percentage=50,
            message="Loading file...",
        )
        await progress_tracker.emit(job_id, event)

        # Retrieve the event
        received_event = queue.get_nowait()
        assert received_event.stage == "loading"
        assert received_event.percentage == 50
        assert received_event.message == "Loading file..."

    @pytest.mark.asyncio
    async def test_multiple_subscribers(self, progress_tracker: ProgressTracker):
        """Test multiple subscribers receiving the same event."""
        job_id = "job-123"
        queue1 = await progress_tracker.subscribe(job_id)
        queue2 = await progress_tracker.subscribe(job_id)

        event = ProgressEvent(
            stage="processing",
            status="running",
            percentage=75,
            message="Processing...",
        )
        await progress_tracker.emit(job_id, event)

        # Both subscribers should receive the event
        event1 = queue1.get_nowait()
        event2 = queue2.get_nowait()

        assert event1.percentage == 75
        assert event2.percentage == 75

    @pytest.mark.asyncio
    async def test_event_history(self, progress_tracker: ProgressTracker):
        """Test event history is preserved."""
        job_id = "job-123"

        # Emit some events before subscribing
        for i in range(3):
            event = ProgressEvent(
                stage="stage-1",
                status="processing",
                percentage=i * 33,
                message=f"Progress {i}...",
            )
            await progress_tracker.emit(job_id, event)

        # Subscribe and get history
        queue = await progress_tracker.subscribe(job_id)

        # Should receive all history events
        for i in range(3):
            received_event = queue.get_nowait()
            assert received_event.percentage == i * 33

    @pytest.mark.asyncio
    async def test_get_history(self, progress_tracker: ProgressTracker):
        """Test retrieving event history."""
        job_id = "job-123"

        events = [
            ProgressEvent("stage-1", "processing", 25, "First"),
            ProgressEvent("stage-2", "processing", 50, "Second"),
            ProgressEvent("stage-3", "processing", 75, "Third"),
        ]

        for event in events:
            await progress_tracker.emit(job_id, event)

        history = progress_tracker.get_history(job_id)
        assert len(history) == 3
        assert history[0].message == "First"
        assert history[2].percentage == 75

    @pytest.mark.asyncio
    async def test_unsubscribe(self, progress_tracker: ProgressTracker):
        """Test unsubscribing from events."""
        job_id = "job-123"
        queue = await progress_tracker.subscribe(job_id)

        # Unsubscribe
        await progress_tracker.unsubscribe(job_id, queue)

        # Emit an event (should not be received by unsubscribed queue)
        event = ProgressEvent("stage", "processing", 50, "Test")
        await progress_tracker.emit(job_id, event)

        # Queue should be empty
        assert queue.empty()

    @pytest.mark.asyncio
    async def test_clear_job(self, progress_tracker: ProgressTracker):
        """Test clearing a job's history and subscribers."""
        job_id = "job-123"
        queue = await progress_tracker.subscribe(job_id)

        event = ProgressEvent("stage", "processing", 50, "Test")
        await progress_tracker.emit(job_id, event)

        # Clear the job
        await progress_tracker.clear(job_id)

        # History should be empty
        history = progress_tracker.get_history(job_id)
        assert len(history) == 0

    @pytest.mark.asyncio
    async def test_progress_event_to_dict(self):
        """Test converting progress event to dictionary."""
        event = ProgressEvent(
            stage="loading",
            status="processing",
            percentage=50,
            message="Loading...",
            data={"eta_seconds": 30, "file_size": 1024},
        )

        event_dict = event.to_dict()
        assert event_dict["stage"] == "loading"
        assert event_dict["status"] == "processing"
        assert event_dict["percentage"] == 50
        assert event_dict["message"] == "Loading..."
        assert event_dict["data"]["eta_seconds"] == 30

    @pytest.mark.asyncio
    async def test_queue_full_handling(self, progress_tracker: ProgressTracker):
        """Test handling of full queues."""
        job_id = "job-123"

        # Create queue with small max size
        queue = asyncio.Queue(maxsize=2)
        progress_tracker.subscribers[job_id] = [queue]

        # Fill the queue
        for i in range(3):
            event = ProgressEvent("stage", "processing", i * 33, f"Event {i}")
            await progress_tracker.emit(job_id, event)

        # First event should be in queue
        event = queue.get_nowait()
        assert event.message == "Event 0"

        # Queue should not be completely full due to dead queue removal
        # (depends on implementation details)

    @pytest.mark.asyncio
    async def test_multiple_jobs(self, progress_tracker: ProgressTracker):
        """Test tracking progress for multiple jobs."""
        job1_queue = await progress_tracker.subscribe("job-1")
        job2_queue = await progress_tracker.subscribe("job-2")

        # Emit events for different jobs
        event1 = ProgressEvent("stage-1", "processing", 50, "Job 1 event")
        event2 = ProgressEvent("stage-2", "processing", 75, "Job 2 event")

        await progress_tracker.emit("job-1", event1)
        await progress_tracker.emit("job-2", event2)

        # Each queue should have its respective event
        received1 = job1_queue.get_nowait()
        received2 = job2_queue.get_nowait()

        assert received1.message == "Job 1 event"
        assert received2.message == "Job 2 event"

    @pytest.mark.asyncio
    async def test_empty_history_for_nonexistent_job(self, progress_tracker: ProgressTracker):
        """Test retrieving history for non-existent job."""
        history = progress_tracker.get_history("non-existent-job")
        assert len(history) == 0
        assert history == []
