# Group C Master Blackboard

## Task
status: in_progress
spec: experiments/03-token-efficiency/task-description.md

## Design Decisions

### AMB-1: Priority Direction
decision: Lower number = higher priority. Priority 1 runs FIRST. Range 1–10, default 5.

### AMB-2: Error Handling Policy
decision: All listeners execute regardless of errors (one bad listener never blocks others). Errors are collected. If `error_handler` callback is set on emitter, each error is passed to `error_handler(event_name, listener, exception)`. If no error_handler and errors occurred, raise `ListenerError` (containing all errors) after all listeners ran. `emit()` always returns the list of return values first — errors are raised/handled after.

### AMB-3: Wildcard Support
decision: `on("*", fn)` catches ALL events — YES. Pattern matching (`user.*`) — NO, too complex for stdlib. Wildcard listeners receive `fn(event_name, *args, **kwargs)` — first arg is the event name so they know which event fired. Wildcard listeners are called AFTER regular listeners for the specific event.

### AMB-4: Async Support
decision: Sync-only. All listeners are regular callables. No async/await support. Keeps the library simple and stdlib-only.

### AMB-5: Max Listeners
decision: Default 10 per event. When exceeded, issue `MaxListenersExceededWarning` via `warnings.warn()` — soft cap, does NOT block registration. Configurable: `emitter.max_listeners = N` (0 = unlimited, no warning). The warning fires once per event when the threshold is first crossed.

### AMB-6: Event Data Model
decision: Pass-through args/kwargs. `emitter.emit("click", x, y, button="left")` → listeners called as `fn(x, y, button="left")`. No typed Event wrapper object. Wildcard listeners get `fn(event_name, *args, **kwargs)`.

### AMB-7: Listener Ordering
decision: Within same priority: FIFO (registration order). Across priorities: lower number first (priority 1 before priority 10). Stable sort — registration order preserved within each priority level.

### AMB-8: Return Values
decision: Listeners CAN return values. `emit()` returns `list[Any]` of return values in execution order. If a listener errored (and error_handler caught it), `None` is placed in that slot. If no listeners registered, returns empty list.

### Interface Contract
```python
# ─── types.py (Dev A) ───────────────────────────────

from dataclasses import dataclass, field
from typing import Any, Callable, Optional
import uuid

# Constants
PRIORITY_MIN = 1
PRIORITY_MAX = 10
PRIORITY_DEFAULT = 5
MAX_LISTENERS_DEFAULT = 10

# Errors
class EventEmitterError(Exception):
    """Base error for the event emitter library."""

class ListenerError(EventEmitterError):
    """Raised when listeners fail during emit. Contains all collected errors."""
    def __init__(self, errors: list[tuple[str, Callable, Exception]]):
        self.errors = errors  # [(event_name, listener_fn, exception), ...]
        super().__init__(f"{len(errors)} listener(s) raised errors")

class MaxListenersExceededWarning(UserWarning):
    """Warning when listener count exceeds max_listeners threshold."""

class InvalidPriorityError(EventEmitterError, ValueError):
    """Raised when priority is outside valid range."""

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
        """Cancel subscription. Returns True if actually cancelled, False if already inactive."""
        if not self.active:
            return False
        self.active = False
        if self._emitter is not None:
            self._emitter._remove_subscription(self)
        return True

# ─── emitter.py (Dev B) ─────────────────────────────

class EventEmitter:
    def __init__(self, max_listeners: int = 10, error_handler: Optional[Callable] = None): ...

    def on(self, event_name: str, listener: Callable, *, priority: int = 5) -> Subscription:
        """Register listener. Returns Subscription. Warns if max_listeners exceeded."""

    def once(self, event_name: str, listener: Callable, *, priority: int = 5) -> Subscription:
        """Register one-time listener. Auto-removed after first call."""

    def off(self, event_name: str, listener: Callable) -> bool:
        """Remove a specific listener. Returns True if found and removed."""

    def emit(self, event_name: str, *args: Any, **kwargs: Any) -> list[Any]:
        """Emit event. Calls listeners in priority order. Returns list of return values.
        Wildcard listeners called AFTER specific listeners.
        If error_handler set: errors caught, None in return slot.
        If no error_handler: ListenerError raised after all listeners run."""

    def listener_count(self, event_name: str) -> int:
        """Return count of active listeners for event (excludes wildcard)."""

    def remove_all_listeners(self, event_name: str | None = None) -> int:
        """Remove all listeners (or for specific event). Returns count removed."""

    @property
    def max_listeners(self) -> int: ...
    @max_listeners.setter
    def max_listeners(self, value: int) -> None: ...

    @property
    def error_handler(self) -> Optional[Callable]: ...
    @error_handler.setter
    def error_handler(self, handler: Optional[Callable]) -> None: ...

    def _remove_subscription(self, sub: Subscription) -> None:
        """Internal: called by Subscription.cancel()."""
```

## Assignments

| task-id | file | owner | status | notes |
|---------|------|-------|--------|-------|
| design | — | architect | done | all 8 ambiguities resolved |
| types | types.py | dev-a | ready | interface stubs written in types.py |
| pkg-init | __init__.py | dev-a | ready | export public API |
| emitter | emitter.py | dev-b | ready | core logic |
| review | all | reviewer | blocked(impl) | |
| tests | test_emitter.py | tester | blocked(review) | |

## Findings


## Metrics
messages_sent: 1
clarifications: 0
