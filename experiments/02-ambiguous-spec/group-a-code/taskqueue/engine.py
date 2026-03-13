"""Task queue processing engine.

Owner: Developer B

Core queue engine with priority scheduling, retry with exponential backoff,
per-task timeouts, and concurrent execution via ThreadPoolExecutor.
"""

from __future__ import annotations

import logging
import queue
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from typing import Any, Callable, Optional

from taskqueue.models import (
    PRIORITY_DEFAULT,
    InvalidPriorityError,
    Task,
    TaskAlreadyExistsError,
    TaskNotFoundError,
    TaskResult,
    TaskStatus,
    TaskTimeoutError,
)

logger = logging.getLogger(__name__)


class TaskQueue:
    """Priority-based task queue with retry, timeout, and concurrency support.

    Usage::

        with TaskQueue(max_workers=4) as tq:
            task_id = tq.submit(my_func, priority=1, timeout=10.0)
            # ... later ...
            result = tq.get_result(task_id)
    """

    def __init__(
        self,
        max_workers: int = 4,
        default_timeout: float = 30.0,
        default_max_retries: int = 3,
    ) -> None:
        if max_workers < 1:
            raise ValueError(f"max_workers must be >= 1, got {max_workers}")
        if default_timeout <= 0:
            raise ValueError(f"default_timeout must be > 0, got {default_timeout}")
        if default_max_retries < 0:
            raise ValueError(f"default_max_retries must be >= 0, got {default_max_retries}")

        self._max_workers = max_workers
        self._default_timeout = default_timeout
        self._default_max_retries = default_max_retries

        # Thread-safe priority queue. Items are (priority, created_at, task)
        # to break ties by insertion order.
        self._queue: queue.PriorityQueue[Any] = queue.PriorityQueue()

        # All submitted tasks keyed by ID
        self._tasks: dict[str, Task] = {}
        self._lock = threading.Lock()

        # Execution machinery
        self._executor: Optional[ThreadPoolExecutor] = None
        self._dispatcher_thread: Optional[threading.Thread] = None
        self._shutdown_event = threading.Event()
        self._running = False

        # Track in-flight futures so we can cancel on stop
        self._futures: dict[str, Future] = {}

    # ─── Public API ────────────────────────────────────────────────

    def submit(
        self,
        fn: Callable[..., Any],
        *,
        name: str = "",
        priority: int = PRIORITY_DEFAULT,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        args: tuple = (),
        kwargs: Optional[dict] = None,
    ) -> str:
        """Submit a task to the queue. Returns the task ID.

        Raises:
            InvalidPriorityError: If priority is outside 1–10.
            TypeError: If fn is not callable.
        """
        task = Task(
            fn=fn,
            name=name,
            args=args,
            kwargs=kwargs if kwargs is not None else {},
            priority=priority,
            max_retries=max_retries if max_retries is not None else self._default_max_retries,
            timeout=timeout if timeout is not None else self._default_timeout,
        )

        with self._lock:
            if task.id in self._tasks:
                raise TaskAlreadyExistsError(f"Task with ID {task.id} already exists")
            self._tasks[task.id] = task

        self._enqueue(task)
        logger.debug("Submitted task %s (name=%r, priority=%d)", task.id, task.name, task.priority)
        return task.id

    def get_status(self, task_id: str) -> TaskStatus:
        """Get the current status of a task.

        Raises:
            TaskNotFoundError: If the task ID is not found.
        """
        return self._get_task(task_id).status

    def get_result(self, task_id: str) -> TaskResult:
        """Get the result of a task.

        Returns a TaskResult regardless of task state. For tasks that are
        still pending or running, success=False with an informational error.

        Raises:
            TaskNotFoundError: If the task ID is not found.
        """
        task = self._get_task(task_id)
        with self._lock:
            if task.is_terminal:
                return task.to_result()
            # Non-terminal: provide informational error messages
            _status_messages = {
                TaskStatus.PENDING: "Task is pending",
                TaskStatus.RUNNING: "Task is still running",
                TaskStatus.RETRYING: "Task is retrying",
            }
            return TaskResult(
                task_id=task.id,
                success=False,
                error=_status_messages.get(task.status, f"Task is {task.status.value}"),
                duration=0.0,
                attempts=task.attempts,
            )

    def cancel(self, task_id: str) -> bool:
        """Cancel a task.

        Returns True if the task was cancelled, False if it was already in a
        terminal state. Running tasks will have their futures cancelled.

        Raises:
            TaskNotFoundError: If the task ID is not found.
        """
        task = self._get_task(task_id)
        with self._lock:
            if task.is_terminal:
                return False
            task.transition_to(TaskStatus.CANCELLED)
            task.completed_at = time.monotonic()
            future = self._futures.pop(task.id, None)
            if future is not None:
                future.cancel()
        logger.debug("Cancelled task %s", task.id)
        return True

    def start(self) -> None:
        """Start the queue processor (dispatcher thread + worker pool)."""
        if self._running:
            return
        self._shutdown_event.clear()
        self._executor = ThreadPoolExecutor(max_workers=self._max_workers)
        self._dispatcher_thread = threading.Thread(
            target=self._dispatcher_loop, daemon=True, name="taskqueue-dispatcher",
        )
        self._running = True
        self._dispatcher_thread.start()
        logger.debug("TaskQueue started with %d workers", self._max_workers)

    def stop(self, wait: bool = True) -> None:
        """Stop the queue processor.

        Args:
            wait: If True, finish currently running tasks before stopping.
                  If False, cancel all pending tasks immediately.
        """
        if not self._running:
            return
        self._running = False
        self._shutdown_event.set()

        if not wait:
            self._cancel_pending_tasks()

        if self._dispatcher_thread is not None:
            self._dispatcher_thread.join(timeout=10.0)
            self._dispatcher_thread = None

        if self._executor is not None:
            self._executor.shutdown(wait=wait)
            self._executor = None

        logger.debug("TaskQueue stopped (wait=%s)", wait)

    def __enter__(self) -> TaskQueue:
        self.start()
        return self

    def __exit__(self, *exc: Any) -> None:
        self.stop(wait=True)

    # ─── Internal: Dispatcher ──────────────────────────────────────

    def _dispatcher_loop(self) -> None:
        """Main dispatcher loop — pulls tasks from the PQ and submits to the executor."""
        while not self._shutdown_event.is_set():
            try:
                item = self._queue.get(timeout=0.1)
            except queue.Empty:
                continue

            task = item
            with self._lock:
                # Skip tasks that have been cancelled while waiting
                if task.status == TaskStatus.CANCELLED:
                    continue

            if self._executor is None:
                break

            future = self._executor.submit(self._execute_task, task)
            with self._lock:
                self._futures[task.id] = future

    # ─── Internal: Execution ───────────────────────────────────────

    def _execute_task(self, task: Task) -> None:
        """Execute a single task with timeout and retry handling."""
        with self._lock:
            if task.status == TaskStatus.CANCELLED:
                return
            task.transition_to(TaskStatus.RUNNING)
            task.attempts += 1
            if task.started_at is None:
                task.started_at = time.monotonic()

        try:
            result = self._run_with_timeout(task)
            with self._lock:
                if task.status == TaskStatus.CANCELLED:
                    return
                task.transition_to(TaskStatus.SUCCESS)
                task.result = result
                task.error = None
                task.completed_at = time.monotonic()
                self._futures.pop(task.id, None)
            logger.debug("Task %s succeeded on attempt %d", task.id, task.attempts)

        except FutureTimeoutError:
            error_msg = f"Task timed out after {task.timeout}s"
            logger.debug("Task %s timed out on attempt %d", task.id, task.attempts)
            self._handle_failure(task, error_msg)

        except Exception as exc:
            error_msg = f"{type(exc).__name__}: {exc}"
            logger.debug("Task %s failed on attempt %d: %s", task.id, task.attempts, error_msg)
            self._handle_failure(task, error_msg)

    def _run_with_timeout(self, task: Task) -> Any:
        """Run the task callable with a timeout.

        We use a separate single-thread executor so we can enforce the
        timeout via future.result(timeout=...). The task's own thread in
        the pool stays blocked waiting, which is acceptable for the
        threading model.
        """
        # Run the callable in a thread and wait with timeout
        inner_future: Future = Future()

        def _worker() -> None:
            try:
                value = task.fn(*task.args, **task.kwargs)
                inner_future.set_result(value)
            except Exception as exc:
                inner_future.set_exception(exc)

        worker_thread = threading.Thread(target=_worker, daemon=True)
        worker_thread.start()
        try:
            return inner_future.result(timeout=task.timeout)
        except TimeoutError:
            raise FutureTimeoutError(f"Task timed out after {task.timeout}s")

    def _handle_failure(self, task: Task, error_msg: str) -> None:
        """Handle a task failure: retry with backoff or mark as failed."""
        with self._lock:
            if task.status == TaskStatus.CANCELLED:
                return
            self._futures.pop(task.id, None)

            if task.retries_remaining > 0:
                task.transition_to(TaskStatus.RETRYING)
                task.error = error_msg
                backoff_delay = 1.0 * (2 ** (task.attempts - 1))
                logger.debug(
                    "Task %s retrying in %.1fs (attempt %d/%d)",
                    task.id, backoff_delay, task.attempts, task.max_retries + 1,
                )
            else:
                task.transition_to(TaskStatus.FAILED)
                task.error = error_msg
                task.completed_at = time.monotonic()
                logger.debug("Task %s failed permanently after %d attempts", task.id, task.attempts)
                return

        # Schedule retry after backoff (outside the lock)
        timer = threading.Timer(backoff_delay, self._retry_task, args=[task])
        timer.daemon = True
        timer.start()

    def _retry_task(self, task: Task) -> None:
        """Re-enqueue a task for retry after backoff."""
        with self._lock:
            if task.status == TaskStatus.CANCELLED or self._shutdown_event.is_set():
                return
        self._enqueue(task)

    # ─── Internal: Helpers ─────────────────────────────────────────

    def _enqueue(self, task: Task) -> None:
        """Put a task on the priority queue."""
        self._queue.put(task)

    def _get_task(self, task_id: str) -> Task:
        """Look up a task by ID, raising TaskNotFoundError if missing."""
        with self._lock:
            try:
                return self._tasks[task_id]
            except KeyError:
                raise TaskNotFoundError(f"No task with ID {task_id!r}") from None

    def _cancel_pending_tasks(self) -> None:
        """Cancel all tasks that haven't started running yet."""
        with self._lock:
            for task in self._tasks.values():
                if not task.is_terminal and task.status != TaskStatus.RUNNING:
                    task.transition_to(TaskStatus.CANCELLED)
                    task.completed_at = time.monotonic()
