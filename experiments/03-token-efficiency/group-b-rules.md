# Group B Rules — AECP v1 (Monolithic Blackboard)

## Protocol
- Shared blackboard: experiments/03-token-efficiency/blackboard-b.md
- Architect populates ALL design decisions and interface contract on the blackboard
- All agents read the FULL blackboard when checking status
- Structured messages only: DONE(component), VERDICT(pass|fail), BUG(id, severity)
- Message budget: ≤5 per agent
- Silence = working (no progress updates)

## Your Team
- Architect: Fills blackboard design decisions + interface contract
- Dev A: Implements types.py + __init__.py per blackboard spec
- Dev B: Implements emitter.py per blackboard spec
- Reviewer: Reviews code, posts findings to blackboard
- Tester: Writes and runs 15-20 tests

## Code Directory
experiments/03-token-efficiency/group-b-code/

## Workflow
1. Architect reads task spec → fills blackboard → sends DONE(design)
2. Dev A reads full blackboard → implements types.py + __init__.py → updates blackboard → sends DONE(types+init)
3. Dev B reads full blackboard → implements emitter.py → updates blackboard → sends DONE(emitter)
4. Reviewer reads full blackboard + all code → posts findings → sends VERDICT
5. Tester reads full blackboard + all code → writes tests → runs them → sends VERDICT
