# Task: Build a Python Task Queue Library

Build a task queue library that lets users submit tasks, schedule them by priority, handle failures, and track status.

## What It Should Do

The library manages a queue of tasks. Users submit callable tasks with a priority level. The queue processes tasks in priority order — higher priority tasks should run first. Failed tasks should be retried. Tasks shouldn't run forever. The queue should support running multiple tasks at the same time.

## Components

Build these three modules:

### 1. Models (`taskqueue/models.py`) — Developer A

Define the data structures for the task queue:

- A **Task** that wraps a callable with metadata: an ID, a name, the callable itself, the priority level, when it was submitted, its current status, how many times it's been attempted, and an optional result or error message.

- A **TaskResult** that holds the outcome of running a task: the task ID, whether it succeeded, the return value if it succeeded, the error message if it failed, and how long it took.

- Appropriate error types for the library.

- Tasks go through several stages as they are processed. Make sure the status tracking is clear.

### 2. Queue Engine (`taskqueue/engine.py`) — Developer B

The core queue processing engine:

- Accept submitted tasks and queue them by priority.
- Process tasks: pull the highest priority task, execute it, handle the result.
- If a task fails, retry it according to the retry policy. Use some kind of backoff between retries.
- If a task takes too long, it should be cancelled or timed out.
- Support running multiple tasks concurrently — decide on an appropriate concurrency model.
- Provide a way to start and stop the queue processor.
- Let users check on the status of their submitted tasks.

### 3. Tests (`tests/test_queue.py`) — Tester

Write tests covering the major behaviors. Think about:
- Basic submit and execute
- Priority ordering (does higher priority actually run first?)
- Retry on failure (does it retry the right number of times?)
- Timeout handling
- Concurrent execution
- Status tracking through the lifecycle
- Edge cases (empty queue, duplicate IDs, invalid priorities)

Aim for 15-20 test cases.

## Architecture

```
taskqueue/
├── __init__.py    # Package init — export public API
├── models.py      # Task, TaskResult, error types, status tracking
├── engine.py      # Queue engine, scheduling, retry, concurrency
tests/
├── __init__.py
└── test_queue.py  # All tests
```

## Requirements

- Pure Python (stdlib only — no external dependencies)
- Should work with Python 3.10+
- Clean error handling
- Type hints on public API

## Roles

| Role | Owns |
|------|------|
| Architect | Design decisions — resolve any ambiguities in this spec |
| Developer A | `models.py` + `__init__.py` |
| Developer B | `engine.py` |
| Reviewer | Review all code |
| Tester | `test_queue.py` — write and run tests |
