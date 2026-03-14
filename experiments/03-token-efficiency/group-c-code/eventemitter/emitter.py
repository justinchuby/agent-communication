"""Event emitter core logic.

Owner: Developer B

EventEmitter class: register listeners, emit events, manage subscriptions
with priority ordering, wildcard support, and error handling.
"""

from __future__ import annotations

import bisect
import warnings
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from eventemitter.types import (
    PRIORITY_DEFAULT,
    PRIORITY_MAX,
    PRIORITY_MIN,
    MAX_LISTENERS_DEFAULT,
    InvalidPriorityError,
    ListenerError,
    MaxListenersExceededWarning,
    Subscription,
)

# Wildcard event name — listeners registered on "*" receive all events
_WILDCARD = "*"


@dataclass(order=True)
class _ListenerEntry:
    """Internal wrapper for a registered listener, sortable by (priority, order)."""

    priority: int
    registration_order: int
    subscription: Subscription = field(compare=False)
    listener: Callable[..., Any] = field(compare=False)
    once: bool = field(compare=False)


class EventEmitter:
    """Priority-based event emitter with wildcard support and error handling.

    Usage::

        emitter = EventEmitter()
        sub = emitter.on("data", lambda x: print(x), priority=1)
        results = emitter.emit("data", 42)
        sub.cancel()
    """

    def __init__(
        self,
        max_listeners: int = MAX_LISTENERS_DEFAULT,
        error_handler: Optional[Callable] = None,
    ) -> None:
        self._listeners: dict[str, list[_ListenerEntry]] = {}
        self._max_listeners = max_listeners
        self._error_handler = error_handler
        self._registration_counter = 0

    # ─── Public API ────────────────────────────────────────────────

    def on(
        self,
        event_name: str,
        listener: Callable,
        *,
        priority: int = PRIORITY_DEFAULT,
    ) -> Subscription:
        """Register a listener for an event. Returns a Subscription handle.

        Warns via MaxListenersExceededWarning if listener count exceeds max_listeners.

        Raises:
            InvalidPriorityError: If priority is outside 1–10.
            TypeError: If listener is not callable.
        """
        return self._add_listener(event_name, listener, priority=priority, once=False)

    def once(
        self,
        event_name: str,
        listener: Callable,
        *,
        priority: int = PRIORITY_DEFAULT,
    ) -> Subscription:
        """Register a one-time listener. Auto-removed after first call.

        Raises:
            InvalidPriorityError: If priority is outside 1–10.
            TypeError: If listener is not callable.
        """
        return self._add_listener(event_name, listener, priority=priority, once=True)

    def off(self, event_name: str, listener: Callable) -> bool:
        """Remove a specific listener by reference. Returns True if found and removed."""
        entries = self._listeners.get(event_name)
        if entries is None:
            return False
        for i, entry in enumerate(entries):
            if entry.listener is listener and entry.subscription.active:
                entry.subscription.active = False
                entries.pop(i)
                if not entries:
                    del self._listeners[event_name]
                return True
        return False

    def emit(self, event_name: str, *args: Any, **kwargs: Any) -> list[Any]:
        """Emit an event, calling all registered listeners in priority order.

        Specific listeners are called first, then wildcard listeners.
        Returns a list of return values in execution order.
        Errored listeners produce None in their slot.

        If error_handler is set, it's called per error. Otherwise,
        ListenerError is raised after all listeners have run (if any errored).
        """
        results: list[Any] = []
        errors: list[tuple[str, Callable, Exception]] = []

        # Specific listeners first
        specific = list(self._listeners.get(event_name, []))
        for entry in specific:
            self._call_listener(entry, event_name, args, kwargs, results, errors)

        # Wildcard listeners second (receive event_name as first arg)
        if event_name != _WILDCARD:
            wildcard = list(self._listeners.get(_WILDCARD, []))
            for entry in wildcard:
                self._call_wildcard_listener(entry, event_name, args, kwargs, results, errors)

        # Error handling: raise if no handler set and errors occurred
        if errors and self._error_handler is None:
            raise ListenerError(errors)

        return results

    def listener_count(self, event_name: str) -> int:
        """Count of active listeners for a specific event (excludes wildcard)."""
        entries = self._listeners.get(event_name, [])
        return len([e for e in entries if e.subscription.active])

    def remove_all_listeners(self, event_name: str | None = None) -> int:
        """Remove all listeners, or all listeners for a specific event.

        Returns the count of listeners removed.
        """
        count = 0
        if event_name is not None:
            entries = self._listeners.pop(event_name, [])
            for entry in entries:
                entry.subscription.active = False
                count += 1
        else:
            for entries in self._listeners.values():
                for entry in entries:
                    entry.subscription.active = False
                    count += 1
            self._listeners.clear()
        return count

    @property
    def max_listeners(self) -> int:
        """Per-event listener limit. 0 means unlimited."""
        return self._max_listeners

    @max_listeners.setter
    def max_listeners(self, value: int) -> None:
        self._max_listeners = value

    @property
    def error_handler(self) -> Optional[Callable]:
        """Callback invoked per listener error: handler(event_name, listener, exception)."""
        return self._error_handler

    @error_handler.setter
    def error_handler(self, handler: Optional[Callable]) -> None:
        self._error_handler = handler

    def _remove_subscription(self, sub: Subscription) -> None:
        """Internal: called by Subscription.cancel() to remove from storage."""
        entries = self._listeners.get(sub.event_name)
        if entries is None:
            return
        self._listeners[sub.event_name] = [
            e for e in entries if e.subscription.id != sub.id
        ]
        if not self._listeners[sub.event_name]:
            del self._listeners[sub.event_name]

    # ─── Internal ──────────────────────────────────────────────────

    def _add_listener(
        self,
        event_name: str,
        listener: Callable,
        *,
        priority: int,
        once: bool,
    ) -> Subscription:
        """Core registration logic shared by on() and once()."""
        if not callable(listener):
            raise TypeError(f"listener must be callable, got {type(listener).__name__}")
        if not (PRIORITY_MIN <= priority <= PRIORITY_MAX):
            raise InvalidPriorityError(
                f"Priority must be {PRIORITY_MIN}–{PRIORITY_MAX}, got {priority}"
            )

        sub = Subscription(
            event_name=event_name,
            listener=listener,
            priority=priority,
            once=once,
            _emitter=self,
        )

        order = self._registration_counter
        self._registration_counter += 1

        entry = _ListenerEntry(
            priority=priority,
            registration_order=order,
            subscription=sub,
            listener=listener,
            once=once,
        )

        if event_name not in self._listeners:
            self._listeners[event_name] = []

        bisect.insort(self._listeners[event_name], entry)

        # Warn if max listeners exceeded (0 = unlimited)
        if (
            event_name != _WILDCARD
            and self._max_listeners > 0
            and len(self._listeners[event_name]) > self._max_listeners
        ):
            warnings.warn(
                MaxListenersExceededWarning(
                    f"Event {event_name!r} has {len(self._listeners[event_name])} listeners "
                    f"(max: {self._max_listeners})"
                ),
                stacklevel=3,
            )

        return sub

    def _call_listener(
        self,
        entry: _ListenerEntry,
        event_name: str,
        args: tuple,
        kwargs: dict,
        results: list[Any],
        errors: list[tuple[str, Callable, Exception]],
    ) -> None:
        """Call a specific listener, handling once and errors."""
        if not entry.subscription.active:
            return
        if entry.once:
            entry.subscription.cancel()
        try:
            value = entry.listener(*args, **kwargs)
            results.append(value)
        except Exception as exc:
            results.append(None)
            errors.append((event_name, entry.listener, exc))
            if self._error_handler is not None:
                self._error_handler(event_name, entry.listener, exc)

    def _call_wildcard_listener(
        self,
        entry: _ListenerEntry,
        event_name: str,
        args: tuple,
        kwargs: dict,
        results: list[Any],
        errors: list[tuple[str, Callable, Exception]],
    ) -> None:
        """Call a wildcard listener with event_name prepended to args."""
        if not entry.subscription.active:
            return
        if entry.once:
            entry.subscription.cancel()
        try:
            value = entry.listener(event_name, *args, **kwargs)
            results.append(value)
        except Exception as exc:
            results.append(None)
            errors.append((event_name, entry.listener, exc))
            if self._error_handler is not None:
                self._error_handler(event_name, entry.listener, exc)