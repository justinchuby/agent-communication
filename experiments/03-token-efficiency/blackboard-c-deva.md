# Group C — Dev A Scoped View

## Task
Event emitter library. You own: `types.py` + `__init__.py`
Code dir: experiments/03-token-efficiency/group-c-code/eventemitter/

## Decisions Relevant to types.py

- **AMB-1 Priority**: 1=highest, range 1–10, default 5
- **AMB-2 Errors**: `ListenerError` holds list of `(event_name, listener, exception)` tuples. Raised after all listeners run if no error_handler set.
- **AMB-3 Wildcard**: `"*"` catches all events. No pattern matching.
- **AMB-5 Max Listeners**: Default 10/event. `MaxListenersExceededWarning` via `warnings.warn()`. 0=unlimited.

## Interface Contract (types.py)

```python
from dataclasses import dataclass, field
from typing import Any, Callable, Optional
import uuid

PRIORITY_MIN = 1
PRIORITY_MAX = 10
PRIORITY_DEFAULT = 5
MAX_LISTENERS_DEFAULT = 10

class EventEmitterError(Exception):
    """Base error for the event emitter library."""

class ListenerError(EventEmitterError):
    """Raised when listeners fail during emit."""
    def __init__(self, errors: list[tuple[str, Callable, Exception]]):
        self.errors = errors  # [(event_name, listener_fn, exception), ...]
        super().__init__(f"{len(errors)} listener(s) raised errors")

class MaxListenersExceededWarning(UserWarning):
    """Warning when listener count exceeds max_listeners threshold."""

class InvalidPriorityError(EventEmitterError, ValueError):
    """Raised when priority is outside valid range (1–10)."""

@dataclass
class Subscription:
    """Handle returned by on()/once() for managing a listener."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    event_name: str = ""
    listener: Callable[..., Any] = field(default=None)
    priority: int = PRIORITY_DEFAULT
    once: bool = False
    active: bool = True
    _emitter: Any = field(default=None, repr=False, compare=False)

    def cancel(self) -> bool:
        """Cancel subscription. Returns True if actually cancelled."""
        if not self.active:
            return False
        self.active = False
        if self._emitter is not None:
            self._emitter._remove_subscription(self)
        return True
```

## __init__.py Exports

```python
from eventemitter.types import (
    Subscription, EventEmitterError, ListenerError,
    MaxListenersExceededWarning, InvalidPriorityError,
    PRIORITY_MIN, PRIORITY_MAX, PRIORITY_DEFAULT, MAX_LISTENERS_DEFAULT,
)
from eventemitter.emitter import EventEmitter

__all__ = [
    "EventEmitter", "Subscription",
    "EventEmitterError", "ListenerError",
    "MaxListenersExceededWarning", "InvalidPriorityError",
    "PRIORITY_MIN", "PRIORITY_MAX", "PRIORITY_DEFAULT", "MAX_LISTENERS_DEFAULT",
]
```

## Your Assignment

| task-id | file | status | notes |
|---------|------|--------|-------|
| types | types.py | ready | stubs written — implement fully |
| pkg-init | __init__.py | ready | export public API |
