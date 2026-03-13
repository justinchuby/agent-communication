"""taskqueue — A Python task queue library.

Submit callable tasks with priority, retry on failure, and track status.
Uses ThreadPoolExecutor for concurrent execution.

Quick start:
    from taskqueue import TaskQueue, TaskStatus

    with TaskQueue(max_workers=4) as q:
        task_id = q.submit(my_function, priority=1)
        result = q.get_result(task_id)
"""

# Models and data types
from taskqueue.models import (
    Task,
    TaskResult,
    TaskStatus,
    TERMINAL_STATUSES,
    PRIORITY_MIN,
    PRIORITY_MAX,
    PRIORITY_DEFAULT,
)

# Error types
from taskqueue.models import (
    TaskQueueError,
    TaskNotFoundError,
    TaskAlreadyExistsError,
    InvalidPriorityError,
    TaskTimeoutError,
)

# Engine (imported last — depends on models)
from taskqueue.engine import TaskQueue

__all__ = [
    # Core classes
    "TaskQueue",
    "Task",
    "TaskResult",
    "TaskStatus",
    # Constants
    "TERMINAL_STATUSES",
    "PRIORITY_MIN",
    "PRIORITY_MAX",
    "PRIORITY_DEFAULT",
    # Errors
    "TaskQueueError",
    "TaskNotFoundError",
    "TaskAlreadyExistsError",
    "InvalidPriorityError",
    "TaskTimeoutError",
]
