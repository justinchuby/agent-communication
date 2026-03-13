# Group B Blackboard

## Task
status: in_progress
spec: experiments/02-ambiguous-spec/task-description.md
note: spec is DELIBERATELY VAGUE — architect must resolve ambiguities below

## Design Decisions

### Priority Model
decision: **1 = highest priority**
- Range: 1–10 inclusive. Values outside raise `InvalidPriorityError`.
- Default: 5
- Queue ordering: lower number runs first (1 before 2 before 10).
- Ties: FIFO by `submitted_at` timestamp.

### Retry Policy
decision: **3 max retries, exponential backoff**
- Default `max_retries`: 3 (configurable per-task, 0 = no retry)
- Backoff: exponential — `base_delay * 2^attempt` where `base_delay=1.0s`
  - Attempt 0: 1s, attempt 1: 2s, attempt 2: 4s
- Failure = any unhandled exception from the callable.
- After all retries exhausted → status `FAILED`, error stored in `Task.error`.
- Each retry increments `Task.attempts`.

### Timeout Behavior
decision: **30s default, raises TaskTimeoutError**
- Default: 30.0 seconds (configurable per-task via `timeout` field, `None` = no timeout)
- On timeout: task thread is marked timed out, status → `TIMED_OUT`
- A `TaskTimeoutError` is stored in `Task.error` (not re-raised to caller)
- Timed-out tasks are NOT retried.

### Concurrency Model
decision: **ThreadPoolExecutor, 4 default workers, configurable**
- Uses `concurrent.futures.ThreadPoolExecutor` (stdlib only, works with sync callables)
- Default `max_workers`: 4 (configurable at `TaskQueue.__init__`)
- Queue runs in a background daemon thread that pulls tasks and submits to pool.
- `start()` / `stop()` control the background processor.
- `stop(wait=True)` waits for running tasks; `stop(wait=False)` cancels pending.

### Status Transitions
decision: **7 states, transitions below**
```
States: PENDING, RUNNING, SUCCESS, FAILED, TIMED_OUT, RETRYING, CANCELLED

PENDING   → RUNNING     (auto: worker picks up task)
PENDING   → CANCELLED   (manual: user calls cancel)
RUNNING   → SUCCESS     (auto: callable returns without error)
RUNNING   → RETRYING    (auto: callable raises, retries remaining)
RUNNING   → FAILED      (auto: callable raises, no retries left)
RUNNING   → TIMED_OUT   (auto: exceeded timeout)
RUNNING   → CANCELLED   (manual: user calls cancel)
RETRYING  → RUNNING     (auto: after backoff delay)
```
- `RETRYING` tracks "waiting for next attempt" — distinct from `RUNNING`.
- Terminal states: `SUCCESS`, `FAILED`, `TIMED_OUT`, `CANCELLED`.

### Interface Contract
```python
from __future__ import annotations

import enum
import uuid
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


class TaskStatus(enum.Enum):
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
    TaskStatus.PENDING:  frozenset({TaskStatus.RUNNING, TaskStatus.CANCELLED}),
    TaskStatus.RUNNING:  frozenset({TaskStatus.SUCCESS, TaskStatus.RETRYING,
                                     TaskStatus.FAILED, TaskStatus.TIMED_OUT,
                                     TaskStatus.CANCELLED}),
    TaskStatus.RETRYING: frozenset({TaskStatus.RUNNING}),
    TaskStatus.SUCCESS:  frozenset(),
    TaskStatus.FAILED:   frozenset(),
    TaskStatus.TIMED_OUT: frozenset(),
    TaskStatus.CANCELLED: frozenset(),
}


@dataclass
class Task:
    func: Callable[..., Any]
    name: str = ""
    priority: int = 5          # 1=highest, 10=lowest
    max_retries: int = 3
    timeout: Optional[float] = 30.0  # seconds; None=no timeout
    args: tuple = ()
    kwargs: dict[str, Any] = field(default_factory=dict)
    # — auto-populated fields —
    task_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    status: TaskStatus = TaskStatus.PENDING
    attempts: int = 0
    submitted_at: float = field(default_factory=time.monotonic)
    error: Optional[str] = None
    result: Any = None


@dataclass
class TaskResult:
    task_id: str
    success: bool
    value: Any = None          # return value on success
    error: Optional[str] = None  # error message on failure
    duration: float = 0.0      # seconds


# --- Error types ---

class TaskQueueError(Exception):
    """Base error for taskqueue library."""

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


# --- TaskQueue interface (implemented in engine.py) ---

class TaskQueue:
    def __init__(self, max_workers: int = 4) -> None: ...
    def submit(self, task: Task) -> str: ...          # returns task_id
    def cancel(self, task_id: str) -> bool: ...       # True if cancelled
    def get_status(self, task_id: str) -> TaskStatus: ...
    def get_result(self, task_id: str) -> Optional[TaskResult]: ...
    def start(self) -> None: ...
    def stop(self, wait: bool = True) -> None: ...
    @property
    def pending_count(self) -> int: ...
    @property
    def active_count(self) -> int: ...
```
contract_status: done

## Assignments

| task-id | file | owner | status | notes |
|---------|------|-------|--------|-------|
| design | — | architect | done | all ambiguities resolved, interfaces in M:MOD |
| models | M:MOD | dev-a | done | added __post_init__ validation, __lt__ ordering, is_terminal, retries_remaining |
| pkg-init | M:INI | dev-a | done | exports all models + errors; lazy-imports TaskQueue from engine |
| engine | M:ENG | dev-b | done | TaskQueue: submit, cancel, retry, timeout, concurrency |
| review | all | reviewer | done(pass) | 2 minor issues, non-blocking |
| tests | T:TST | tester | done(pass) | 18/18 passed in 36s |
| fix | — | dev-a,dev-b | blocked(tests) | fix any failures |

## Findings
### F-1: retries_remaining off-by-one (M:MOD, minor)
`retries_remaining` uses `max(0, max_retries - attempts)` but `attempts` counts ALL executions including the initial (non-retry) one. After first failure (attempts=1, max_retries=3), returns 2 but 3 retries remain. Fix: `used = max(0, self.attempts - 1); return max(0, self.max_retries - used)`. Does NOT affect engine execution — engine uses its own check.

### F-2: import style inconsistency (M:INI, trivial)
`__init__.py` uses absolute imports (`from taskqueue.models`), `engine.py` uses relative (`from .models`). Prefer relative for intra-package consistency.

## Metrics
messages_sent: 1
clarifications: 0
