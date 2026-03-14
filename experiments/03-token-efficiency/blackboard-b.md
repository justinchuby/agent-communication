# Group B Blackboard

## Task
status: in_progress
spec: experiments/03-token-efficiency/task-description.md

## Design Decisions

### AMB-1: Priority Direction
decision: **1 = highest priority**
- Range: 1–10 inclusive. Default: 5.
- Lower number = called first.
- Invalid values raise `ValueError`.

### AMB-2: Error Handling Policy
decision: **Configurable error_handler callback**
- Default (no handler): exception propagates immediately, remaining listeners skipped.
- With `error_handler: Callable[[str, Exception], None]`: exceptions caught, passed to handler with event name, remaining listeners still execute.
- Set at construction or via `emitter.error_handler = fn`.

### AMB-3: Wildcard Support
decision: **`"*"` catches all events, no pattern matching**
- `on("*", fn)` registers a wildcard listener called on every `emit()`.
- Wildcard listeners run AFTER event-specific listeners.
- Wildcard listeners respect priority ordering among themselves.
- No glob/regex patterns like `user.*`.

### AMB-4: Async Support
decision: **Sync-only**
- All listeners are synchronous callables.
- No asyncio support. Keeps stdlib-only, simple, testable.

### AMB-5: Max Listeners
decision: **10 per event, configurable, warning (not error)**
- Default `max_listeners`: 10 per event.
- Exceeding emits `MaxListenersExceededWarning` via `warnings.warn`.
- `max_listeners = 0` means unlimited (no warning).
- Configurable at init or via property setter.

### AMB-6: Event Data Model
decision: **Pass-through positional + keyword args**
- `emit(event_name, *args, **kwargs)` → `listener(*args, **kwargs)`.
- No typed Event object. Event name is `str`.
- Listeners receive exactly what `emit()` is given.

### AMB-7: Listener Ordering
decision: **Same priority: FIFO (registration order)**
- Listeners sorted by priority (1 first), then by registration order within same priority.

### AMB-8: Return Values
decision: **Listeners return values are ignored; `emit()` returns listener count**
- `emit()` returns `int` — number of listeners called.
- Listener return values discarded.

### Interface Contract
```python
from __future__ import annotations

import uuid
import warnings
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

# Type aliases
ListenerFn = Callable[..., Any]
ErrorHandler = Callable[[str, Exception], None]


@dataclass
class Listener:
    """Internal wrapper around a registered listener function."""
    callback: ListenerFn
    priority: int = 5          # 1=highest, 10=lowest
    once: bool = False
    listener_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    _sequence: int = 0         # auto-set on registration for FIFO within priority

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


class EventEmitterError(Exception):
    """Base error for the eventemitter library."""


class MaxListenersExceededWarning(UserWarning):
    """Emitted when listener count exceeds max_listeners for an event."""


# --- EventEmitter interface (implemented in emitter.py) ---

class EventEmitter:
    def __init__(self, max_listeners: int = 10,
                 error_handler: Optional[ErrorHandler] = None) -> None: ...
    def on(self, event_name: str, listener: ListenerFn,
           priority: int = 5) -> Subscription: ...
    def once(self, event_name: str, listener: ListenerFn,
             priority: int = 5) -> Subscription: ...
    def off(self, event_name: str, listener: ListenerFn) -> bool: ...
    def emit(self, event_name: str, *args: Any, **kwargs: Any) -> int: ...
    def listener_count(self, event_name: str) -> int: ...
    def remove_all_listeners(self, event_name: Optional[str] = None) -> None: ...
    @property
    def max_listeners(self) -> int: ...
    @max_listeners.setter
    def max_listeners(self, value: int) -> None: ...
```
contract_status: done

## Assignments

| task-id | file | owner | status | notes |
|---------|------|-------|--------|-------|
| design | — | architect | done | all 8 ambiguities resolved, interface in types.py |
| types | types.py | dev-a | done | added __post_init__ priority validation |
| pkg-init | __init__.py | dev-a | done | exports all types + errors; lazy-imports EventEmitter |
| emitter | emitter.py | dev-b | ready | EventEmitter core logic |
| review | all | reviewer | blocked(impl) | |
| tests | test_emitter.py | tester | blocked(review) | |

## Findings


## Metrics
messages_sent: 1
clarifications: 0
