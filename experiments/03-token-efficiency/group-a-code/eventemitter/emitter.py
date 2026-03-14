"""EventEmitter — core event registration, emission, and lifecycle management.

Owner: Developer B

Provides:
    EventEmitter: Register listeners with priority ordering, emit events,
    manage subscriptions, and handle listener errors.
"""

from __future__ import annotations

import warnings
from collections import defaultdict

from eventemitter.types import (
    EmitError,
    ErrorHandler,
    Listener,
    MaxListenersWarning,
    Subscription,
)


class EventEmitter:
    """A priority-based synchronous event emitter.

    Listeners are called in priority order (lower number = higher priority).
    Within the same priority, listeners are called in registration order (FIFO).

    Args:
        max_listeners: Optional per-event listener cap. When exceeded, a
            ``MaxListenersWarning`` is issued (not an error).
        error_handler: Optional callback ``(event, exception, listener)`` invoked
            when a listener raises. If not set, exceptions are collected and
            re-raised as an ``EmitError`` after all listeners run.
    """

    def __init__(
        self,
        max_listeners: int | None = None,
        error_handler: ErrorHandler | None = None,
    ) -> None:
        self._listeners: dict[str, list[Subscription]] = defaultdict(list)
        self._max_listeners = max_listeners
        self._error_handler = error_handler

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def on(
        self,
        event: str,
        listener: Listener,
        priority: int = 0,
    ) -> Subscription:
        """Register a listener for *event*. Returns a cancellable Subscription."""
        return self._add_listener(event, listener, priority, once=False)

    def once(
        self,
        event: str,
        listener: Listener,
        priority: int = 0,
    ) -> Subscription:
        """Register a one-shot listener that auto-removes after first call."""
        return self._add_listener(event, listener, priority, once=True)

    # ------------------------------------------------------------------
    # Emission
    # ------------------------------------------------------------------

    def emit(self, event: str, *args: object, **kwargs: object) -> None:
        """Emit *event*, calling all registered listeners in priority order.

        Listeners that raise are handled by ``error_handler`` if set.
        Otherwise, exceptions are collected and raised together as ``EmitError``
        after all listeners have been called.
        """
        # Snapshot the listener list so mutations during emit are safe
        subscriptions = list(self._listeners.get(event, []))
        errors: list[Exception] = []
        to_remove: list[Subscription] = []

        for sub in subscriptions:
            if sub._cancelled:
                continue
            try:
                sub.listener(*args, **kwargs)
            except Exception as exc:
                if self._error_handler is not None:
                    self._error_handler(event, exc, sub.listener)
                else:
                    errors.append(exc)
            finally:
                if sub.once and not sub._cancelled:
                    to_remove.append(sub)

        # Remove once-listeners after full iteration
        for sub in to_remove:
            sub.cancel()

        if errors:
            raise EmitError(event, errors)

    # ------------------------------------------------------------------
    # Unsubscription
    # ------------------------------------------------------------------

    def off(self, event: str, listener: Listener) -> bool:
        """Remove the first subscription matching *event* and *listener*.

        Returns True if a listener was removed, False otherwise.
        """
        subs = self._listeners.get(event, [])
        for sub in subs:
            if sub.listener is listener and not sub._cancelled:
                sub.cancel()
                return True
        return False

    def remove_all_listeners(self, event: str | None = None) -> None:
        """Remove all listeners for *event*, or all events if None."""
        if event is not None:
            subs = self._listeners.pop(event, [])
            for sub in subs:
                sub._cancelled = True
        else:
            for subs in self._listeners.values():
                for sub in subs:
                    sub._cancelled = True
            self._listeners.clear()

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def listener_count(self, event: str) -> int:
        """Return the number of active listeners for *event*."""
        return sum(
            1 for sub in self._listeners.get(event, []) if not sub._cancelled
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _add_listener(
        self,
        event: str,
        listener: Listener,
        priority: int,
        once: bool,
    ) -> Subscription:
        """Insert a subscription in sorted-priority position (stable FIFO)."""
        sub = Subscription(
            event=event,
            listener=listener,
            priority=priority,
            once=once,
        )
        sub._cancel_fn = lambda: self._remove_subscription(event, sub)

        subs = self._listeners[event]

        # Binary-style insertion to maintain sorted order (lower priority first)
        insert_idx = len(subs)
        for i, existing in enumerate(subs):
            if existing.priority > priority:
                insert_idx = i
                break
        subs.insert(insert_idx, sub)

        # Warn if max_listeners exceeded
        if self._max_listeners is not None:
            active = self.listener_count(event)
            if active > self._max_listeners:
                warnings.warn(
                    f"Event {event!r} has {active} listeners "
                    f"(max_listeners={self._max_listeners})",
                    MaxListenersWarning,
                    stacklevel=3,
                )

        return sub

    def _remove_subscription(self, event: str, sub: Subscription) -> None:
        """Remove a specific subscription from the internal list."""
        subs = self._listeners.get(event, [])
        try:
            subs.remove(sub)
        except ValueError:
            pass
        # Clean up empty event keys
        if not subs and event in self._listeners:
            del self._listeners[event]
