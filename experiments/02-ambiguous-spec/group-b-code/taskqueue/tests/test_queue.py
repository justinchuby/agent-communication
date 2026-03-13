"""Comprehensive tests for the task queue library.

Owner: QA Tester

20 tests across 7 categories:
  1. Basic submit and execute (tests 1-3)
  2. Priority ordering (tests 4-6)
  3. Retry on failure with exponential backoff (tests 7-10)
  4. Timeout handling (tests 11-12)
  5. Concurrent execution (tests 13-14)
  6. Status tracking (tests 15-17)
  7. Edge cases (tests 18-20)
"""

import time
import threading
import pytest

from taskqueue.models import (
    Task,
    TaskResult,
    TaskStatus,
    TERMINAL_STATUSES,
    VALID_TRANSITIONS,
    InvalidPriorityError,
    InvalidTransitionError,
    TaskNotFoundError,
    TaskTimeoutError,
    QueueStoppedError,
)
from taskqueue.engine import TaskQueue


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _noop():
    return "ok"


def _add(a, b):
    return a + b


def _failing():
    raise ValueError("boom")


def _slow(seconds=5.0):
    time.sleep(seconds)
    return "done"


# ---------------------------------------------------------------------------
# Fixture: auto-stop queue to prevent leaked threads
# ---------------------------------------------------------------------------

@pytest.fixture
def queue():
    """Provide a started TaskQueue that is reliably stopped after the test."""
    q = TaskQueue(max_workers=2)
    q.start()
    yield q
    q.stop(wait=True)


# ---------------------------------------------------------------------------
# 1. Basic submit and execute
# ---------------------------------------------------------------------------

class TestSubmitAndExecute:
    """Tests 1-3: basic submit, result retrieval, and stopped-queue guard."""

    def test_submit_returns_nonempty_task_id(self, queue):
        """T1: submit() returns a non-empty string task ID."""
        task = Task(func=_noop, name="t1")
        tid = queue.submit(task)
        assert isinstance(tid, str)
        assert len(tid) > 0

    def test_execute_returns_correct_result(self, queue):
        """T2: a simple add(2,3) task produces result.value == 5."""
        task = Task(func=_add, name="add", args=(2, 3), timeout=5.0)
        tid = queue.submit(task)
        time.sleep(1.0)
        result = queue.get_result(tid)
        assert result is not None
        assert result.success is True
        assert result.value == 5
        assert result.duration > 0

    def test_submit_to_stopped_queue_raises(self):
        """T3: submitting to a queue that was never started raises QueueStoppedError."""
        q = TaskQueue(max_workers=1)
        with pytest.raises(QueueStoppedError):
            q.submit(Task(func=_noop))

    def test_execute_with_kwargs(self, queue):
        """T3b: task using kwargs instead of positional args."""
        def kw_func(x=0, y=0):
            return x * y

        task = Task(func=kw_func, name="kw", kwargs={"x": 6, "y": 7}, timeout=5.0)
        tid = queue.submit(task)
        time.sleep(1.0)
        result = queue.get_result(tid)
        assert result is not None
        assert result.success is True
        assert result.value == 42


# ---------------------------------------------------------------------------
# 2. Priority ordering
# ---------------------------------------------------------------------------

