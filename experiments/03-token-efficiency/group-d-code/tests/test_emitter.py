"""Tests for the event emitter library (Group D).

Owner: Tester

18 tests covering:
- Basic registration and emission (3)
- Priority ordering (2)
- Once listeners (2)
- Unsubscription (3)
- Error handling (3)
- Max listeners warning (1)
- Remove all listeners (1)
- Edge cases (3)
"""

import warnings

import pytest

from eventemitter import (
    EventEmitter,
    Subscription,
    Listener,
    EventEmitterError,
    MaxListenersExceededWarning,
)


# ─── Basic Registration and Emission ──────────────────────────────

class TestBasicEmission:
    def test_on_returns_subscription(self):
        """on() returns a Subscription with correct metadata."""
        ee = EventEmitter()
        sub = ee.on("click", lambda: None, priority=2)
        assert isinstance(sub, Subscription)
        assert sub.event == "click"
        assert sub.listener.priority == 2
        assert sub._cancelled is False

    def test_emit_triggers_listener_with_args(self):
        """emit() calls registered listener with correct args and kwargs."""
        received = []
        ee = EventEmitter()
        ee.on("data", lambda x, y, z=0: received.append((x, y, z)))
        ee.emit("data", 1, 2, z=3)
        assert received == [(1, 2, 3)]

    def test_emit_returns_listener_count(self):
        """emit() returns the number of listeners called."""
        ee = EventEmitter()
        ee.on("evt", lambda: None)
        ee.on("evt", lambda: None)
        ee.on("evt", lambda: None)
        count = ee.emit("evt")
        assert count == 3


# ─── Priority Ordering ────────────────────────────────────────────

class TestPriorityOrdering:
    def test_lower_priority_number_runs_first(self):
        """Priority 0 (highest) runs before priority 10 (lowest)."""
        order = []
        ee = EventEmitter()
        ee.on("evt", lambda: order.append("low"), priority=10)
        ee.on("evt", lambda: order.append("high"), priority=0)
        ee.on("evt", lambda: order.append("mid"), priority=5)
        ee.emit("evt")
        assert order == ["high", "mid", "low"]

    def test_same_priority_fifo(self):
        """Listeners with same priority are called in registration (FIFO) order."""
        order = []
        ee = EventEmitter()
        ee.on("evt", lambda: order.append("first"), priority=0)
        ee.on("evt", lambda: order.append("second"), priority=0)
        ee.on("evt", lambda: order.append("third"), priority=0)
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
        """After firing, once listener is no longer counted."""
        ee = EventEmitter()
        ee.once("evt", lambda: None)
        assert ee.listener_count("evt") == 1
        ee.emit("evt")
        assert ee.listener_count("evt") == 0


# ─── Unsubscription ───────────────────────────────────────────────

class TestUnsubscription:
    def test_cancel_subscription(self):
        """Subscription.cancel() removes the listener from future emits."""
        called = [False]
        ee = EventEmitter()
        sub = ee.on("evt", lambda: called.__setitem__(0, True))
        sub.cancel()
        ee.emit("evt")
        assert called[0] is False

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

    def test_off_returns_false_for_unknown(self):
        """off() returns False when listener is not registered."""
        ee = EventEmitter()
        assert ee.off("evt", lambda: None) is False


# ─── Error Handling ────────────────────────────────────────────────

class TestErrorHandling:
    def test_error_without_handler_raises_first_exception(self):
        """Without error_handler, first exception is raised after all listeners run."""
        call_order = []
        ee = EventEmitter()
        ee.on("evt", lambda: call_order.append("ok1"), priority=0)

        def bad():
            call_order.append("bad")
            raise RuntimeError("boom")

        ee.on("evt", bad, priority=1)
        ee.on("evt", lambda: call_order.append("ok2"), priority=2)

        with pytest.raises(RuntimeError, match="boom"):
            ee.emit("evt")
        # All listeners should have been called
        assert call_order == ["ok1", "bad", "ok2"]

    def test_error_with_handler_continues(self):
        """With error_handler, errors are caught and remaining listeners still run."""
        caught = []
        call_order = []
        ee = EventEmitter(error_handler=lambda name, exc, fn: caught.append(str(exc)))

        def bad():
            raise ValueError("oops")

        ee.on("evt", bad, priority=0)
        ee.on("evt", lambda: call_order.append("after"), priority=1)
        count = ee.emit("evt")
        assert count == 2
        assert len(caught) == 1
        assert "oops" in caught[0]
        assert call_order == ["after"]

    def test_error_handler_receives_correct_args(self):
        """error_handler receives (event_name, exception, listener_fn)."""
        handler_args = []
        ee = EventEmitter(error_handler=lambda evt, exc, fn: handler_args.append((evt, type(exc).__name__, fn)))

        def bad_fn():
            raise TypeError("wrong type")

        ee.on("test_event", bad_fn)
        ee.emit("test_event")
        assert len(handler_args) == 1
        assert handler_args[0][0] == "test_event"
        assert handler_args[0][1] == "TypeError"
        assert handler_args[0][2] is bad_fn


# ─── Max Listeners Warning ─────────────────────────────────────────

class TestMaxListeners:
    def test_warns_when_exceeding_max_listeners(self):
        """Adding more listeners than max_listeners triggers a warning."""
        ee = EventEmitter(max_listeners=2)
        ee.on("evt", lambda: None)
        ee.on("evt", lambda: None)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            ee.on("evt", lambda: None)  # 3rd exceeds limit of 2
            assert len(w) == 1
            assert issubclass(w[0].category, MaxListenersExceededWarning)


# ─── Remove All Listeners ─────────────────────────────────────────

class TestRemoveAllListeners:
    def test_remove_all_for_specific_event(self):
        """remove_all_listeners(event) clears only that event's listeners."""
        ee = EventEmitter()
        ee.on("a", lambda: None)
        ee.on("b", lambda: None)
        ee.remove_all_listeners("a")
        assert ee.listener_count("a") == 0
        assert ee.listener_count("b") == 1


# ─── Edge Cases ────────────────────────────────────────────────────

class TestEdgeCases:
    def test_emit_with_no_listeners_returns_zero(self):
        """Emitting an event with no listeners returns 0."""
        ee = EventEmitter()
        assert ee.emit("ghost") == 0

    def test_listener_count_for_unknown_event(self):
        """listener_count for unregistered event returns 0."""
        ee = EventEmitter()
        assert ee.listener_count("unknown") == 0

    def test_remove_all_listeners_global(self):
        """remove_all_listeners() with no arg clears everything."""
        ee = EventEmitter()
        ee.on("a", lambda: None)
        ee.on("b", lambda: None)
        ee.on("b", lambda: None)
        ee.remove_all_listeners()
        assert ee.listener_count("a") == 0
        assert ee.listener_count("b") == 0
