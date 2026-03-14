"""eventemitter — A Python event emitter library.

Public API re-exports for convenience.
"""

from eventemitter.types import (
    Listener,
    Subscription,
    ListenerFn,
    ErrorHandler,
    EventEmitterError,
    MaxListenersExceededWarning,
)

__all__ = [
    # Data models
    "Listener",
    "Subscription",
    # Type aliases
    "ListenerFn",
    "ErrorHandler",
    # Errors / warnings
    "EventEmitterError",
    "MaxListenersExceededWarning",
]


def _import_emitter() -> None:
    """Lazy-import emitter exports so init works even if emitter isn't ready yet."""
    from eventemitter.emitter import EventEmitter  # noqa: F811

    globals()["EventEmitter"] = EventEmitter
    __all__.append("EventEmitter")


try:
    _import_emitter()
except ImportError:
    pass
