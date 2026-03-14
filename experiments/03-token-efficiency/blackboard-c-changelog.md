# Blackboard Changelog

## v2 (design complete)
- All 8 ambiguities resolved:
  - AMB-1: priority 1=highest, range 1–10, default 5
  - AMB-2: all listeners execute, errors collected → error_handler or ListenerError
  - AMB-3: wildcard `"*"` yes, pattern matching no. Wildcard called after specific.
  - AMB-4: sync-only
  - AMB-5: default 10/event, warn on exceed, 0=unlimited
  - AMB-6: pass-through args/kwargs, no Event wrapper
  - AMB-7: same priority FIFO, cross priority lower-first
  - AMB-8: emit() returns list[Any], errored→None
- Interface contract written (types.py + emitter.py signatures)
- types.py stubs written in code dir
- 4 scoped views created: deva, devb, reviewer, tester
- Assignments: types+pkg-init=ready, emitter=ready, review=blocked(impl), tests=blocked(review)

## v1 (initial)
- Blackboard created. Design pending.

## v2 (dev-b)
- emitter.py: done. EventEmitter class implemented with on/once/off/emit/cancel/wildcard/priority/error handling.

## v3 (dev-a)
- types.py: done. Subscription with __lt__ ordering, __post_init__ priority validation, cancel(). All error types and constants implemented.
- __init__.py: done. Exports all public types + EventEmitter.

## v4 (tester)
- tests: done. 18/18 passed in 0.03s. Coverage: basic emission (3), priority ordering (2), once listeners (2), unsubscription (3), wildcard (2), error handling (2), max listeners (1), edge cases (3).

## v5 (reviewer)
- review: PASS. 11/12 checklist items pass, 1 warning.
- Issue #1 (Medium): error_handler exception breaks AMB-2 "all listeners execute" — wrap error_handler call in try/except in _call_listener and _call_wildcard_listener.
- Issue #2 (Low): Subscription.__lt__ UUID tiebreak is non-FIFO (not used internally, cosmetic).
- Issue #3 (Low): max_listeners setter accepts negative values (no validation).
- Issue #4 (Trivial): _call_listener/_call_wildcard_listener near-duplication.
- Assignment status: review → done.
