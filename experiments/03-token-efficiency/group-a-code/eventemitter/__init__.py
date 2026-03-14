"""Event emitter library — public API.

Usage::

    from eventemitter import EventEmitter, Subscription

    emitter = EventEmitter()
    sub = emitter.on("click", lambda x: print(x))
    emitter.emit("click", "hello")
    sub.cancel()
"""

from eventemitter.emitter import EventEmitter
from eventemitter.types import (
    EmitError,
    EmitterError,
    ErrorHandler,
    Listener,
    MaxListenersWarning,
    Subscription,
)

__all__ = [
    "EventEmitter",
    "Subscription",
    "Listener",
    "ErrorHandler",
    "EmitterError",
    "EmitError",
    "MaxListenersWarning",
]
