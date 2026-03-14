# Event Emitter Library — Task Specification

Build a Python event emitter library. Users register listeners for named events, emit events to trigger listeners, and manage subscriptions with priority, filtering, and error handling.

## Module Structure
```
eventemitter/
├── __init__.py         # Public API exports
├── types.py            # Event, Listener, Subscription types
├── emitter.py          # EventEmitter core logic
tests/
├── __init__.py
└── test_emitter.py     # 15-20 test cases
```

## Requirements
- Pure Python, standard library only
- Python 3.10+
- Type hints on all public APIs
- 15–20 test cases covering core functionality

## Core Features
1. **Event registration**: `emitter.on(event_name, listener_fn)` — returns a subscription handle
2. **Event emission**: `emitter.emit(event_name, *args, **kwargs)` — triggers all registered listeners
3. **Unsubscription**: `subscription.cancel()` or `emitter.off(event_name, listener_fn)`
4. **One-time listeners**: `emitter.once(event_name, listener_fn)` — auto-removes after first call
5. **Priority ordering**: Listeners called in priority order
6. **Error handling**: Define how listener exceptions are handled
7. **Listener count**: `emitter.listener_count(event_name)` — returns count
8. **Remove all**: `emitter.remove_all_listeners(event_name=None)` — clears listeners

## Design Decisions (for the Architect to resolve)
The following are deliberately unspecified. The Architect must decide:

1. **Priority direction**: Is priority=1 highest or lowest?
2. **Error handling**: Swallow silently? Collect and re-raise? Call an error handler callback?
3. **Wildcard support**: Does `on("*", fn)` catch all events? Pattern matching like `user.*`?
4. **Async support**: Sync-only? Optional async? Both?
5. **Max listeners**: Per-event cap? Global cap? Warning threshold?
6. **Event data model**: Positional args? Keyword args? Typed Event object?
7. **Listener ordering**: Within same priority: FIFO? LIFO? Undefined?
8. **Return values**: Do listeners return values? How are they collected?
