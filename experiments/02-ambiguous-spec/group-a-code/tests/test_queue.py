"""Tests for the task queue library.

Owner: Tester

18 tests covering:
- Basic submit and execute (3)
- Priority ordering (2)
- Retry on failure (3)
- Timeout handling (2)
- Concurrent execution (2)
- Status tracking (2)
- Edge cases and error handling (4)
"""

import threading
import time

import pytest

from taskqueue import (
    TaskQueue,
    TaskStatus,
    TaskResult,
    Task,
    TERMINAL_STATUSES,
    PRIORITY_DEFAULT,
    TaskNotFoundError,
    InvalidPriorityError,
    TaskQueueError,
)


# ─── Helpers ───────────────────────────────────────────────────────

def _wait_for_status(tq: TaskQueue, task_id: str, statuses: set[TaskStatus], timeout: float = 5.0) -> TaskStatus:
    """Poll until the task reaches one of the given statuses or timeout."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status = tq.get_status(task_id)
        if status in statuses:
            return status
        time.sleep(0.05)
    return tq.get_status(task_id)


# ─── Basic Submit and Execute ──────────────────────────────────────

class TestBasicSubmitExecute:
    def test_submit_returns_task_id(self):
        """submit() returns a non-empty string task ID."""
        tq = TaskQueue()
        task_id = tq.submit(lambda: 42, name="simple")
        assert isinstance(task_id, str)
        assert len(task_id) > 0

    def test_simple_task_succeeds(self):
        """A simple task executes and produces SUCCESS with correct result."""
        with TaskQueue(max_workers=1) as tq:
            task_id = tq.submit(lambda: 42, name="answer")
            status = _wait_for_status(tq, task_id, TERMINAL_STATUSES)
            assert status == TaskStatus.SUCCESS
            result = tq.get_result(task_id)
            assert result.success is True
            assert result.result == 42
            assert result.error is None
            assert result.attempts == 1
            assert result.duration > 0

    def test_task_with_args_and_kwargs(self):
        """Tasks correctly receive positional and keyword arguments."""
        def add(a, b, extra=0):
            return a + b + extra

        with TaskQueue(max_workers=1) as tq:
            task_id = tq.submit(add, args=(3, 4), kwargs={"extra": 10})
            _wait_for_status(tq, task_id, TERMINAL_STATUSES)
            result = tq.get_result(task_id)
            assert result.success is True
            assert result.result == 17


# ─── Priority Ordering ─────────────────────────────────────────────

class TestPriorityOrdering:
    def test_higher_priority_runs_first(self):
        """Priority 1 (highest) tasks run before priority 10 (lowest)."""
        execution_order = []

        def track(label):
            execution_order.append(label)

        tq = TaskQueue(max_workers=1)
        # Submit tasks before starting — they queue up by priority
        tq.submit(track, args=("low",), priority=10, name="low")
        tq.submit(track, args=("high",), priority=1, name="high")
        tq.submit(track, args=("mid",), priority=5, name="mid")
        tq.start()
        time.sleep(1.0)
        tq.stop(wait=True)

        assert execution_order[0] == "high"
        assert execution_order[1] == "mid"
        assert execution_order[2] == "low"

    def test_same_priority_fifo(self):
        """Tasks with the same priority run in FIFO (submission) order."""
        execution_order = []

        def track(label):
            execution_order.append(label)

        tq = TaskQueue(max_workers=1)
        tq.submit(track, args=("first",), priority=5, name="first")
        tq.submit(track, args=("second",), priority=5, name="second")
        tq.submit(track, args=("third",), priority=5, name="third")
        tq.start()
        time.sleep(1.0)
        tq.stop(wait=True)

        assert execution_order == ["first", "second", "third"]


# ─── Retry on Failure ──────────────────────────────────────────────

class TestRetryOnFailure:
    def test_retry_then_succeed(self):
        """A task that fails once then succeeds uses retry correctly."""
        call_count = 0

        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RuntimeError("transient failure")
            return "recovered"

        with TaskQueue(max_workers=1, default_timeout=5.0) as tq:
            task_id = tq.submit(flaky, max_retries=3, name="flaky")
            status = _wait_for_status(tq, task_id, TERMINAL_STATUSES, timeout=15.0)
            assert status == TaskStatus.SUCCESS
            result = tq.get_result(task_id)
            assert result.success is True
            assert result.result == "recovered"
            assert result.attempts == 2

    def test_exhausts_retries_then_fails(self):
        """A task that always fails exhausts retries and ends FAILED."""
        def always_fail():
            raise ValueError("permanent error")

        with TaskQueue(max_workers=1, default_timeout=5.0, default_max_retries=2) as tq:
            task_id = tq.submit(always_fail, max_retries=2, name="doomed")
            status = _wait_for_status(tq, task_id, TERMINAL_STATUSES, timeout=30.0)
            assert status == TaskStatus.FAILED
            result = tq.get_result(task_id)
            assert result.success is False
            assert "ValueError" in result.error
            assert result.attempts == 3  # 1 initial + 2 retries

    def test_zero_retries_fails_immediately(self):
        """With max_retries=0, a failing task goes directly to FAILED."""
        def fail():
            raise RuntimeError("oops")

        with TaskQueue(max_workers=1, default_timeout=5.0) as tq:
            task_id = tq.submit(fail, max_retries=0, name="no-retry")
            status = _wait_for_status(tq, task_id, TERMINAL_STATUSES, timeout=5.0)
            assert status == TaskStatus.FAILED
            result = tq.get_result(task_id)
            assert result.attempts == 1


# ─── Timeout Handling ──────────────────────────────────────────────

class TestTimeoutHandling:
    def test_task_times_out(self):
        """A task exceeding its timeout is treated as a failure."""
        def slow():
            time.sleep(10)

        with TaskQueue(max_workers=1) as tq:
            task_id = tq.submit(slow, timeout=0.5, max_retries=0, name="slow")
            status = _wait_for_status(tq, task_id, TERMINAL_STATUSES, timeout=5.0)
            assert status == TaskStatus.FAILED
            result = tq.get_result(task_id)
            assert result.success is False
            assert "timed out" in result.error.lower()

    def test_timeout_with_retries(self):
        """A timed-out task is retried if retries remain."""
        call_count = 0

        def slow_then_fast():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                time.sleep(10)  # will timeout
            return "done"

        with TaskQueue(max_workers=1) as tq:
            task_id = tq.submit(slow_then_fast, timeout=0.5, max_retries=2, name="timeout-retry")
            status = _wait_for_status(tq, task_id, TERMINAL_STATUSES, timeout=15.0)
            assert status == TaskStatus.SUCCESS
            result = tq.get_result(task_id)
            assert result.success is True
            assert result.result == "done"
            assert result.attempts >= 2


# ─── Concurrent Execution ──────────────────────────────────────────

class TestConcurrentExecution:
    def test_multiple_tasks_run_concurrently(self):
        """With multiple workers, tasks run in parallel."""
        started = threading.Event()
        barrier = threading.Barrier(2, timeout=5.0)

        def concurrent_task():
            barrier.wait()
            return "done"

        with TaskQueue(max_workers=2) as tq:
            id1 = tq.submit(concurrent_task, name="c1")
            id2 = tq.submit(concurrent_task, name="c2")
            s1 = _wait_for_status(tq, id1, TERMINAL_STATUSES, timeout=10.0)
            s2 = _wait_for_status(tq, id2, TERMINAL_STATUSES, timeout=10.0)
            assert s1 == TaskStatus.SUCCESS
            assert s2 == TaskStatus.SUCCESS

    def test_context_manager_lifecycle(self):
        """Context manager starts on enter and stops on exit."""
        with TaskQueue(max_workers=1) as tq:
            task_id = tq.submit(lambda: "ctx", name="ctx-test")
            _wait_for_status(tq, task_id, TERMINAL_STATUSES)
            result = tq.get_result(task_id)
            assert result.success is True
            assert result.result == "ctx"


# ─── Status Tracking ──────────────────────────────────────────────

class TestStatusTracking:
    def test_initial_status_is_pending(self):
        """A submitted task starts in PENDING status."""
        tq = TaskQueue()
        task_id = tq.submit(lambda: None, name="pending-check")
        assert tq.get_status(task_id) == TaskStatus.PENDING

    def test_get_result_on_pending_task(self):
        """get_result() on a pending task returns informational error."""
        tq = TaskQueue()
        task_id = tq.submit(lambda: None, name="pending-result")
        result = tq.get_result(task_id)
        assert result.success is False
        assert result.error == "Task is pending"
        assert result.duration == 0.0


# ─── Edge Cases and Error Handling ─────────────────────────────────

class TestEdgeCases:
    def test_invalid_priority_too_low(self):
        """Priority below 1 raises InvalidPriorityError."""
        tq = TaskQueue()
        with pytest.raises(InvalidPriorityError):
            tq.submit(lambda: None, priority=0)

    def test_invalid_priority_too_high(self):
        """Priority above 10 raises InvalidPriorityError."""
        tq = TaskQueue()
        with pytest.raises(InvalidPriorityError):
            tq.submit(lambda: None, priority=11)

    def test_get_status_unknown_id(self):
        """get_status() with unknown ID raises TaskNotFoundError."""
        tq = TaskQueue()
        with pytest.raises(TaskNotFoundError):
            tq.get_status("nonexistent-id")

    def test_cancel_pending_task(self):
        """Cancelling a pending task returns True and sets CANCELLED status."""
        tq = TaskQueue()
        task_id = tq.submit(lambda: None, name="to-cancel")
        assert tq.cancel(task_id) is True
        assert tq.get_status(task_id) == TaskStatus.CANCELLED
        result = tq.get_result(task_id)
        assert result.success is False
        assert result.error == "Task was cancelled"

    def test_cancel_terminal_task_returns_false(self):
        """Cancelling an already-completed task returns False."""
        with TaskQueue(max_workers=1) as tq:
            task_id = tq.submit(lambda: "done", name="already-done")
            _wait_for_status(tq, task_id, TERMINAL_STATUSES)
            assert tq.cancel(task_id) is False

    def test_submit_non_callable_raises_type_error(self):
        """Submitting a non-callable raises TypeError."""
        tq = TaskQueue()
        with pytest.raises(TypeError):
            tq.submit("not a function")  # type: ignore

    def test_constructor_validation(self):
        """Invalid constructor args raise ValueError."""
        with pytest.raises(ValueError):
            TaskQueue(max_workers=0)
        with pytest.raises(ValueError):
            TaskQueue(default_timeout=-1)
        with pytest.raises(ValueError):
            TaskQueue(default_max_retries=-1)
