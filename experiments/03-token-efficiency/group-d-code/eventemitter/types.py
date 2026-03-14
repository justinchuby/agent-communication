"""Event emitter type definitions — interface contract.

DO NOT change signatures without architect sign-off.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Protocol


# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

ListenerFn = Callable[..., Any]
ErrorHandler = Callable[[str, Exception, ListenerFn], None]


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class EventEmitterError(Exception):
    """Base error for event emitter operations."""


class MaxListenersExceededWarning(UserWarning):
    """Warning emitted when listener count exceeds the per-event cap."""


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class Listener:
    """A registered event listener."""

    fn: ListenerFn
    priority: int = 0           # lower number = higher priority (1 is highest)
    once: bool = False
    _seq: int = 0               # insertion order for FIFO tie-breaking

    def __lt__(self, other: Listener) -> bool:
        """Sort by priority ascending, then by insertion order (FIFO)."""
        if self.priority != other.priority:
            return self.priority < other.priority
        return self._seq < other._seq


@dataclass(slots=True)
class Subscription:
    """Handle returned by on()/once(). Call cancel() to unsubscribe."""

    event: str
    listener: Listener
    _emitter: Any = field(repr=False)  # back-reference to EventEmitter
    _cancelled: bool = field(default=False, repr=False)

    def cancel(self) -> None:
        """Remove this listener from the emitter."""
        if not self._cancelled:
            self._emitter.off(self.event, self.listener.fn)
            self._cancelled = True


# ---------------------------------------------------------------------------
# EventEmitter protocol (Dev B implements)
# ---------------------------------------------------------------------------

class EventEmitterProtocol(Protocol):
    """Abstract interface for the event emitter."""

    def on(
        self,
        event: str,
        fn: ListenerFn,
        priority: int = 0,
    ) -> Subscription: ...

    def once(
        self,
        event: str,
        fn: ListenerFn,
        priority: int = 0,
    ) -> Subscription: ...

    def emit(self, event: str, *args: Any, **kwargs: Any) -> int: ...

    def off(self, event: str, fn: ListenerFn) -> bool: ...

    def remove_all_listeners(self, event: str | None = None) -> None: ...

    def listener_count(self, event: str) -> int: ...

    @property
    def max_listeners(self) -> int: ...

    @max_listeners.setter
    def max_listeners(self, value: int) -> None: ...
