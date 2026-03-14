# Group C — Reviewer Scoped View

## Task
Event emitter library. Review ALL code files.
Code dir: experiments/03-token-efficiency/group-c-code/eventemitter/

## All Design Decisions

| ID | Decision |
|----|----------|
| AMB-1 | Priority 1=highest, range 1–10, default 5 |
| AMB-2 | All listeners execute. Errors collected. error_handler callback or raise ListenerError. |
| AMB-3 | `"*"` wildcard catches all events (called AFTER specific). No pattern matching. Wildcard gets `(event_name, *args, **kwargs)`. |
| AMB-4 | Sync-only. No async. |
| AMB-5 | Default 10/event. `MaxListenersExceededWarning` via warnings.warn(). 0=unlimited. Soft cap. |
| AMB-6 | Pass-through args/kwargs. No typed Event object. |
| AMB-7 | Same priority → FIFO. Cross priority → lower first. Stable sort. |
| AMB-8 | `emit()` returns `list[Any]`. Errored → `None` in slot. Empty list if no listeners. |

## Interface Contract

### types.py (Dev A)
- `EventEmitterError(Exception)` — base
- `ListenerError(EventEmitterError)` — `.errors: list[tuple[str, Callable, Exception]]`
- `MaxListenersExceededWarning(UserWarning)`
- `InvalidPriorityError(EventEmitterError, ValueError)`
- `Subscription` dataclass: id, event_name, listener, priority, once, active, _emitter. Has `cancel() -> bool`.
- Constants: `PRIORITY_MIN=1`, `PRIORITY_MAX=10`, `PRIORITY_DEFAULT=5`, `MAX_LISTENERS_DEFAULT=10`

### emitter.py (Dev B)
- `EventEmitter(max_listeners=10, error_handler=None)`
- `.on(event_name, listener, *, priority=5) -> Subscription`
- `.once(event_name, listener, *, priority=5) -> Subscription`
- `.off(event_name, listener) -> bool`
- `.emit(event_name, *args, **kwargs) -> list[Any]`
- `.listener_count(event_name) -> int`
- `.remove_all_listeners(event_name=None) -> int`
- `.max_listeners` property (r/w)
- `.error_handler` property (r/w)
- `._remove_subscription(sub)` — internal, called by Subscription.cancel()

### __init__.py (Dev A)
- Re-exports: EventEmitter, Subscription, all errors, all constants

## Review Checklist
- [ ] types.py: Subscription.cancel() calls _emitter._remove_subscription()
- [ ] types.py: ListenerError.errors has correct tuple shape
- [ ] types.py: InvalidPriorityError inherits both EventEmitterError + ValueError
- [ ] emitter.py: priority validated on on()/once()
- [ ] emitter.py: wildcard listeners called AFTER specific
- [ ] emitter.py: wildcard receives event_name as first arg
- [ ] emitter.py: once() auto-removes after first call
- [ ] emitter.py: error_handler semantics match AMB-2
- [ ] emitter.py: max_listeners warning (not block)
- [ ] emitter.py: emit() returns list in execution order
- [ ] emitter.py: FIFO within same priority
- [ ] __init__.py: all public types exported

## All Assignments

| task-id | file | owner | status | notes |
|---------|------|-------|--------|-------|
| design | — | architect | done | all 8 resolved |
| types | types.py | dev-a | ready | |
| pkg-init | __init__.py | dev-a | ready | |
| emitter | emitter.py | dev-b | ready | |
| review | all | reviewer | blocked(impl) | |
| tests | test_emitter.py | tester | blocked(review) | |

## Findings

(post findings here during review)
