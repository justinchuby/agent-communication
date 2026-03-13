"""In-memory storage backend implementing StorageBackend protocol.

Owner: Developer B

Implement:
    class InMemoryStorage:
        - Internal dict storage keyed by short code
        - Secondary index by URL for dedup lookups
        - All 6 StorageBackend methods
        - Thread-safe (not required but bonus)

Dependencies: urlshort.models (URLRecord, StorageBackend)
"""

from __future__ import annotations


# TODO: Implement InMemoryStorage per spec