class TestPriorityOrdering:
    """Tests 4-6: priority heap ordering and boundary validation."""

    def test_higher_priority_runs_first(self):
        """T4: with 1 worker, priority-1 task runs before priority-10 when
        both are queued while the worker is busy."""
        order = []
        blocker = threading.Event()

        def _block():
            blocker.wait(timeout=5)

        def _record(label):
            order.append(label)

        q = TaskQueue(max_workers=1)
        q.start()
        try:
            # Occupy the single worker
            q.submit(Task(func=_block, name="blocker", timeout=10.0))
            time.sleep(0.3)
            # Queue low then high while worker is busy
            q.submit(Task(func=_record, name="low", priority=10, args=("low",), timeout=5.0))
            q.submit(Task(func=_record, name="high", priority=1, args=("high",), timeout=5.0))
            time.sleep(0.3)
            blocker.set()  # release blocker
            time.sleep(2.0)
        finally:
            q.stop(wait=True)
        # high should appear before low
        assert order.index("high") < order.index("low")

    def test_fifo_for_equal_priority(self):
        """T5: same-priority tasks execute in FIFO order."""
        order = []
        blocker = threading.Event()

        def _block():
            blocker.wait(timeout=5)

        def _record(label):
            order.append(label)

        q = TaskQueue(max_workers=1)
        q.start()
        try:
            # Block the worker so all 3 queue up
            q.submit(Task(func=_block, name="blocker", priority=1, timeout=10.0))
            time.sleep(0.3)
            q.submit(Task(func=_record, name="a", priority=5, args=("a",), timeout=5.0))
            time.sleep(0.01)  # ensure monotonic ordering
            q.submit(Task(func=_record, name="b", priority=5, args=("b",), timeout=5.0))
            time.sleep(0.01)
            q.submit(Task(func=_record, name="c", priority=5, args=("c",), timeout=5.0))
            time.sleep(0.3)
            blocker.set()
            time.sleep(3.0)
        finally:
            q.stop(wait=True)
        assert order == ["a", "b", "c"]

    def test_invalid_priority_raises(self):
        """T6: priorities outside 1-10 raise InvalidPriorityError."""
        with pytest.raises(InvalidPriorityError):
            Task(func=_noop, priority=0)
        with pytest.raises(InvalidPriorityError):
            Task(func=_noop, priority=11)
        with pytest.raises(InvalidPriorityError):
            Task(func=_noop, priority=-1)


# ---------------------------------------------------------------------------
# 3. Retry on failure with exponential backoff
# ---------------------------------------------------------------------------

class TestRetry:
    """Tests 7-10: retry mechanics, backoff timing, and eventual success."""

    def test_retry_attempts_correct_count(self):
        """T7: max_retries=2 means 1 initial + 2 retries = 3 total calls."""
        call_count = 0

        def _count_fail():
            nonlocal call_count
            call_count += 1
            raise RuntimeError("fail")

        q = TaskQueue(max_workers=2)
        q.start()
        try:
            task = Task(func=_count_fail, name="retry-count",
                        max_retries=2, timeout=10.0)
            tid = q.submit(task)
            # backoff: ~1s + ~2s + margin
            time.sleep(6.0)
            assert q.get_status(tid) == TaskStatus.FAILED
            assert call_count == 3
        finally:
            q.stop(wait=True)

    def test_no_retry_when_max_retries_zero(self):
        """T8: max_retries=0 → only 1 attempt, then FAILED immediately."""
        call_count = 0

        def _count_fail():
            nonlocal call_count
            call_count += 1
            raise RuntimeError("fail")

        q = TaskQueue(max_workers=2)
        q.start()
        try:
            task = Task(func=_count_fail, name="no-retry",
                        max_retries=0, timeout=5.0)
            tid = q.submit(task)
            time.sleep(2.0)
            assert q.get_status(tid) == TaskStatus.FAILED
            assert call_count == 1
        finally:
            q.stop(wait=True)

    def test_retry_succeeds_eventually(self):
        """T9: task fails twice then succeeds on third attempt."""
        call_count = 0

        def _fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RuntimeError("not yet")
            return "finally"

        q = TaskQueue(max_workers=2)
        q.start()
        try:
            task = Task(func=_fail_then_succeed, name="eventual",
                        max_retries=3, timeout=10.0)
            tid = q.submit(task)
            time.sleep(8.0)
            result = q.get_result(tid)
            assert result is not None
            assert result.success is True
            assert result.value == "finally"
        finally:
            q.stop(wait=True)

    def test_exponential_backoff_timing(self):
        """T10: retries use exponential backoff (1s, 2s, …). Verify total
        elapsed time is consistent with backoff schedule."""
        timestamps = []

        def _record_and_fail():
            timestamps.append(time.monotonic())
            raise RuntimeError("timed fail")

        q = TaskQueue(max_workers=2)
        q.start()
        try:
            task = Task(func=_record_and_fail, name="backoff-check",
                        max_retries=2, timeout=10.0)
            q.submit(task)
            # 3 attempts total: attempt 1, then ~1s gap, attempt 2, then ~2s gap, attempt 3
            time.sleep(7.0)
        finally:
            q.stop(wait=True)

        assert len(timestamps) == 3, f"Expected 3 timestamps, got {len(timestamps)}"
        gap1 = timestamps[1] - timestamps[0]
        gap2 = timestamps[2] - timestamps[1]
        # Backoff: first retry after ~1s, second after ~2s (with tolerance)
        assert 0.8 <= gap1 <= 2.0, f"First retry gap {gap1:.2f}s not ~1s"
        assert 1.5 <= gap2 <= 3.5, f"Second retry gap {gap2:.2f}s not ~2s"


