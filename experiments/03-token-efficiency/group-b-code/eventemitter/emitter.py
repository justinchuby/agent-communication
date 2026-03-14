"""Event emitter core logic.

Owner: Developer B

Design decisions (from architect blackboard):
- Priority 1 = highest (called first), 10 = lowest. Same priority -> FIFO.
- Wildcard "*" catches all events, runs AFTER event-specific listeners.
- Error handling: configurable callback. No handler -> exception propagates, rest skipped.
- emit() returns int (number of listeners called). Return values discarded.
- Max listeners: default 10 per event, warning (not error). 0 = unlimited.
- Sync-only. Pass-through *args/**kwargs.
"""

from __future__ import annotations

import warnings
from typing import Any, Optional

from .types import (
    ErrorHandler,
    Listener,
    ListenerFn,
    MaxListenersExceededWarning,
    Subscription,
)

_WILDCARD = "*"


class EventEmitter:
    """Priority-ordered event emitter with wildcard support and error handling."""

    def __init__(
        self,
        max_listeners: int = 10,
        error_handler: Optional[ErrorHandler] = None,
    ) -> None:
        self._listeners: dict[str, list[Listener]] = {}
        self._max_listeners = max_listeners
        self.error_handler = error_handler
        self._sequence = 0  # global counter for FIFO within same priority

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def on(
        self,
        event_name: str,
        listener: ListenerFn,
        priority: int = 5,
    ) -> Subscription:
        """Register *listener* for *event_name*. Returns a Subscription handle."""
        return self._add_listener(event_name, listener, priority, once=False)

    def once(
        self,
        event_name: str,
        listener: ListenerFn,
        priority: int = 5,
    ) -> Subscription:
        """Register a one-time *listener* -- auto-removed after first invocation."""
        return self._add_listener(event_name, listener, priority, once=True)

    def off(self, event_name: str, listener: ListenerFn) -> bool:
        """Remove the first registration of *listener* for *event_name*.

        Returns True if a listener was removed, False if not found.
        """
        entries = self._listeners.get(event_name, [])
        for i, entry in enumerate(entries):
            if entry.callback is listener:
                entries.pop(i)
                return True
        return False

    def emit(self, event_name: str, *args: Any, **kwargs: Any) -> int:
        """Emit *event_name*, calling listeners in priority order.

        Wildcard listeners run after event-specific listeners.
        Returns the number of listeners called.
        """
        specific = sorted(self._listeners.get(event_name, []))
        wildcard = (
            sorted(self._listeners.get(_WILDCARD, []))
            if event_name != _WILDCARD
            else []
        )

        called = 0
        once_to_remove: list[tuple[str, str]] = []

        for event_key, entries in ((event_name, specific), (_WILDCARD, wildcard)):
            for entry in entries:
                try:
                    entry.callback(*args, **kwargs)
                except Exception as exc:
                    called += 1
                    if entry.once:
                        once_to_remove.append((event_key, entry.listener_id))
                    if self.error_handler is not None:
                        self.error_handler(event_name, exc)
                        continue
                    # No handler -- clean up once listeners, then propagate
                    self._remove_by_ids(once_to_remove)
                    raise
                else:
                    called += 1
                    if entry.once:
                        once_to_remove.append((event_key, entry.listener_id))

        self._remove_by_ids(once_to_remove)
        return called

    def listener_count(self, event_name: str) -> int:
        """Return number of listeners registered for *event_name*."""
        return len(self._listeners.get(event_name, []))

    def remove_all_listeners(self, event_name: Optional[str] = None) -> None:
        """Remove all listeners for *event_name*, or all events if None."""
        if event_name is not None:
            self._listeners.pop(event_name, None)
        else:
            self._listeners.clear()

    @property
    def max_listeners(self) -> int:
        """Per-event listener cap. 0 means unlimited."""
        return self._max_listeners

    @max_listeners.setter
    def max_listeners(self, value: int) -> None:
        self._max_listeners = value

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _add_listener(
        self,
        event_name: str,
        callback: ListenerFn,
        priority: int,
        once: bool,
    ) -> Subscription:
        if not (1 <= priority <= 10):
            raise ValueError(f"Priority must be 1-10, got {priority}")

        self._sequence += 1
        entry = Listener(
            callback=callback,
            priority=priority,
            once=once,
            _sequence=self._sequence,
        )

        bucket = self._listeners.setdefault(event_name, [])
        bucket.append(entry)

        if self._max_listeners > 0 and len(bucket) > self._max_listeners:
            warnings.warn(
                f"Max listeners ({self._max_listeners}) exceeded for event "
                f"'{event_name}'. Current count: {len(bucket)}.",
                MaxListenersExceededWarning,
                stacklevel=3,
            )

        def cancel() -> None:
            entries = self._listeners.get(event_name, [])
            for i, e in enumerate(entries):
                if e.listener_id == entry.listener_id:
                    entries.pop(i)
                    return

        return Subscription(
            event_name=event_name,
            listener_id=entry.listener_id,
            _cancel_fn=cancel,
        )

    def _remove_by_ids(self, ids: list[tuple[str, str]]) -> None:
        """Remove listeners identified by (event_name, listener_id) pairs."""
        for event_key, listener_id in ids:
            entries = self._listeners.get(event_key, [])
            for i, e in enumerate(entries):
                if e.listener_id == listener_id:
                    entries.pop(i)
                    break
