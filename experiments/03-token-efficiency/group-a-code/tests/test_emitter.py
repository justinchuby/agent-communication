"""Tests for the EventEmitter library.

Owner: Tester

18 tests covering:
    1. on() registers a listener and emit() calls it
    2. emit() passes args and kwargs to listeners
    3. Multiple listeners on same event all called
    4. Listeners called in priority order (lower = higher priority)
    5. Same-priority listeners called in FIFO order
    6. once() listener fires only once then auto-removes
    7. subscription.cancel() stops future calls
    8. subscription.is_active reflects state
    9. off() removes a listener by reference
    10. off() returns False for unknown listener
    11. remove_all_listeners(event) clears one event
    12. remove_all_listeners(None) clears all events
    13. listener_count() returns correct count
    14. listener_count() excludes cancelled subscriptions
    15. Error handling: no handler → EmitError with collected exceptions
    16. Error handling: custom error_handler called instead of raising
    17. max_listeners warning issued when exceeded
    18. emit() continues calling remaining listeners after one raises
"""

import warnings

import pytest

from eventemitter import (
    EmitError,
    EventEmitter,
    MaxListenersWarning,
    Subscription,
)


@pytest.fixture
def emitter():
    return EventEmitter()


# 1. on() registers a listener and emit() calls it
def test_on_and_emit_basic(emitter):
    results = []
    emitter.on("click", lambda: results.append("clicked"))
    emitter.emit("click")
    assert results == ["clicked"]


# 2. emit() passes args and kwargs to listeners
def test_emit_passes_args_and_kwargs(emitter):
    received = {}

    def handler(x, y, label=None):
        received["x"] = x
        received["y"] = y
        received["label"] = label

    emitter.on("data", handler)
    emitter.emit("data", 1, 2, label="test")
    assert received == {"x": 1, "y": 2, "label": "test"}


# 3. Multiple listeners on same event all called
def test_multiple_listeners_all_called(emitter):
    calls = []
    emitter.on("evt", lambda: calls.append("a"))
    emitter.on("evt", lambda: calls.append("b"))
    emitter.on("evt", lambda: calls.append("c"))
    emitter.emit("evt")
    assert calls == ["a", "b", "c"]


# 4. Listeners called in priority order (lower = higher priority)
def test_priority_ordering(emitter):
    calls = []
    emitter.on("evt", lambda: calls.append("low"), priority=10)
    emitter.on("evt", lambda: calls.append("high"), priority=1)
    emitter.on("evt", lambda: calls.append("mid"), priority=5)
    emitter.emit("evt")
    assert calls == ["high", "mid", "low"]


# 5. Same-priority listeners called in FIFO order
def test_same_priority_fifo(emitter):
    calls = []
    emitter.on("evt", lambda: calls.append("first"), priority=0)
    emitter.on("evt", lambda: calls.append("second"), priority=0)
    emitter.on("evt", lambda: calls.append("third"), priority=0)
    emitter.emit("evt")
    assert calls == ["first", "second", "third"]


# 6. once() listener fires only once then auto-removes
def test_once_fires_once(emitter):
    calls = []
    emitter.once("evt", lambda: calls.append("once"))
    emitter.emit("evt")
    emitter.emit("evt")
    assert calls == ["once"]
    assert emitter.listener_count("evt") == 0


# 7. subscription.cancel() stops future calls
def test_subscription_cancel(emitter):
    calls = []
    sub = emitter.on("evt", lambda: calls.append("called"))
    emitter.emit("evt")
    sub.cancel()
    emitter.emit("evt")
    assert calls == ["called"]


# 8. subscription.is_active reflects state
def test_subscription_is_active(emitter):
    sub = emitter.on("evt", lambda: None)
    assert sub.is_active is True
    sub.cancel()
    assert sub.is_active is False
    # Double cancel is safe
    sub.cancel()
    assert sub.is_active is False


# 9. off() removes a listener by reference
def test_off_removes_listener(emitter):
    calls = []
    fn = lambda: calls.append("x")
    emitter.on("evt", fn)
    result = emitter.off("evt", fn)
    assert result is True
    emitter.emit("evt")
    assert calls == []


# 10. off() returns False for unknown listener
def test_off_returns_false_for_unknown(emitter):
    result = emitter.off("evt", lambda: None)
    assert result is False


# 11. remove_all_listeners(event) clears one event
def test_remove_all_listeners_single_event(emitter):
    emitter.on("a", lambda: None)
    emitter.on("a", lambda: None)
    emitter.on("b", lambda: None)
    emitter.remove_all_listeners("a")
    assert emitter.listener_count("a") == 0
    assert emitter.listener_count("b") == 1


# 12. remove_all_listeners(None) clears all events
def test_remove_all_listeners_all_events(emitter):
    emitter.on("a", lambda: None)
    emitter.on("b", lambda: None)
    emitter.on("c", lambda: None)
    emitter.remove_all_listeners()
    assert emitter.listener_count("a") == 0
    assert emitter.listener_count("b") == 0
    assert emitter.listener_count("c") == 0


# 13. listener_count() returns correct count
def test_listener_count(emitter):
    assert emitter.listener_count("evt") == 0
    emitter.on("evt", lambda: None)
    emitter.on("evt", lambda: None)
    assert emitter.listener_count("evt") == 2


# 14. listener_count() excludes cancelled subscriptions
def test_listener_count_excludes_cancelled(emitter):
    sub1 = emitter.on("evt", lambda: None)
    emitter.on("evt", lambda: None)
    assert emitter.listener_count("evt") == 2
    sub1.cancel()
    assert emitter.listener_count("evt") == 1


# 15. Error handling: no handler → EmitError with collected exceptions
def test_emit_error_no_handler(emitter):
    def bad_listener():
        raise ValueError("boom")

    emitter.on("evt", bad_listener)
    with pytest.raises(EmitError) as exc_info:
        emitter.emit("evt")
    assert len(exc_info.value.errors) == 1
    assert exc_info.value.event == "evt"
    assert isinstance(exc_info.value.errors[0], ValueError)


# 16. Error handling: custom error_handler called instead of raising
def test_custom_error_handler():
    errors_caught = []

    def handler(event, exc, listener):
        errors_caught.append((event, exc))

    emitter = EventEmitter(error_handler=handler)
    emitter.on("evt", lambda: 1 / 0)
    emitter.emit("evt")  # Should not raise
    assert len(errors_caught) == 1
    assert errors_caught[0][0] == "evt"
    assert isinstance(errors_caught[0][1], ZeroDivisionError)


# 17. max_listeners warning issued when exceeded
def test_max_listeners_warning():
    emitter = EventEmitter(max_listeners=2)
    emitter.on("evt", lambda: None)
    emitter.on("evt", lambda: None)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        emitter.on("evt", lambda: None)  # 3rd listener exceeds max of 2
    assert len(w) == 1
    assert issubclass(w[0].category, MaxListenersWarning)
    assert "3 listeners" in str(w[0].message)


# 18. emit() continues calling remaining listeners after one raises
def test_emit_continues_after_error(emitter):
    calls = []

    def good_before():
        calls.append("before")

    def bad():
        raise RuntimeError("fail")

    def good_after():
        calls.append("after")

    emitter.on("evt", good_before, priority=1)
    emitter.on("evt", bad, priority=2)
    emitter.on("evt", good_after, priority=3)

    with pytest.raises(EmitError):
        emitter.emit("evt")

    assert calls == ["before", "after"]
