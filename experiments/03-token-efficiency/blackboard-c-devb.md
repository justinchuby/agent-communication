# Group C — Dev B Scoped View

## Task
Event emitter library. You own: `emitter.py`
Code dir: experiments/03-token-efficiency/group-c-code/eventemitter/

## Decisions Relevant to emitter.py

- **AMB-1 Priority**: 1=highest, range 1–10, default 5. Lower number runs first.
- **AMB-2 Errors**: All listeners always execute. Errors collected. If `error_handler` set: call `error_handler(event_name, listener, exception)` per error, `None` in return slot. If no handler: raise `ListenerError` after all listeners ran.
- **AMB-3 Wildcard**: `on("*", fn)` catches all events. Wildcard listeners called AFTER specific listeners. Wildcard listeners receive `fn(event_name, *args, **kwargs)`.
- **AMB-4 Async**: Sync-only. No async support.
- **AMB-5 Max Listeners**: Default 10/event. Warn via `warnings.warn(MaxListenersExceededWarning(...))` when exceeded. 0=unlimited. Soft cap — don't block.
- **AMB-6 Data Model**: Pass-through args/kwargs. `emit("e", a, b, k=v)` → `fn(a, b, k=v)`. Wildcard: `fn(event_name, a, b, k=v)`.
- **AMB-7 Ordering**: Same priority → FIFO (registration order). Cross priority → lower number first. Stable sort.
- **AMB-8 Returns**: `emit()` returns `list[Any]` in execution order. Errored listeners → `None` in slot.

## Interface Contract (emitter.py)

```python
from typing import Any, Callable, Optional
from eventemitter.types import (
    Subscription, ListenerError, MaxListenersExceededWarning,
    InvalidPriorityError, PRIORITY_DEFAULT, MAX_LISTENERS_DEFAULT,
)

class EventEmitter:
    def __init__(self, max_listeners: int = MAX_LISTENERS_DEFAULT,
                 error_handler: Optional[Callable] = None): ...

    def on(self, event_name: str, listener: Callable, *, priority: int = PRIORITY_DEFAULT) -> Subscription:
        """Register listener. Returns Subscription. Warns if count > max_listeners."""

    def once(self, event_name: str, listener: Callable, *, priority: int = PRIORITY_DEFAULT) -> Subscription:
        """One-time listener. Auto-removed after first call."""

    def off(self, event_name: str, listener: Callable) -> bool:
        """Remove specific listener by reference. Returns True if found."""

    def emit(self, event_name: str, *args: Any, **kwargs: Any) -> list[Any]:
        """Emit event. Returns list of return values. See AMB-2 for error semantics."""

    def listener_count(self, event_name: str) -> int:
        """Count of active listeners for event (excludes wildcard)."""

    def remove_all_listeners(self, event_name: str | None = None) -> int:
        """Remove all (or per-event) listeners. Returns count removed."""

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

## Internal Implementation Notes

- Store listeners per event in a `dict[str, list[_ListenerEntry]]`
- `_ListenerEntry`: internal wrapper holding (subscription, listener, priority, once, registration_order)
- Keep listeners sorted by (priority, registration_order) — use `bisect.insort` or sort on emit
- Wildcard listeners stored separately under key `"*"`
- `emit()` flow: get specific listeners → sort → call each → get wildcard listeners → call each with event_name prepended → collect returns → handle errors

## Your Assignment

| task-id | file | status | notes |
|---------|------|--------|-------|
| emitter | emitter.py | ready | implement full EventEmitter class |
