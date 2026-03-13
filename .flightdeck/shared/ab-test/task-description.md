# A/B Test: AECP vs English Communication

## Task: Build a Python URL Shortener Library

Build a working URL shortener library in Python. The library must:

1. **Generate short codes** for URLs (base62, 6 characters)
2. **Store and resolve** short codes back to original URLs
3. **Track click statistics** (click count, last accessed timestamp)
4. **Handle edge cases**: duplicate URLs reuse existing codes, expired URLs, invalid inputs
5. **Pass all tests** (provided test file has 18 test cases)

### Architecture (mandatory for both groups)

```
urlshort/
├── __init__.py      # Package init — exports public API
├── models.py        # Data models (architect designs, dev A implements)
├── storage.py       # Storage backend (dev B implements)
├── shortener.py     # Core logic (dev A implements)
tests/
├── __init__.py
└── test_shortener.py  # Integration tests (tester implements)
```

### Coordination Requirements

This task is designed to require inter-developer coordination:

- **Dev A** owns `models.py` + `shortener.py`. The shortener depends on the storage interface.
- **Dev B** owns `storage.py`. Must implement the `StorageBackend` protocol that Dev A's code calls.
- **The architect** must define the `StorageBackend` interface so both developers can work in parallel.
- **The reviewer** reviews all code before the tester runs tests.
- **The tester** writes `test_shortener.py` and runs the full suite.

### Specifications

**Short code generation:**
- Base62 alphabet: `0-9a-zA-Z`
- Length: 6 characters
- Deterministic for same URL (hash-based, not random)
- Collision resolution: append counter suffix

**StorageBackend protocol (architect must define):**
```python
class StorageBackend(Protocol):
    def save(self, record: URLRecord) -> None: ...
    def get_by_code(self, code: str) -> URLRecord | None: ...
    def get_by_url(self, url: str) -> URLRecord | None: ...
    def delete(self, code: str) -> bool: ...
    def increment_clicks(self, code: str) -> None: ...
    def list_all(self) -> list[URLRecord]: ...
```

**URLRecord model:**
```python
@dataclass
class URLRecord:
    code: str               # 6-char base62 short code
    url: str                # Original URL
    created_at: datetime    # Creation timestamp
    click_count: int = 0    # Number of times resolved
    last_accessed: datetime | None = None  # Last resolve timestamp
    expires_at: datetime | None = None     # Optional expiry
```

**Shortener public API:**
```python
class URLShortener:
    def __init__(self, storage: StorageBackend): ...
    def shorten(self, url: str, expires_in: timedelta | None = None) -> str: ...
    def resolve(self, code: str) -> str: ...  # raises NotFoundError or ExpiredError
    def get_stats(self, code: str) -> URLRecord: ...
    def delete(self, code: str) -> bool: ...
```

**Error types:**
- `ShortenerError` (base)
- `NotFoundError(ShortenerError)` — code doesn't exist
- `ExpiredError(ShortenerError)` — code exists but expired
- `InvalidURLError(ShortenerError)` — malformed URL

### Success Criteria

- All 18 tests pass
- Code is clean, typed, documented
- No hardcoded values — configurable via constructor params
- Error handling is complete

### What's Provided

- Stub files with docstrings (in `codebase/`)
- This task description
- Role assignments

### Roles

| Role | Responsibilities |
|------|-----------------|
| Architect | Define interfaces, review design decisions, resolve conflicts |
| Developer A | Implement `models.py` + `shortener.py` |
| Developer B | Implement `storage.py` + `__init__.py` |
| Reviewer | Review all code for correctness, style, completeness |
| Tester | Write tests, run suite, report results |
