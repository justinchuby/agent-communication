"""URL shortener data models and error types.

Defines: URLRecord, error hierarchy, StorageBackend protocol.
Interface contract — DO NOT change method signatures without architect sign-off.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


# ---------------------------------------------------------------------------
# Error hierarchy
# ---------------------------------------------------------------------------

class ShortenerError(Exception):
    """Base error for all URL shortener operations."""


class NotFoundError(ShortenerError):
    """Raised when a short code does not exist in storage."""


class ExpiredError(ShortenerError):
    """Raised when a short code exists but has expired."""


class InvalidURLError(ShortenerError):
    """Raised when the provided URL is malformed (must start with http:// or https://)."""


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class URLRecord:
    """Represents a shortened URL entry."""

    code: str                                  # 6-char base62 short code
    url: str                                   # Original URL
    created_at: datetime                       # Creation timestamp
    click_count: int = 0                       # Number of times resolved
    last_accessed: datetime | None = None      # Last resolve timestamp
    expires_at: datetime | None = None         # Optional expiry


# ---------------------------------------------------------------------------
# Storage protocol — Dev B implements this; Dev A codes against it
# ---------------------------------------------------------------------------

class StorageBackend(Protocol):
    """Abstract storage interface. All implementations must provide these 6 methods."""

    def save(self, record: URLRecord) -> None:
        """Persist a URLRecord. Overwrites if code already exists."""
        ...

    def get_by_code(self, code: str) -> URLRecord | None:
        """Return the record for *code*, or None if not found."""
        ...

    def get_by_url(self, url: str) -> URLRecord | None:
        """Return existing record for *url* (dedup lookup), or None."""
        ...

    def delete(self, code: str) -> bool:
        """Delete the record for *code*. Return True if deleted, False if not found."""
        ...

    def increment_clicks(self, code: str) -> None:
        """Increment click_count by 1 and set last_accessed to now."""
        ...

    def list_all(self) -> list[URLRecord]:
        """Return all stored records."""
        ...
