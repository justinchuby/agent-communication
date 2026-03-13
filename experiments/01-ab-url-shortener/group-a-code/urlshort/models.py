"""URL shortener data models and error types.

Defines the core data model (URLRecord), error hierarchy, and the
StorageBackend protocol that all storage implementations must satisfy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


# ---------------------------------------------------------------------------
# Error hierarchy
# ---------------------------------------------------------------------------

class ShortenerError(Exception):
    """Base exception for all URL shortener errors."""


class NotFoundError(ShortenerError):
    """Raised when a short code does not exist in storage."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(f"Short code not found: {code}")


class ExpiredError(ShortenerError):
    """Raised when a short code exists but has expired."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(f"Short code has expired: {code}")


class InvalidURLError(ShortenerError):
    """Raised when a URL is malformed (must start with http:// or https://)."""

    def __init__(self, url: str) -> None:
        self.url = url
        super().__init__(f"Invalid URL: {url!r}")


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class URLRecord:
    """Represents a shortened URL and its metadata."""

    code: str
    """6-character base62 short code."""

    url: str
    """Original full URL."""

    created_at: datetime
    """Timestamp when the record was created."""

    click_count: int = 0
    """Number of times the short code has been resolved."""

    last_accessed: datetime | None = None
    """Timestamp of the most recent resolve, or None if never accessed."""

    expires_at: datetime | None = None
    """Optional expiration timestamp. None means the link never expires."""


# ---------------------------------------------------------------------------
# Storage protocol
# ---------------------------------------------------------------------------

class StorageBackend(Protocol):
    """Protocol that every storage implementation must satisfy.

    All methods operate on URLRecord instances keyed by their ``code`` field.
    Implementations must maintain a secondary index on ``url`` to support
    efficient deduplication lookups via ``get_by_url``.
    """

    def save(self, record: URLRecord) -> None:
        """Persist a URLRecord. Overwrites if code already exists."""
        ...

    def get_by_code(self, code: str) -> URLRecord | None:
        """Return the record for *code*, or None if not found."""
        ...

    def get_by_url(self, url: str) -> URLRecord | None:
        """Return the record for *url*, or None if not found.

        Used for deduplication — if a URL was already shortened, return
        the existing record instead of creating a new one.
        """
        ...

    def delete(self, code: str) -> bool:
        """Delete the record for *code*. Return True if it existed, False otherwise."""
        ...

    def increment_clicks(self, code: str) -> None:
        """Increment ``click_count`` by 1 and set ``last_accessed`` to now.

        If *code* does not exist, this is a no-op (the caller checks
        existence before calling).
        """
        ...

    def list_all(self) -> list[URLRecord]:
        """Return a list of every stored URLRecord."""
        ...
