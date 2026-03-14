"""eventemitter — A Python event emitter library.

Public API exports for the eventemitter package.
"""

from eventemitter.types import (
    ErrorHandler,
    EventEmitterError,
    Listener,
    ListenerFn,
    MaxListenersExceededWarning,
    Subscription,
)
from eventemitter.emitter import EventEmitter

__all__ = [
    "EventEmitter",
    "EventEmitterError",
    "ErrorHandler",
    "Listener",
    "ListenerFn",
    "MaxListenersExceededWarning",
    "Subscription",
]
