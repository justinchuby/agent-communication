"""taskqueue — A Python task queue library.

Public API re-exports for convenience.
"""

from taskqueue.models import (
    Task,
    TaskResult,
    TaskStatus,
    TERMINAL_STATUSES,
    VALID_TRANSITIONS,
    TaskQueueError,
    InvalidPriorityError,
    TaskTimeoutError,
    TaskNotFoundError,
    InvalidTransitionError,
    QueueStoppedError,
)

__all__ = [
    # Data models
    "Task",
    "TaskResult",
    "TaskStatus",
    # Constants
    "TERMINAL_STATUSES",
    "VALID_TRANSITIONS",
    # Errors
    "TaskQueueError",
    "InvalidPriorityError",
    "TaskTimeoutError",
    "TaskNotFoundError",
    "InvalidTransitionError",
    "QueueStoppedError",
]


def _import_engine() -> None:
    """Lazy-import engine exports so init works even if engine isn't ready yet."""
    # pylint: disable=import-outside-toplevel
    from taskqueue.engine import TaskQueue  # noqa: F811

    globals()["TaskQueue"] = TaskQueue
    __all__.append("TaskQueue")


try:
    _import_engine()
except ImportError:
    pass
