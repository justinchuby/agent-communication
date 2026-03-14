"""Tests for the event emitter library.

Owner: Tester (Group C)

18 tests covering:
- Basic registration and emission (3)
- Priority ordering (2)
- Once listeners (2)
- Unsubscription (3)
- Wildcard listeners (2)
- Error handling (2)
- Max listeners warning (1)
- Edge cases (3)
"""

import warnings

import pytest

from eventemitter import (
    EventEmitter,
    Subscription,
    ListenerError,
    InvalidPriorityError,
    MaxListenersExceededWarning,
)


# ─── Basic Registration and Emission ──────────────────────────────

class TestBasicEmission:
    def test_on_returns_subscription(self):
        """on() returns a Subscription with correct metadata."""
        ee = EventEmitter()
        sub = ee.on("click", lambda: None, priority=3)
        assert isinstance(sub, Subscription)
        assert sub.event_name == "click"
        assert sub.priority == 3
        assert sub.active is True

    def test_emit_triggers_listener(self):
        """emit() calls registered listener with correct args."""
        received = []
        ee = EventEmitter()
        ee.on("data", lambda x, y: received.append((x, y)))
        ee.emit("data", 1, 2)
        assert received == [(1, 2)]

    def test_emit_returns_listener_results(self):
        """emit() returns list of listener return values."""
        ee = EventEmitter()
        ee.on("calc", lambda: 10)
        ee.on("calc", lambda: 20)
        results = ee.emit("calc")
        assert sorted(results) == [10, 20]


# ─── Priority Ordering ────────────────────────────────────────────

class TestPriorityOrdering:
    def test_higher_priority_runs_first(self):
        """Priority 1 (highest) listener runs before priority 10 (lowest)."""
        order = []
        ee = EventEmitter()
        ee.on("evt", lambda: order.append("low"), priority=10)
        ee.on("evt", lambda: order.append("high"), priority=1)
        ee.on("evt", lambda: order.append("mid"), priority=5)
        ee.emit("evt")
        assert order == ["high", "mid", "low"]

    def test_same_priority_fifo(self):
        """Listeners with same priority are called in FIFO registration order."""
        order = []
        ee = EventEmitter()
        ee.on("evt", lambda: order.append("first"), priority=5)
        ee.on("evt", lambda: order.append("second"), priority=5)
        ee.on("evt", lambda: order.append("third"), priority=5)
        ee.emit("evt")
        assert order == ["first", "second", "third"]


# ─── Once Listeners ───────────────────────────────────────────────

class TestOnceListeners:
    def test_once_fires_only_once(self):
        """once() listener is auto-removed after first emit."""
        count = [0]
        ee = EventEmitter()
        ee.once("ping", lambda: count.__setitem__(0, count[0] + 1))
        ee.emit("ping")
        ee.emit("ping")
        assert count[0] == 1

    def test_once_removed_from_count(self):
        """After firing, once listener no longer appears in listener_count."""
        ee = EventEmitter()
        ee.once("evt", lambda: None)
        assert ee.listener_count("evt") == 1
        ee.emit("evt")
        assert ee.listener_count("evt") == 0


# ─── Unsubscription ───────────────────────────────────────────────

class TestUnsubscription:
    def test_cancel_subscription(self):
        """Subscription.cancel() removes the listener."""
        called = [False]
        ee = EventEmitter()
        sub = ee.on("evt", lambda: called.__setitem__(0, True))
        sub.cancel()
        ee.emit("evt")
        assert called[0] is False
        assert sub.active is False

    def test_cancel_returns_false_on_double_cancel(self):
        """Cancelling an already-cancelled subscription returns False."""
        ee = EventEmitter()
        sub = ee.on("evt", lambda: None)
        assert sub.cancel() is True
        assert sub.cancel() is False

    def test_off_removes_by_reference(self):
        """off() removes a specific listener by function reference."""
        order = []
        fn_a = lambda: order.append("a")
        fn_b = lambda: order.append("b")
        ee = EventEmitter()
        ee.on("evt", fn_a)
        ee.on("evt", fn_b)
        assert ee.off("evt", fn_a) is True
        ee.emit("evt")
        assert order == ["b"]


# ─── Wildcard Listeners ───────────────────────────────────────────

class TestWildcardListeners:
    def test_wildcard_catches_all_events(self):
        """on("*", fn) listener receives all emitted events."""
        received = []
        ee = EventEmitter()
        ee.on("*", lambda name, *a: received.append(name))
        ee.emit("click")
        ee.emit("hover")
        assert received == ["click", "hover"]

    def test_wildcard_receives_event_name_as_first_arg(self):
        """Wildcard listener gets (event_name, *args, **kwargs)."""
        received = []
        ee = EventEmitter()
        ee.on("*", lambda name, x: received.append((name, x)))
        ee.emit("data", 42)
        assert received == [("data", 42)]


# ─── Error Handling ────────────────────────────────────────────────

class TestErrorHandling:
    def test_error_without_handler_raises_listener_error(self):
        """Without error_handler, a failing listener raises ListenerError after all run."""
        results_seen = []
        ee = EventEmitter()
        ee.on("evt", lambda: results_seen.append("ok"), priority=1)

        def bad():
            raise RuntimeError("boom")

        ee.on("evt", bad, priority=2)
        with pytest.raises(ListenerError) as exc_info:
            ee.emit("evt")
        assert len(exc_info.value.errors) == 1
        assert results_seen == ["ok"]  # first listener still ran

    def test_error_with_handler_collects_errors(self):
        """With error_handler set, errors are caught and handler is called."""
        caught = []
        ee = EventEmitter(error_handler=lambda name, fn, exc: caught.append(str(exc)))
        ee.on("evt", lambda: 1 / 0)
        results = ee.emit("evt")
        assert len(caught) == 1
        assert "division by zero" in caught[0]
        assert results == [None]  # errored listener produces None


# ─── Max Listeners Warning ─────────────────────────────────────────

class TestMaxListeners:
    def test_warns_when_exceeding_max_listeners(self):
        """Adding more listeners than max_listeners triggers a warning."""
        ee = EventEmitter(max_listeners=2)
        ee.on("evt", lambda: None)
        ee.on("evt", lambda: None)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            ee.on("evt", lambda: None)  # 3rd, exceeds limit of 2
            assert len(w) == 1
            assert issubclass(w[0].category, MaxListenersExceededWarning)


# ─── Edge Cases ────────────────────────────────────────────────────

class TestEdgeCases:
    def test_emit_with_no_listeners(self):
        """Emitting an event with no listeners returns empty list."""
        ee = EventEmitter()
        results = ee.emit("ghost")
        assert results == []

    def test_invalid_priority_raises(self):
        """Priority outside 1-10 raises InvalidPriorityError."""
        ee = EventEmitter()
        with pytest.raises(InvalidPriorityError):
            ee.on("evt", lambda: None, priority=0)
        with pytest.raises(InvalidPriorityError):
            ee.on("evt", lambda: None, priority=11)

    def test_remove_all_listeners(self):
        """remove_all_listeners() clears all registered listeners."""
        ee = EventEmitter()
        ee.on("a", lambda: None)
        ee.on("b", lambda: None)
        ee.on("b", lambda: None)
        count = ee.remove_all_listeners()
        assert count == 3
        assert ee.listener_count("a") == 0
        assert ee.listener_count("b") == 0