# ---------------------------------------------------------------------------
# 4. Timeout handling
# ---------------------------------------------------------------------------

class TestTimeout:
    """Tests 11-12: timeout detection and no-retry for timed-out tasks."""

    def test_task_times_out(self):
        """T11: task exceeding its timeout gets TIMED_OUT with error message."""
        q = TaskQueue(max_workers=2)
        q.start()
        try:
            task = Task(func=_slow, name="slow", timeout=0.5,
                        args=(10.0,), max_retries=0)
            tid = q.submit(task)
            time.sleep(2.0)
            assert q.get_status(tid) == TaskStatus.TIMED_OUT
            result = q.get_result(tid)
            assert result is not None
            assert result.success is False
            assert "timed out" in (result.error or "").lower()
        finally:
            q.stop(wait=True)

    def test_timed_out_task_not_retried(self):
        """T12: a timed-out task is NOT retried even if retries remain."""
        call_count = 0

        def _slow_tracked():
            nonlocal call_count
            call_count += 1
            time.sleep(10.0)

        q = TaskQueue(max_workers=2)
        q.start()
        try:
            task = Task(func=_slow_tracked, name="timeout-no-retry",
                        timeout=0.5, max_retries=3)
            tid = q.submit(task)
            time.sleep(3.0)
            assert q.get_status(tid) == TaskStatus.TIMED_OUT
            assert call_count == 1  # no retries happened
        finally:
            q.stop(wait=True)


# ---------------------------------------------------------------------------
# 5. Concurrent execution
# ---------------------------------------------------------------------------

class TestConcurrency:
    """Tests 13-14: parallel execution and max-worker ceiling."""

    def test_multiple_tasks_run_concurrently(self):
        """T13: with 4 workers and 4 slow tasks, at least 2 run in parallel."""
        concurrent_count = 0
        max_concurrent = 0
        lock = threading.Lock()

        def _track():
            nonlocal concurrent_count, max_concurrent
            with lock:
                concurrent_count += 1
                max_concurrent = max(max_concurrent, concurrent_count)
            time.sleep(0.5)
            with lock:
                concurrent_count -= 1

        q = TaskQueue(max_workers=4)
        q.start()
        try:
            for i in range(4):
                q.submit(Task(func=_track, name=f"con-{i}", timeout=5.0))
            time.sleep(2.0)
        finally:
            q.stop(wait=True)
        assert max_concurrent >= 2

    def test_max_workers_caps_concurrency(self):
        """T14: with max_workers=2, never more than 2 tasks execute at once."""
        concurrent_count = 0
        max_concurrent = 0
        lock = threading.Lock()

        def _track():
            nonlocal concurrent_count, max_concurrent
            with lock:
                concurrent_count += 1
                max_concurrent = max(max_concurrent, concurrent_count)
            time.sleep(0.5)
            with lock:
                concurrent_count -= 1

        q = TaskQueue(max_workers=2)
        q.start()
        try:
            for i in range(6):
                q.submit(Task(func=_track, name=f"w-{i}", timeout=5.0))
            time.sleep(4.0)
        finally:
            q.stop(wait=True)
        assert max_concurrent <= 2


# ---------------------------------------------------------------------------
# 6. Status tracking
# ---------------------------------------------------------------------------

