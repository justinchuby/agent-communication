"""EventEmitter — core event emitter implementation.

Implements all 6 public methods + max_listeners property per interface contract.
"""

from __future__ import annotations

import warnings
from collections import defaultdict
from typing import Any

from eventemitter.types import (
    ErrorHandler,
    EventEmitterError,
    Listener,
    ListenerFn,
    MaxListenersExceededWarning,
    Subscription,
)


class EventEmitter:
    """Synchronous event emitter with priority ordering and error handling."""

    def __init__(
        self,
        max_listeners: int = 10,
        error_handler: ErrorHandler | None = None,
    ) -> None:
        self._max_listeners = max_listeners
        self._error_handler = error_handler
        self._listeners: dict[str, list[Listener]] = defaultdict(list)
        self._seq = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def on(
        self,
        event: str,
        fn: ListenerFn,
        priority: int = 0,
    ) -> Subscription:
        """Register a listener for *event*. Returns a Subscription handle."""
        listener = Listener(fn=fn, priority=priority, once=False, _seq=self._next_seq())
        self._add_listener(event, listener)
        return Subscription(event=event, listener=listener, _emitter=self)

    def once(
        self,
        event: str,
        fn: ListenerFn,
        priority: int = 0,
    ) -> Subscription:
        """Register a one-time listener for *event*."""
        listener = Listener(fn=fn, priority=priority, once=True, _seq=self._next_seq())
        self._add_listener(event, listener)
        return Subscription(event=event, listener=listener, _emitter=self)

    def emit(self, event: str, *args: Any, **kwargs: Any) -> int:
        """Emit *event*, calling all listeners in priority order.

        Returns the number of listeners called.
        If a listener raises, behaviour depends on error_handler:
        - With error_handler: call it, continue to next listener.
        - Without: collect exceptions, finish all listeners, then raise the first.
        """
        listeners = list(self._listeners.get(event, []))
        if not listeners:
            return 0

        errors: list[Exception] = []
        called = 0
        to_remove: list[Listener] = []

        for listener in listeners:
            try:
                listener.fn(*args, **kwargs)
                called += 1
            except Exception as exc:
                called += 1
                if self._error_handler is not None:
                    self._error_handler(event, exc, listener.fn)
                else:
                    errors.append(exc)

            if listener.once:
                to_remove.append(listener)

        for listener in to_remove:
            self._remove_listener(event, listener)

        if errors:
            raise errors[0]

        return called

    def off(self, event: str, fn: ListenerFn) -> bool:
        """Remove the first listener matching *fn* for *event*.

        Returns True if a listener was removed, False otherwise.
        """
        listeners = self._listeners.get(event, [])
        for i, listener in enumerate(listeners):
            if listener.fn is fn:
                listeners.pop(i)
                if not listeners:
                    self._listeners.pop(event, None)
                return True
        return False

    def remove_all_listeners(self, event: str | None = None) -> None:
        """Remove all listeners for *event*, or all events if None."""
        if event is None:
            self._listeners.clear()
        else:
            self._listeners.pop(event, None)

    def listener_count(self, event: str) -> int:
        """Return the number of listeners registered for *event*."""
        return len(self._listeners.get(event, []))

    @property
    def max_listeners(self) -> int:
        return self._max_listeners

    @max_listeners.setter
    def max_listeners(self, value: int) -> None:
        self._max_listeners = value

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _next_seq(self) -> int:
        seq = self._seq
        self._seq += 1
        return seq

    def _add_listener(self, event: str, listener: Listener) -> None:
        """Insert listener in sorted position and check max_listeners."""
        listeners = self._listeners[event]
        listeners.append(listener)
        listeners.sort(key=lambda l: (l.priority, l._seq))

        if self._max_listeners > 0 and len(listeners) > self._max_listeners:
            warnings.warn(
                f"Event '{event}' has {len(listeners)} listeners "
                f"(max: {self._max_listeners})",
                MaxListenersExceededWarning,
                stacklevel=3,
            )

    def _remove_listener(self, event: str, listener: Listener) -> None:
        """Remove a specific Listener object."""
        listeners = self._listeners.get(event, [])
        try:
            listeners.remove(listener)
        except ValueError:
            pass
        if not listeners:
            self._listeners.pop(event, None)
