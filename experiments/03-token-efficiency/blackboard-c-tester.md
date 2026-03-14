# Group C — Tester Scoped View

## Task
Event emitter library. You own: `tests/test_emitter.py`
Code dir: experiments/03-token-efficiency/group-c-code/

## Interface Contract (what to test)

```python
from eventemitter import EventEmitter, Subscription, ListenerError, InvalidPriorityError, MaxListenersExceededWarning

# Create emitter
emitter = EventEmitter(max_listeners=10, error_handler=None)

# Register listeners
sub = emitter.on("event", listener_fn, priority=5)   # returns Subscription
sub = emitter.once("event", listener_fn, priority=5)  # one-time, auto-removes

# Emit
results = emitter.emit("event", *args, **kwargs)  # returns list[Any] of return values

# Unsubscribe
sub.cancel()                               # returns bool
emitter.off("event", listener_fn)          # returns bool
emitter.remove_all_listeners("event")      # returns int (count removed)
emitter.remove_all_listeners()             # removes ALL, returns int

# Query
count = emitter.listener_count("event")    # int

# Wildcard: on("*", fn) catches all events — fn receives (event_name, *args, **kwargs)
# Priority: 1=highest (runs first), 10=lowest, default=5
# Same priority: FIFO order
# Errors: all listeners run. With error_handler: errors caught. Without: ListenerError raised.
# Once: auto-removed after first call
# Max listeners: warns (MaxListenersExceededWarning) but doesn't block
```

## Assignment Statuses

| task-id | owner | status |
|---------|-------|--------|
| design | architect | done |
| types | dev-a | ready |
| pkg-init | dev-a | ready |
| emitter | dev-b | ready |
| review | reviewer | blocked(impl) |
| tests | tester | blocked(review) |
