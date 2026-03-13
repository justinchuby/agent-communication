"""Task queue data models.

Owner: Developer A

Data structures for the task queue system. Interfaces defined by Architect.
Dev A: flesh out any helper methods needed; do NOT change field names/types.
"""

from __future__ import annotations

import enum
import uuid
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


# ---------------------------------------------------------------------------
# Status enum
# ---------------------------------------------------------------------------

class TaskStatus(enum.Enum):
    """Lifecycle states for a task."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


TERMINAL_STATUSES: frozenset[TaskStatus] = frozenset({
    TaskStatus.SUCCESS,
    TaskStatus.FAILED,
    TaskStatus.TIMED_OUT,
    TaskStatus.CANCELLED,
})

VALID_TRANSITIONS: dict[TaskStatus, frozenset[TaskStatus]] = {
    TaskStatus.PENDING:   frozenset({TaskStatus.RUNNING, TaskStatus.CANCELLED}),
    TaskStatus.RUNNING:   frozenset({TaskStatus.SUCCESS, TaskStatus.RETRYING,
                                      TaskStatus.FAILED, TaskStatus.TIMED_OUT,
                                      TaskStatus.CANCELLED}),
    TaskStatus.RETRYING:  frozenset({TaskStatus.RUNNING}),
    TaskStatus.SUCCESS:   frozenset(),
    TaskStatus.FAILED:    frozenset(),
    TaskStatus.TIMED_OUT: frozenset(),
    TaskStatus.CANCELLED: frozenset(),
}


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """A unit of work submitted to the queue.

    Priority: 1 = highest, 10 = lowest.  Default 5.
    Ordering: lower priority number runs first; ties broken by submitted_at (FIFO).
    """
    func: Callable[..., Any]
    name: str = ""
    priority: int = 5
    max_retries: int = 3
    timeout: Optional[float] = 30.0   # seconds; None = no timeout
    args: tuple = ()
    kwargs: dict[str, Any] = field(default_factory=dict)
    # — auto-populated on submit —
    task_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    status: TaskStatus = TaskStatus.PENDING
    attempts: int = 0
    submitted_at: float = field(default_factory=time.monotonic)
    error: Optional[str] = None
    result: Any = None

    def __post_init__(self) -> None:
        if not (1 <= self.priority <= 10):
            raise InvalidPriorityError(
                f"Priority must be 1-10, got {self.priority}"
            )

    def __lt__(self, other: object) -> bool:
        """Ordering for priority queue: lower priority number first, then FIFO."""
        if not isinstance(other, Task):
            return NotImplemented
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.submitted_at < other.submitted_at

    def transition(self, new_status: TaskStatus) -> None:
        """Move to *new_status*, raising InvalidTransitionError if illegal."""
        if new_status not in VALID_TRANSITIONS[self.status]:
            raise InvalidTransitionError(
                f"Cannot transition from {self.status.value} to {new_status.value}"
            )
        self.status = new_status

    @property
    def is_terminal(self) -> bool:
        return self.status in TERMINAL_STATUSES

    @property
    def retries_remaining(self) -> int:
        """Number of retry attempts still available if the task keeps failing.

        Engine increments attempts before each execution (including initial),
        so retries_remaining accounts for attempts counting the initial run.
        """
        if self.attempts == 0:
            return self.max_retries
        return max(0, self.max_retries - self.attempts + 1)


@dataclass
class TaskResult:
    """Outcome of executing a task."""
    task_id: str
    success: bool
    value: Any = None
    error: Optional[str] = None
    duration: float = 0.0   # seconds


# ---------------------------------------------------------------------------
# Error types
# ---------------------------------------------------------------------------

class TaskQueueError(Exception):
    """Base error for the taskqueue library."""


class InvalidPriorityError(TaskQueueError):
    """Priority outside valid range 1-10."""


class TaskTimeoutError(TaskQueueError):
    """Task exceeded its timeout."""


class TaskNotFoundError(TaskQueueError):
    """No task with the given ID exists."""


class InvalidTransitionError(TaskQueueError):
    """Status transition not allowed."""


class QueueStoppedError(TaskQueueError):
    """Attempted to submit to a stopped queue."""
