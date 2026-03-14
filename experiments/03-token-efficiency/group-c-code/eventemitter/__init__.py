"""eventemitter - A Python event emitter library.

Register listeners for named events, emit events with priority ordering,
and manage subscriptions with error handling.

Quick start:
    from eventemitter import EventEmitter

    ee = EventEmitter()
    sub = ee.on("data", lambda x: print(x))
    ee.emit("data", "hello")
    sub.cancel()
"""

from eventemitter.types import (
    Subscription,
    EventEmitterError,
    ListenerError,
    MaxListenersExceededWarning,
    InvalidPriorityError,
    PRIORITY_MIN,
    PRIORITY_MAX,
    PRIORITY_DEFAULT,
    MAX_LISTENERS_DEFAULT,
)

from eventemitter.emitter import EventEmitter

__all__ = [
    "EventEmitter",
    "Subscription",
    "EventEmitterError",
    "ListenerError",
    "MaxListenersExceededWarning",
    "InvalidPriorityError",
    "PRIORITY_MIN",
    "PRIORITY_MAX",
    "PRIORITY_DEFAULT",
    "MAX_LISTENERS_DEFAULT",
]
