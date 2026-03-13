"""Task queue processing engine.

Owner: Developer B

Core queue engine: priority scheduling, execution, retry with exponential
backoff, timeout handling, and thread-pool concurrency.

Design decisions (from architect blackboard):
- Priority 1 = highest, 10 = lowest. Ties broken by submit time (FIFO).
- Retry: up to max_retries per task, exponential backoff (1s, 2s, 4s, …).
- Timeout: default 30s per task. Timed-out tasks are NOT retried.
- Concurrency: ThreadPoolExecutor, default 4 workers (configurable).
- Background dispatcher thread pulls from priority queue, submits to pool.
"""

from __future__ import annotations

import heapq
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from .models import (
    Task,
    TaskResult,
    TaskStatus,
    InvalidPriorityError,
    TaskNotFoundError,
    TaskTimeoutError,
    QueueStoppedError,
)

_BACKOFF_BASE: float = 1.0  # seconds


class TaskQueue:
    """Priority-based task queue with retry, timeout, and concurrency."""

    def __init__(self, max_workers: int = 4) -> None:
        self._max_workers = max_workers
        self._tasks: dict[str, Task] = {}
        self._results: dict[str, TaskResult] = {}
        # Min-heap ordered by (priority, submitted_at, task_id)
        self._queue: list[tuple[int, float, str]] = []
        self._lock = threading.Lock()
        self._has_work = threading.Event()
        self._executor: Optional[ThreadPoolExecutor] = None
        self._dispatcher_thread: Optional[threading.Thread] = None
        self._running = False
        self._active_count = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def submit(self, task: Task) -> str:
        """Add *task* to the queue. Returns the task ID.

        Raises QueueStoppedError if the queue has not been started.
        Raises InvalidPriorityError if priority is outside 1–10.
        """
        if not self._running:
            raise QueueStoppedError("Cannot submit to a stopped queue")
        if not (1 <= task.priority <= 10):
            raise InvalidPriorityError(
                f"Priority must be 1\u201310, got {task.priority}"
            )
        with self._lock:
            self._tasks[task.task_id] = task
            heapq.heappush(
                self._queue,
                (task.priority, task.submitted_at, task.task_id),
            )
            self._has_work.set()
        return task.task_id

    def cancel(self, task_id: str) -> bool:
        """Cancel a task. Returns True if successfully cancelled.

        Only PENDING and RUNNING tasks can be cancelled.
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                raise TaskNotFoundError(f"No task with ID {task_id}")
            if task.status in (TaskStatus.PENDING, TaskStatus.RUNNING):
                task.transition(TaskStatus.CANCELLED)
                return True
            return False

    def get_status(self, task_id: str) -> TaskStatus:
        """Return the current status of *task_id*."""
        task = self._tasks.get(task_id)
        if task is None:
            raise TaskNotFoundError(f"No task with ID {task_id}")
        return task.status

    def get_result(self, task_id: str) -> Optional[TaskResult]:
        """Return the result for *task_id*, or None if not yet finished."""
        if task_id not in self._tasks:
            raise TaskNotFoundError(f"No task with ID {task_id}")
        return self._results.get(task_id)

    def start(self) -> None:
        """Start the background dispatcher and thread pool."""
        if self._running:
            return
        self._running = True
        self._executor = ThreadPoolExecutor(max_workers=self._max_workers)
        self._dispatcher_thread = threading.Thread(
            target=self._dispatch_loop, daemon=True, name="tq-dispatcher",
        )
        self._dispatcher_thread.start()

    def stop(self, wait: bool = True) -> None:
        """Stop the queue processor.

        *wait=True*  — block until running tasks finish.
        *wait=False* — cancel pending tasks and return immediately.
        """
        self._running = False
        self._has_work.set()  # wake dispatcher so it exits

        if not wait:
            with self._lock:
                while self._queue:
                    _, _, task_id = heapq.heappop(self._queue)
                    task = self._tasks[task_id]
                    if task.status == TaskStatus.PENDING:
                        task.transition(TaskStatus.CANCELLED)

        if self._dispatcher_thread is not None:
            self._dispatcher_thread.join(timeout=10)
            self._dispatcher_thread = None

        if self._executor is not None:
            self._executor.shutdown(wait=wait)
            self._executor = None

    @property
    def pending_count(self) -> int:
        """Number of tasks in PENDING status."""
        with self._lock:
            return sum(
                1 for t in self._tasks.values()
                if t.status == TaskStatus.PENDING
            )

    @property
    def active_count(self) -> int:
        """Number of tasks currently executing."""
        with self._lock:
            return self._active_count

    # ------------------------------------------------------------------
    # Internal machinery
    # ------------------------------------------------------------------

    def _dispatch_loop(self) -> None:
        """Pull tasks from the priority queue and submit to the thread pool."""
        while self._running:
            self._has_work.wait(timeout=0.1)
            with self._lock:
                while self._queue and self._active_count < self._max_workers:
                    _, _, task_id = heapq.heappop(self._queue)
                    task = self._tasks[task_id]
                    if task.status not in (TaskStatus.PENDING, TaskStatus.RETRYING):
                        continue
                    task.transition(TaskStatus.RUNNING)
                    task.attempts += 1
                    self._active_count += 1
                    self._executor.submit(self._execute_task, task)  # type: ignore[union-attr]
                if not self._queue:
                    self._has_work.clear()

    def _execute_task(self, task: Task) -> None:
        """Run a single task, handling success, failure, timeout, and retry."""
        start = time.monotonic()
        try:
            # Bail out if cancelled between dispatch and execution
            with self._lock:
                if task.status != TaskStatus.RUNNING:
                    return

            if task.timeout is not None:
                value = self._run_with_timeout(task)
            else:
                value = task.func(*task.args, **task.kwargs)

            duration = time.monotonic() - start

            with self._lock:
                if task.status != TaskStatus.RUNNING:
                    return  # cancelled while running
                task.result = value
                task.transition(TaskStatus.SUCCESS)
                self._results[task.task_id] = TaskResult(
                    task_id=task.task_id,
                    success=True,
                    value=value,
                    duration=duration,
                )

        except TaskTimeoutError:
            duration = time.monotonic() - start
            with self._lock:
                if task.status != TaskStatus.RUNNING:
                    return
                task.error = f"Task timed out after {task.timeout}s"
                task.transition(TaskStatus.TIMED_OUT)
                self._results[task.task_id] = TaskResult(
                    task_id=task.task_id,
                    success=False,
                    error=task.error,
                    duration=duration,
                )

        except Exception as exc:
            duration = time.monotonic() - start
            error_msg = f"{type(exc).__name__}: {exc}"
            should_retry = False
            retry_delay = 0.0

            with self._lock:
                if task.status != TaskStatus.RUNNING:
                    return
                task.error = error_msg

                if task.attempts <= task.max_retries:
                    task.transition(TaskStatus.RETRYING)
                    retry_number = task.attempts - 1
                    retry_delay = _BACKOFF_BASE * (2 ** retry_number)
                    should_retry = True
                else:
                    task.transition(TaskStatus.FAILED)
                    self._results[task.task_id] = TaskResult(
                        task_id=task.task_id,
                        success=False,
                        error=error_msg,
                        duration=duration,
                    )

            if should_retry:
                timer = threading.Timer(
                    retry_delay, self._enqueue_retry, args=(task,),
                )
                timer.daemon = True
                timer.start()

        finally:
            with self._lock:
                self._active_count -= 1

    def _enqueue_retry(self, task: Task) -> None:
        """Re-add a retrying task to the priority queue after backoff."""
        with self._lock:
            if not self._running or task.status != TaskStatus.RETRYING:
                return
            heapq.heappush(
                self._queue,
                (task.priority, task.submitted_at, task.task_id),
            )
            self._has_work.set()

    def _run_with_timeout(self, task: Task) -> object:
        """Execute the task callable, raising TaskTimeoutError if it exceeds *task.timeout*."""
        result_box: list[object] = []
        error_box: list[BaseException] = []

        def _target() -> None:
            try:
                result_box.append(task.func(*task.args, **task.kwargs))
            except BaseException as exc:
                error_box.append(exc)

        worker = threading.Thread(target=_target, daemon=True, name="tq-timeout")
        worker.start()
        worker.join(timeout=task.timeout)

        if worker.is_alive():
            raise TaskTimeoutError(f"Task timed out after {task.timeout}s")

        if error_box:
            raise error_box[0]

        return result_box[0] if result_box else None
