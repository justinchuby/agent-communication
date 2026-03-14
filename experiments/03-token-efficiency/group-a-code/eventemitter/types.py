"""Event emitter type definitions and interface contracts.

Defines the data types, type aliases, and exception classes used across
the event emitter library.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

Listener = Callable[..., Any]
"""A listener is any callable that accepts the args/kwargs passed to emit()."""

ErrorHandler = Callable[[str, Exception, Listener], None]
"""Signature: (event_name, exception, listener_fn) -> None.

Called when a listener raises during emit(), if an error handler is set.
"""


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class EmitterError(Exception):
    """Base exception for the event emitter library."""


class EmitError(EmitterError):
    """Raised after emit() if listeners raised and no error_handler is set.

    Wraps one or more listener exceptions so the caller can inspect them.
    """

    def __init__(self, event: str, errors: list[Exception]) -> None:
        self.event = event
        self.errors = errors
        count = len(errors)
        super().__init__(
            f"{count} listener(s) raised during emit({event!r}): "
            + "; ".join(str(e) for e in errors)
        )


class MaxListenersWarning(UserWarning):
    """Warning issued when the listener count exceeds max_listeners."""


# ---------------------------------------------------------------------------
# Subscription handle
# ---------------------------------------------------------------------------

@dataclass
class Subscription:
    """Handle returned by on()/once() that lets the caller cancel the listener.

    Call ``cancel()`` to unsubscribe. Safe to call multiple times.
    """

    event: str
    """The event name this subscription is for."""

    listener: Listener
    """The registered listener callable."""

    priority: int = 0
    """Priority value. Lower number = higher priority (called first)."""

    once: bool = False
    """If True, the listener auto-removes after its first invocation."""

    _cancelled: bool = field(default=False, repr=False)
    """Internal flag — True after cancel() has been called."""

    _cancel_fn: Callable[[], None] | None = field(default=None, repr=False)
    """Internal callback wired by the emitter to perform actual removal."""

    def cancel(self) -> None:
        """Unsubscribe this listener. No-op if already cancelled."""
        if not self._cancelled and self._cancel_fn is not None:
            self._cancel_fn()
            self._cancelled = True

    @property
    def is_active(self) -> bool:
        """True if this subscription has not been cancelled."""
        return not self._cancelled
