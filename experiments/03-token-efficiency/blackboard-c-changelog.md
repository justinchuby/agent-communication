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
