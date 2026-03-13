"""Task queue data models.

Owner: Developer A

Data structures for the task queue system:
- TaskStatus enum with 6 states (PENDING, RUNNING, SUCCESS, FAILED, RETRYING, CANCELLED)
- Task dataclass wrapping a callable with scheduling metadata
- TaskResult frozen dataclass for execution outcomes
- Error hierarchy rooted at TaskQueueError
"""

from __future__ import annotations

import enum
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


# ─── Errors ────────────────────────────────────────────────────────
# Defined first so Task.__post_init__ can reference InvalidPriorityError.

class TaskQueueError(Exception):
    """Base error for the task queue library."""


class TaskNotFoundError(TaskQueueError):
    """Raised when a task ID is not found in the queue."""


class TaskAlreadyExistsError(TaskQueueError):
    """Raised when submitting a task with a duplicate ID."""


class InvalidPriorityError(TaskQueueError, ValueError):
    """Raised when priority is outside the valid range (1–10)."""


class TaskTimeoutError(TaskQueueError):
    """Raised when a task exceeds its timeout duration."""


# ─── Task Status (finite state machine) ────────────────────────────
#
#  PENDING ──→ RUNNING ──→ SUCCESS   (terminal)
#                │
#                ├──→ FAILED    (terminal — retries exhausted)
#                │
#                └──→ RETRYING ──→ RUNNING  (back into execution)
#
#  Any non-terminal state ──→ CANCELLED  (terminal)
#

class TaskStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


TERMINAL_STATUSES: frozenset[TaskStatus] = frozenset({
    TaskStatus.SUCCESS,
    TaskStatus.FAILED,
    TaskStatus.CANCELLED,
})

# Valid transitions enforced by Task.transition_to()
_VALID_TRANSITIONS: dict[TaskStatus, frozenset[TaskStatus]] = {
    TaskStatus.PENDING: frozenset({TaskStatus.RUNNING, TaskStatus.CANCELLED}),
    TaskStatus.RUNNING: frozenset({TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.RETRYING, TaskStatus.CANCELLED}),
    TaskStatus.RETRYING: frozenset({TaskStatus.RUNNING, TaskStatus.CANCELLED}),
    TaskStatus.SUCCESS: frozenset(),
    TaskStatus.FAILED: frozenset(),
    TaskStatus.CANCELLED: frozenset(),
}


# ─── Priority ──────────────────────────────────────────────────────
# Lower number = higher priority.  Priority 1 is the HIGHEST.
# Valid range: 1–10 inclusive.  Default: 5.
PRIORITY_MIN = 1
PRIORITY_MAX = 10
PRIORITY_DEFAULT = 5


# ─── Task ──────────────────────────────────────────────────────────

@dataclass
class Task:
    """A unit of work submitted to the queue.

    User-provided fields (set at creation):
        fn, name, args, kwargs, priority, max_retries, timeout

    System-managed fields (mutated by the engine during execution):
        id, status, attempts, created_at, started_at, completed_at, result, error
    """

    fn: Callable[..., Any]
    name: str = ""
    args: tuple = ()
    kwargs: dict[str, Any] = field(default_factory=dict)
    priority: int = PRIORITY_DEFAULT
    max_retries: int = 3
    timeout: float = 30.0

    # System-managed — callers should NOT set these directly
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    status: TaskStatus = TaskStatus.PENDING
    attempts: int = 0
    created_at: float = field(default_factory=time.monotonic)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Any = None
    error: Optional[str] = None

    def __post_init__(self) -> None:
        if not callable(self.fn):
            raise TypeError(f"fn must be callable, got {type(self.fn).__name__}")
        if not (PRIORITY_MIN <= self.priority <= PRIORITY_MAX):
            raise InvalidPriorityError(
                f"Priority must be {PRIORITY_MIN}–{PRIORITY_MAX}, got {self.priority}"
            )

    # PriorityQueue ordering: lower priority number = higher urgency,
    # ties broken by creation time (FIFO).
    def __lt__(self, other: Task) -> bool:
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.created_at < other.created_at

    @property
    def is_terminal(self) -> bool:
        """True if the task is in a final state (SUCCESS, FAILED, CANCELLED)."""
        return self.status in TERMINAL_STATUSES

    @property
    def retries_remaining(self) -> int:
        """How many retry attempts are left."""
        used_retries = max(0, self.attempts - 1)
        return max(0, self.max_retries - used_retries)

    def transition_to(self, new_status: TaskStatus) -> None:
        """Transition to a new status, enforcing the state machine rules.

        Raises TaskQueueError if the transition is invalid.
        """
        allowed = _VALID_TRANSITIONS.get(self.status, frozenset())
        if new_status not in allowed:
            raise TaskQueueError(
                f"Invalid status transition: {self.status.value} → {new_status.value}"
            )
        self.status = new_status

    def to_result(self) -> TaskResult:
        """Create a TaskResult snapshot from this task's current state."""
        duration = 0.0
        if self.started_at is not None:
            end = self.completed_at if self.completed_at is not None else time.monotonic()
            duration = end - self.started_at
        error = self.error
        if self.status == TaskStatus.CANCELLED and error is None:
            error = "Task was cancelled"
        return TaskResult(
            task_id=self.id,
            success=self.status == TaskStatus.SUCCESS,
            result=self.result,
            error=error,
            duration=duration,
            attempts=self.attempts,
        )


# ─── TaskResult ────────────────────────────────────────────────────

@dataclass(frozen=True)
class TaskResult:
    """Immutable snapshot of a task's execution outcome."""

    task_id: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    duration: float = 0.0
    attempts: int = 0
