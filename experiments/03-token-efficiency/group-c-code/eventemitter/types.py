"""Event emitter type definitions.

Owner: Developer A

Types for the event emitter library:
- Subscription: handle for managing listener registrations
- Error hierarchy: EventEmitterError, ListenerError, InvalidPriorityError
- MaxListenersExceededWarning
- Priority and max listener constants
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


# ─── Constants ─────────────────────────────────────────────────────
# Lower number = higher priority.  Priority 1 runs FIRST.
PRIORITY_MIN = 1
PRIORITY_MAX = 10
PRIORITY_DEFAULT = 5
MAX_LISTENERS_DEFAULT = 10


# ─── Errors ────────────────────────────────────────────────────────

class EventEmitterError(Exception):
    """Base error for the event emitter library."""


class ListenerError(EventEmitterError):
    """Raised when one or more listeners fail during emit.

    Attributes:
        errors: List of (event_name, listener_fn, exception) tuples.
    """

    def __init__(self, errors: list[tuple[str, Callable, Exception]]) -> None:
        self.errors = errors
        super().__init__(f"{len(errors)} listener(s) raised errors")


class InvalidPriorityError(EventEmitterError, ValueError):
    """Raised when priority is outside the valid range (1-10)."""


class MaxListenersExceededWarning(UserWarning):
    """Warning issued when listener count exceeds max_listeners threshold."""


# ─── Subscription ──────────────────────────────────────────────────

@dataclass
class Subscription:
    """Handle returned by on()/once() for managing a listener registration.

    Call cancel() to unsubscribe. Cancelling an already-cancelled subscription
    returns False.
    """

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    event_name: str = ""
    listener: Callable[..., Any] = field(default=None)
    priority: int = PRIORITY_DEFAULT
    once: bool = False
    active: bool = True
    _emitter: Any = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not (PRIORITY_MIN <= self.priority <= PRIORITY_MAX):
            raise InvalidPriorityError(
                f"Priority must be {PRIORITY_MIN}-{PRIORITY_MAX}, got {self.priority}"
            )

    def cancel(self) -> bool:
        """Cancel this subscription. Returns True if actually cancelled."""
        if not self.active:
            return False
        self.active = False
        if self._emitter is not None:
            self._emitter._remove_subscription(self)
        return True

    # Priority ordering for sorted listener dispatch
    def __lt__(self, other: Subscription) -> bool:
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.id < other.id
