"""In-memory storage backend implementing StorageBackend protocol.

Owner: Developer B
Dependencies: urlshort.models (URLRecord)
"""

from __future__ import annotations

import threading
from datetime import datetime, timezone

from urlshort.models import URLRecord


class InMemoryStorage:
    """Thread-safe in-memory implementation of StorageBackend.

    Uses a primary dict keyed by short code and a secondary index
    keyed by URL for O(1) dedup lookups.
    """

    def __init__(self) -> None:
        self._by_code: dict[str, URLRecord] = {}
        self._by_url: dict[str, str] = {}  # url -> code
        self._lock = threading.Lock()

    def save(self, record: URLRecord) -> None:
        """Persist a URLRecord. Overwrites if code already exists."""
        with self._lock:
            old = self._by_code.get(record.code)
            if old is not None:
                self._by_url.pop(old.url, None)
            self._by_code[record.code] = record
            self._by_url[record.url] = record.code

    def get_by_code(self, code: str) -> URLRecord | None:
        """Return the record for *code*, or None if not found."""
        with self._lock:
            return self._by_code.get(code)

    def get_by_url(self, url: str) -> URLRecord | None:
        """Return existing record for *url* (dedup lookup), or None."""
        with self._lock:
            code = self._by_url.get(url)
            if code is None:
                return None
            return self._by_code.get(code)

    def delete(self, code: str) -> bool:
        """Delete the record for *code*. Return True if deleted, False if not found."""
        with self._lock:
            record = self._by_code.pop(code, None)
            if record is None:
                return False
            self._by_url.pop(record.url, None)
            return True

    def increment_clicks(self, code: str) -> None:
        """Increment click_count by 1 and set last_accessed to now."""
        with self._lock:
            record = self._by_code.get(code)
            if record is None:
                return
            record.click_count += 1
            record.last_accessed = datetime.now(timezone.utc)

    def list_all(self) -> list[URLRecord]:
        """Return all stored records."""
        with self._lock:
            return list(self._by_code.values())
