"""Tests for the event emitter library.

Owner: Tester

18 tests covering: on/emit basics, priority ordering, once listeners,
off/cancel, wildcard, error handling, max listeners, listener count, edge cases.
"""

import warnings
import pytest

from eventemitter.types import (
    Listener,
    Subscription,
    MaxListenersExceededWarning,
)
from eventemitter.emitter import EventEmitter


# ---------------------------------------------------------------------------
# 1-3: Basic on/emit
# ---------------------------------------------------------------------------

class TestBasicOnEmit:
    def test_on_and_emit_calls_listener(self):
        ee = EventEmitter()
        results = []
        ee.on("click", lambda: results.append("clicked"))
        count = ee.emit("click")
        assert results == ["clicked"]
        assert count == 1

    def test_emit_passes_args_and_kwargs(self):
        ee = EventEmitter()
        received = {}
        def handler(x, y, flag=False):
            received.update(x=x, y=y, flag=flag)
        ee.on("data", handler)
        ee.emit("data", 1, 2, flag=True)
        assert received == {"x": 1, "y": 2, "flag": True}

    def test_emit_no_listeners_returns_zero(self):
        ee = EventEmitter()
        assert ee.emit("nothing") == 0


# ---------------------------------------------------------------------------
# 4-6: Priority ordering
# ---------------------------------------------------------------------------

class TestPriorityOrdering:
    def test_higher_priority_called_first(self):
        ee = EventEmitter()
        order = []
        ee.on("e", lambda: order.append("low"), priority=10)
        ee.on("e", lambda: order.append("high"), priority=1)
        ee.emit("e")
        assert order == ["high", "low"]

    def test_fifo_within_same_priority(self):
        ee = EventEmitter()
        order = []
        ee.on("e", lambda: order.append("a"), priority=5)
        ee.on("e", lambda: order.append("b"), priority=5)
        ee.on("e", lambda: order.append("c"), priority=5)
        ee.emit("e")
        assert order == ["a", "b", "c"]

    def test_invalid_priority_raises(self):
        ee = EventEmitter()
        with pytest.raises(ValueError):
            ee.on("e", lambda: None, priority=0)
        with pytest.raises(ValueError):
            ee.on("e", lambda: None, priority=11)


# ---------------------------------------------------------------------------
# 7-8: Once listeners
# ---------------------------------------------------------------------------

class TestOnce:
    def test_once_fires_once(self):
        ee = EventEmitter()
        count = 0
        def handler():
            nonlocal count
            count += 1
        ee.once("e", handler)
        ee.emit("e")
        ee.emit("e")
        assert count == 1

    def test_once_removed_after_emit(self):
        ee = EventEmitter()
        ee.once("e", lambda: None)
        assert ee.listener_count("e") == 1
        ee.emit("e")
        assert ee.listener_count("e") == 0


# ---------------------------------------------------------------------------
# 9-10: Off / cancel
# ---------------------------------------------------------------------------

class TestOffCancel:
    def test_off_removes_listener(self):
        ee = EventEmitter()
        fn = lambda: None
        ee.on("e", fn)
        assert ee.off("e", fn) is True
        assert ee.listener_count("e") == 0

    def test_subscription_cancel(self):
        ee = EventEmitter()
        sub = ee.on("e", lambda: None)
        assert isinstance(sub, Subscription)
        sub.cancel()
        assert ee.listener_count("e") == 0


# ---------------------------------------------------------------------------
# 11-12: Wildcard
# ---------------------------------------------------------------------------

class TestWildcard:
    def test_wildcard_catches_all_events(self):
        ee = EventEmitter()
        caught = []
        ee.on("*", lambda: caught.append("wild"))
        ee.emit("click")
        ee.emit("hover")
        assert caught == ["wild", "wild"]

    def test_wildcard_runs_after_specific(self):
        ee = EventEmitter()
        order = []
        ee.on("*", lambda: order.append("wildcard"))
        ee.on("click", lambda: order.append("specific"))
        ee.emit("click")
        assert order == ["specific", "wildcard"]


# ---------------------------------------------------------------------------
# 13-14: Error handling
# ---------------------------------------------------------------------------

class TestErrorHandling:
    def test_no_handler_exception_propagates(self):
        ee = EventEmitter()
        ee.on("e", lambda: 1 / 0)
        with pytest.raises(ZeroDivisionError):
            ee.emit("e")

    def test_error_handler_catches_and_continues(self):
        ee = EventEmitter()
        errors = []
        ee.error_handler = lambda event, exc: errors.append(str(exc))
        results = []
        ee.on("e", lambda: 1 / 0, priority=1)
        ee.on("e", lambda: results.append("ok"), priority=2)
        count = ee.emit("e")
        assert count == 2
        assert len(errors) == 1
        assert results == ["ok"]


# ---------------------------------------------------------------------------
# 15-16: Max listeners warning
# ---------------------------------------------------------------------------

class TestMaxListeners:
    def test_exceeding_max_listeners_warns(self):
        ee = EventEmitter(max_listeners=2)
        ee.on("e", lambda: None)
        ee.on("e", lambda: None)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            ee.on("e", lambda: None)  # 3rd listener
            assert len(w) == 1
            assert issubclass(w[0].category, MaxListenersExceededWarning)

    def test_unlimited_listeners_no_warning(self):
        ee = EventEmitter(max_listeners=0)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            for _ in range(50):
                ee.on("e", lambda: None)
            assert len(w) == 0


# ---------------------------------------------------------------------------
# 17-18: Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_remove_all_listeners_for_event(self):
        ee = EventEmitter()
        ee.on("a", lambda: None)
        ee.on("a", lambda: None)
        ee.on("b", lambda: None)
        ee.remove_all_listeners("a")
        assert ee.listener_count("a") == 0
        assert ee.listener_count("b") == 1

    def test_remove_all_listeners_global(self):
        ee = EventEmitter()
        ee.on("a", lambda: None)
        ee.on("b", lambda: None)
        ee.remove_all_listeners()
        assert ee.listener_count("a") == 0
        assert ee.listener_count("b") == 0