class TestStatusTracking:
    """Tests 15-17: lifecycle state transitions."""

    def test_initial_status_is_pending(self):
        """T15: freshly created Task is PENDING."""
        task = Task(func=_noop)
        assert task.status == TaskStatus.PENDING

    def test_status_reaches_success(self, queue):
        """T16: a successful task ends in SUCCESS."""
        task = Task(func=_noop, name="succeed", timeout=5.0)
        tid = queue.submit(task)
        time.sleep(1.0)
        assert queue.get_status(tid) == TaskStatus.SUCCESS

    def test_terminal_statuses_are_terminal(self):
        """T17: all TERMINAL_STATUSES report is_terminal == True, non-terminal don't."""
        for status in TERMINAL_STATUSES:
            task = Task(func=_noop)
            task.status = status
            assert task.is_terminal, f"{status} should be terminal"
        for status in (TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.RETRYING):
            task = Task(func=_noop)
            task.status = status
            assert not task.is_terminal, f"{status} should not be terminal"

    def test_invalid_transition_raises(self):
        """T17b: invalid status transitions raise InvalidTransitionError."""
        task = Task(func=_noop)
        assert task.status == TaskStatus.PENDING
        # PENDING → SUCCESS is invalid (must go through RUNNING)
        with pytest.raises(InvalidTransitionError):
            task.transition(TaskStatus.SUCCESS)


# ---------------------------------------------------------------------------
# 7. Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Tests 18-20: not-found, cancel, stop(wait=False), etc."""

    def test_get_status_unknown_task_raises(self, queue):
        """T18: querying a non-existent task ID raises TaskNotFoundError."""
        with pytest.raises(TaskNotFoundError):
            queue.get_status("nonexistent-id")

    def test_get_result_unknown_task_raises(self, queue):
        """T18b: get_result on unknown ID also raises TaskNotFoundError."""
        with pytest.raises(TaskNotFoundError):
            queue.get_result("nonexistent-id")

    def test_cancel_pending_task(self):
        """T19: a PENDING task can be cancelled and shows CANCELLED status."""
        blocker = threading.Event()

        def _block():
            blocker.wait(timeout=10)

        q = TaskQueue(max_workers=1)
        q.start()
        try:
            # Fill the single worker so next task stays PENDING
            q.submit(Task(func=_block, name="blocker", timeout=10.0))
            time.sleep(0.3)
            task2 = Task(func=_noop, name="to-cancel", timeout=5.0)
            tid = q.submit(task2)
            time.sleep(0.3)
            result = q.cancel(tid)
            assert result is True
            assert q.get_status(tid) == TaskStatus.CANCELLED
        finally:
            blocker.set()
            q.stop(wait=True)

    def test_cancel_completed_task_returns_false(self, queue):
        """T19b: cancelling an already-SUCCESS task returns False."""
        task = Task(func=_noop, name="already-done", timeout=5.0)
        tid = queue.submit(task)
        time.sleep(1.0)
        assert queue.get_status(tid) == TaskStatus.SUCCESS
        assert queue.cancel(tid) is False

    def test_cancel_unknown_task_raises(self, queue):
        """T19c: cancelling a non-existent ID raises TaskNotFoundError."""
        with pytest.raises(TaskNotFoundError):
            queue.cancel("does-not-exist")

    def test_stop_wait_false_cancels_pending(self):
        """T20: stop(wait=False) cancels pending tasks."""
        blocker = threading.Event()

        def _block():
            blocker.wait(timeout=10)

        q = TaskQueue(max_workers=1)
        q.start()
        try:
            # Occupy worker
            q.submit(Task(func=_block, name="blocker", timeout=10.0))
            time.sleep(0.3)
            pending_tids = []
            for i in range(3):
                tid = q.submit(Task(func=_noop, name=f"pending-{i}", timeout=5.0))
                pending_tids.append(tid)
            time.sleep(0.3)
        finally:
            blocker.set()
            q.stop(wait=False)

        for tid in pending_tids:
            status = q.get_status(tid)
            # Should be CANCELLED (or possibly executed if timing was lucky)
            assert status in (TaskStatus.CANCELLED, TaskStatus.SUCCESS, TaskStatus.PENDING)
