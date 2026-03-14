"""Event emitter type definitions.

Owner: Developer A

Types for the event emitter library. Interfaces defined by Architect.
Dev A: implement as-is; add helper methods if needed, do NOT change field names/types.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Callable


# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

ListenerFn = Callable[..., Any]
ErrorHandler = Callable[[str, Exception], None]


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class Listener:
    """Internal wrapper around a registered listener function.

    Priority: 1 = highest (called first), 10 = lowest. Default 5.
    Within same priority: FIFO by _sequence (registration order).
    """
    callback: ListenerFn
    priority: int = 5
    once: bool = False
    listener_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    _sequence: int = 0  # auto-set on registration for FIFO within priority

    def __post_init__(self) -> None:
        if not (1 <= self.priority <= 10):
            raise ValueError(f"Priority must be 1-10, got {self.priority}")

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Listener):
            return NotImplemented
        if self.priority != other.priority:
            return self.priority < other.priority
        return self._sequence < other._sequence


@dataclass
class Subscription:
    """Handle returned by on()/once() — call cancel() to unsubscribe."""
    event_name: str
    listener_id: str
    _cancel_fn: Callable[[], None] = field(repr=False)

    def cancel(self) -> None:
        """Remove the associated listener."""
        self._cancel_fn()


# ---------------------------------------------------------------------------
# Error / warning types
# ---------------------------------------------------------------------------

class EventEmitterError(Exception):
    """Base error for the eventemitter library."""


class MaxListenersExceededWarning(UserWarning):
    """Emitted when listener count exceeds max_listeners for an event."""
