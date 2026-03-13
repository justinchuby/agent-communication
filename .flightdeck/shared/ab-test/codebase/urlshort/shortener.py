"""Core URL shortener logic.

Owner: Developer A

Implement:
    class URLShortener:
        __init__(self, storage: StorageBackend, code_length: int = 6)
        shorten(self, url: str, expires_in: timedelta | None = None) -> str
            - Validate URL (must start with http:// or https://)
            - Check for existing code via storage.get_by_url()
            - Generate base62 hash code (hashlib.sha256 → base62 → truncate)
            - Handle collisions by appending counter
            - Store URLRecord and return code
        resolve(self, code: str) -> str
            - Lookup via storage.get_by_code()
            - Raise NotFoundError if missing
            - Raise ExpiredError if expired
            - Increment click count + update last_accessed
            - Return original URL
        get_stats(self, code: str) -> URLRecord
            - Return full record or raise NotFoundError
        delete(self, code: str) -> bool
            - Delegate to storage.delete()

Dependencies: urlshort.models (URLRecord, StorageBackend, error types)
"""

from __future__ import annotations


# TODO: Implement URLShortener per spec
