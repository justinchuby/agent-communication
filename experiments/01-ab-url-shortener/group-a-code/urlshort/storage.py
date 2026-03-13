"""In-memory storage backend implementing StorageBackend protocol.

Owner: Developer B
"""

from __future__ import annotations

import threading
from copy import deepcopy
from datetime import datetime, timezone

from urlshort.models import URLRecord


class InMemoryStorage:
    """Thread-safe in-memory storage for URL records.

    Uses a primary dict keyed by short code and a secondary index
    keyed by original URL for fast deduplication lookups.
    """

    def __init__(self) -> None:
        self._by_code: dict[str, URLRecord] = {}
        self._by_url: dict[str, URLRecord] = {}
        self._lock = threading.Lock()

    def save(self, record: URLRecord) -> None:
        """Store a URLRecord, indexed by both code and URL.

        If the code already exists with a different URL, the old URL's
        secondary index entry is removed to prevent stale dedup lookups.
        """
        with self._lock:
            old = self._by_code.get(record.code)
            if old is not None and old.url != record.url:
                self._by_url.pop(old.url, None)
            self._by_code[record.code] = record
            self._by_url[record.url] = record

    def get_by_code(self, code: str) -> URLRecord | None:
        """Look up a record by its short code."""
        with self._lock:
            record = self._by_code.get(code)
            return deepcopy(record) if record is not None else None

    def get_by_url(self, url: str) -> URLRecord | None:
        """Look up a record by its original URL."""
        with self._lock:
            record = self._by_url.get(url)
            return deepcopy(record) if record is not None else None

    def delete(self, code: str) -> bool:
        """Remove a record by short code. Returns True if it existed."""
        with self._lock:
            record = self._by_code.pop(code, None)
            if record is None:
                return False
            self._by_url.pop(record.url, None)
            return True

    def increment_clicks(self, code: str) -> None:
        """Increment click count and update last_accessed timestamp."""
        with self._lock:
            record = self._by_code.get(code)
            if record is not None:
                record.click_count += 1
                record.last_accessed = datetime.now(timezone.utc)

    def list_all(self) -> list[URLRecord]:
        """Return a list of all stored records (deep copies)."""
        with self._lock:
            return [deepcopy(r) for r in self._by_code.values()]
