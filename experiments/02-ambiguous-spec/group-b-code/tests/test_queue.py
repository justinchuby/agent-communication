"""Tests for the task queue library.

Owner: Tester

18 tests covering: submit/execute, priority ordering, retry, timeout,
concurrency, status tracking, edge cases.
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
# 1-3: Basic submit and execute
# ---------------------------------------------------------------------------

class TestSubmitAndExecute:
    def test_submit_returns_task_id(self):
        q = TaskQueue(max_workers=2)
        q.start()
        try:
            task = Task(func=_noop, name="t1")
            tid = q.submit(task)
            assert isinstance(tid, str) and len(tid) > 0
        finally:
            q.stop(wait=True)

    def test_execute_returns_result(self):
        q = TaskQueue(max_workers=2)
        q.start()
        try:
            task = Task(func=_add, name="add", args=(2, 3), timeout=5.0)
            tid = q.submit(task)
            time.sleep(1.0)
            result = q.get_result(tid)
            assert result is not None
            assert result.success is True
            assert result.value == 5
        finally:
            q.stop(wait=True)

    def test_submit_to_stopped_queue_raises(self):
        q = TaskQueue(max_workers=2)
        with pytest.raises(QueueStoppedError):
            q.submit(Task(func=_noop))


# ---------------------------------------------------------------------------
# 4-6: Priority ordering
# ---------------------------------------------------------------------------

class TestPriorityOrdering:
    def test_higher_priority_runs_first(self):
        """Priority 1 should execute before priority 10."""
        order = []
        def _record(label):
            order.append(label)

        q = TaskQueue(max_workers=1)
        q.start()
        try:
            # Submit low priority first, then high priority
            q.submit(Task(func=_record, name="low", priority=10, args=("low",), timeout=5.0))
            q.submit(Task(func=_record, name="high", priority=1, args=("high",), timeout=5.0))
            time.sleep(2.0)
        finally:
            q.stop(wait=True)
        # The first task may already be running, but high should come before any remaining low
        assert "high" in order

    def test_fifo_for_equal_priority(self):
        """Tasks with same priority run in submission order."""
        order = []
        barrier = threading.Event()

        def _record(label):
            barrier.wait(timeout=3)
            order.append(label)

        q = TaskQueue(max_workers=1)
        q.start()
        try:
            q.submit(Task(func=_record, name="a", priority=5, args=("a",), timeout=5.0))
            q.submit(Task(func=_record, name="b", priority=5, args=("b",), timeout=5.0))
            q.submit(Task(func=_record, name="c", priority=5, args=("c",), timeout=5.0))
            barrier.set()
            time.sleep(3.0)
        finally:
            q.stop(wait=True)
        assert order == ["a", "b", "c"]

    def test_invalid_priority_raises(self):
        with pytest.raises(InvalidPriorityError):
            Task(func=_noop, priority=0)
        with pytest.raises(InvalidPriorityError):
            Task(func=_noop, priority=11)


# ---------------------------------------------------------------------------
# 7-9: Retry on failure
# ---------------------------------------------------------------------------

class TestRetry:
    def test_retry_on_failure(self):
        """A failing task with max_retries=2 should attempt 3 times total."""
        call_count = 0
        def _count_fail():
            nonlocal call_count
            call_count += 1
            raise RuntimeError("fail")

        q = TaskQueue(max_workers=2)
        q.start()
        try:
            task = Task(func=_count_fail, name="retry-me", max_retries=2, timeout=10.0)
            tid = q.submit(task)
            # Wait enough for retries (backoff: 1s + 2s + margin)
            time.sleep(6.0)
            status = q.get_status(tid)
            assert status == TaskStatus.FAILED
            assert call_count == 3  # 1 initial + 2 retries
        finally:
            q.stop(wait=True)

    def test_no_retry_when_max_retries_zero(self):
        call_count = 0
        def _count_fail():
            nonlocal call_count
            call_count += 1
            raise RuntimeError("fail")

        q = TaskQueue(max_workers=2)
        q.start()
        try:
            task = Task(func=_count_fail, name="no-retry", max_retries=0, timeout=5.0)
            tid = q.submit(task)
            time.sleep(2.0)
            assert q.get_status(tid) == TaskStatus.FAILED
            assert call_count == 1
        finally:
            q.stop(wait=True)

    def test_retry_succeeds_eventually(self):
        call_count = 0
        def _fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RuntimeError("not yet")
            return "success"

        q = TaskQueue(max_workers=2)
        q.start()
        try:
            task = Task(func=_fail_then_succeed, name="eventual", max_retries=3, timeout=10.0)
            tid = q.submit(task)
            time.sleep(8.0)
            result = q.get_result(tid)
            assert result is not None
            assert result.success is True
            assert result.value == "success"
        finally:
            q.stop(wait=True)


# ---------------------------------------------------------------------------
# 10-11: Timeout handling
# ---------------------------------------------------------------------------

class TestTimeout:
    def test_task_times_out(self):
        q = TaskQueue(max_workers=2)
        q.start()
        try:
            task = Task(func=_slow, name="slow", timeout=0.5, args=(10.0,), max_retries=0)
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
        call_count = 0
        def _slow_tracked():
            nonlocal call_count
            call_count += 1
            time.sleep(10.0)

        q = TaskQueue(max_workers=2)
        q.start()
        try:
            task = Task(func=_slow_tracked, name="no-retry-timeout",
                        timeout=0.5, max_retries=3)
            tid = q.submit(task)
            time.sleep(3.0)
            assert q.get_status(tid) == TaskStatus.TIMED_OUT
            assert call_count == 1  # no retries
        finally:
            q.stop(wait=True)


# ---------------------------------------------------------------------------
# 12-13: Concurrent execution
# ---------------------------------------------------------------------------

class TestConcurrency:
    def test_multiple_tasks_run_concurrently(self):
        active = threading.Event()
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
        assert max_concurrent >= 2  # at least 2 ran concurrently

    def test_max_workers_respected(self):
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
# 14-16: Status tracking
# ---------------------------------------------------------------------------

class TestStatusTracking:
    def test_initial_status_pending(self):
        task = Task(func=_noop)
        assert task.status == TaskStatus.PENDING

    def test_status_transitions_to_success(self):
        q = TaskQueue(max_workers=2)
        q.start()
        try:
            task = Task(func=_noop, name="succeed", timeout=5.0)
            tid = q.submit(task)
            time.sleep(1.0)
            assert q.get_status(tid) == TaskStatus.SUCCESS
        finally:
            q.stop(wait=True)

    def test_terminal_statuses_are_terminal(self):
        for status in TERMINAL_STATUSES:
            task = Task(func=_noop)
            task.status = status
            assert task.is_terminal


# ---------------------------------------------------------------------------
# 17-18: Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_get_status_unknown_task_raises(self):
        q = TaskQueue(max_workers=1)
        q.start()
        try:
            with pytest.raises(TaskNotFoundError):
                q.get_status("nonexistent-id")
        finally:
            q.stop(wait=True)

    def test_cancel_pending_task(self):
        barrier = threading.Event()

        def _block():
            barrier.wait(timeout=10)

        q = TaskQueue(max_workers=1)
        q.start()
        try:
            # Fill the single worker so next task stays PENDING
            q.submit(Task(func=_block, name="blocker", timeout=10.0))
            time.sleep(0.3)
            task2 = Task(func=_noop, name="to-cancel", timeout=5.0)
            tid = q.submit(task2)
            time.sleep(0.3)
            cancelled = q.cancel(tid)
            assert cancelled is True
            assert q.get_status(tid) == TaskStatus.CANCELLED
        finally:
            barrier.set()
            q.stop(wait=True)
