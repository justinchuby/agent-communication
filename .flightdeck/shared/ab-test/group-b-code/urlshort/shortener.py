"""Core URL shortener logic.

Implements URLShortener — the public API for shortening, resolving,
and managing shortened URLs.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

from urlshort.models import (
    ExpiredError,
    InvalidURLError,
    NotFoundError,
    StorageBackend,
    URLRecord,
)

BASE62_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _base62_encode(number: int, length: int) -> str:
    """Encode a non-negative integer into a base62 string of exactly *length* chars."""
    if number == 0:
        return BASE62_ALPHABET[0] * length
    chars: list[str] = []
    while number:
        number, remainder = divmod(number, 62)
        chars.append(BASE62_ALPHABET[remainder])
    result = "".join(reversed(chars))
    # Pad or truncate to desired length
    return result[:length].rjust(length, BASE62_ALPHABET[0])


def _generate_code(url: str, length: int, attempt: int = 0) -> str:
    """Deterministic short code from *url*. On collision, bump *attempt*."""
    source = url if attempt == 0 else f"{url}#{attempt}"
    digest = hashlib.sha256(source.encode()).hexdigest()
    num = int(digest, 16)
    return _base62_encode(num, length)


class URLShortener:
    """Facade for shortening, resolving, and managing short URLs."""

    def __init__(self, storage: StorageBackend, code_length: int = 6) -> None:
        self._storage = storage
        self._code_length = code_length

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def shorten(self, url: str, expires_in: timedelta | None = None) -> str:
        """Create or retrieve a short code for *url*.

        Returns the short code string.
        Raises InvalidURLError if *url* doesn't start with http(s)://.
        """
        self._validate_url(url)

        # De-dup: return existing code for the same URL
        existing = self._storage.get_by_url(url)
        if existing is not None:
            return existing.code

        # Generate code with collision resolution
        code = self._generate_unique_code(url)

        expires_at: datetime | None = None
        if expires_in is not None:
            expires_at = datetime.now(timezone.utc) + expires_in

        record = URLRecord(
            code=code,
            url=url,
            created_at=datetime.now(timezone.utc),
            expires_at=expires_at,
        )
        self._storage.save(record)
        return code

    def resolve(self, code: str) -> str:
        """Resolve *code* to the original URL.

        Raises NotFoundError if the code doesn't exist.
        Raises ExpiredError if the URL has expired.
        """
        record = self._storage.get_by_code(code)
        if record is None:
            raise NotFoundError(f"Short code not found: {code}")

        if record.expires_at is not None and record.expires_at <= datetime.now(timezone.utc):
            raise ExpiredError(f"Short code expired: {code}")

        self._storage.increment_clicks(code)
        return record.url

    def get_stats(self, code: str) -> URLRecord:
        """Return the full URLRecord for *code*.

        Raises NotFoundError if the code doesn't exist.
        """
        record = self._storage.get_by_code(code)
        if record is None:
            raise NotFoundError(f"Short code not found: {code}")
        return record

    def delete(self, code: str) -> bool:
        """Delete the record for *code*. Returns True if deleted, False if not found."""
        return self._storage.delete(code)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_url(url: str) -> None:
        if not url:
            raise InvalidURLError("URL must not be empty")
        if not (url.startswith("http://") or url.startswith("https://")):
            raise InvalidURLError(
                f"Invalid URL (must start with http:// or https://): {url}"
            )

    def _generate_unique_code(self, url: str) -> str:
        """Generate a code for *url*, retrying on collision."""
        attempt = 0
        while True:
            code = _generate_code(url, self._code_length, attempt)
            if self._storage.get_by_code(code) is None:
                return code
            attempt += 1
