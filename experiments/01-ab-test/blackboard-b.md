# Group B Blackboard

## Task
status: in_progress
spec: .flightdeck/shared/ab-test/task-description.md
target_tests: 18/18

## Interface Contract
```python
# SIGNED OFF — DO NOT MODIFY without architect approval

class ShortenerError(Exception): ...
class NotFoundError(ShortenerError): ...
class ExpiredError(ShortenerError): ...
class InvalidURLError(ShortenerError): ...

@dataclass
class URLRecord:
    code: str                              # 6-char base62
    url: str                               # original URL
    created_at: datetime
    click_count: int = 0
    last_accessed: datetime | None = None
    expires_at: datetime | None = None

class StorageBackend(Protocol):
    def save(self, record: URLRecord) -> None: ...
    def get_by_code(self, code: str) -> URLRecord | None: ...
    def get_by_url(self, url: str) -> URLRecord | None: ...
    def delete(self, code: str) -> bool: ...
    def increment_clicks(self, code: str) -> None: ...  # +1 click_count, set last_accessed=now
    def list_all(self) -> list[URLRecord]: ...

class URLShortener:
    def __init__(self, storage: StorageBackend, code_length: int = 6): ...
    def shorten(self, url: str, expires_in: timedelta | None = None) -> str: ...
    def resolve(self, code: str) -> str: ...   # raises NotFoundError | ExpiredError
    def get_stats(self, code: str) -> URLRecord: ...  # raises NotFoundError
    def delete(self, code: str) -> bool: ...
```
contract_status: done

## Assignments

| task-id | file | owner | status | notes |
|---------|------|-------|--------|-------|
| design | M:MOD | architect | done | interfaces written to M:MOD |
| models | M:MOD | dev-a | done | architect wrote interfaces; verified imports |
| shortener | M:SHR | dev-a | done | URLShortener: shorten/resolve/get_stats/delete |
| storage | M:STO | dev-b | done | InMemoryStorage — 6 methods, thread-safe, dual index |
| pkg-init | M:INI | dev-b | done | exports all public API (needs M:SHR to import) |
| review | all | reviewer | done | PASS — no blocking issues |
| tests | T:TST | tester | done | 18/18 passed |
| fix | — | dev-a,dev-b | blocked(tests) | fix any failures |

## Findings
- M:MOD: unused `field` import (line 9) — non-blocking lint issue
- M:SHR: `_generate_unique_code` has no retry cap — acceptable for scope
- M:STO: `list_all` returns mutable refs to internal records — acceptable for in-memory scope
- All files: correct type hints, spec-compliant interfaces, proper error handling

## Metrics
messages_sent: 1
clarifications: 0
