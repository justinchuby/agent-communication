"""Core URL shortener logic.

Owner: Developer A

Provides the URLShortener class which orchestrates short-code generation,
URL resolution, statistics tracking, and deletion through a pluggable
StorageBackend.
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


def _to_base62(number: int) -> str:
    """Convert a non-negative integer to a base62 string."""
    if number == 0:
        return "0"
    result: list[str] = []
    while number > 0:
        number, remainder = divmod(number, 62)
        result.append(BASE62_ALPHABET[remainder])
    return "".join(reversed(result))


def _generate_code(url: str, length: int, attempt: int = 0) -> str:
    """Generate a deterministic base62 code for *url*.

    On the first attempt the raw SHA-256 hash is used.  For subsequent
    attempts (collision resolution) the *attempt* counter is appended to
    the URL before hashing so that a different code is produced.
    """
    source = url if attempt == 0 else f"{url}#{attempt}"
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
    number = int(digest, 16)
    return _to_base62(number)[:length]


class URLShortener:
    """High-level URL shortening service.

    Parameters
    ----------
    storage:
        A :class:`StorageBackend` implementation used for persistence.
    code_length:
        Length of generated short codes (default 6).
    """

    def __init__(self, storage: StorageBackend, code_length: int = 6) -> None:
        self._storage = storage
        self._code_length = code_length

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def shorten(self, url: str, expires_in: timedelta | None = None) -> str:
        """Create or retrieve a short code for *url*.

        If the URL has already been shortened, the existing code is returned
        (deduplication).  Otherwise a new base62 code is generated and stored.

        Raises :class:`InvalidURLError` if *url* is empty or does not start
        with ``http://`` or ``https://``.
        """
        self._validate_url(url)

        existing = self._storage.get_by_url(url)
        if existing is not None:
            if existing.expires_at is None or datetime.now(timezone.utc) < existing.expires_at:
                return existing.code
            # Expired — delete stale record and re-create below
            self._storage.delete(existing.code)

        code = self._unique_code(url)

        now = datetime.now(timezone.utc)
        expires_at = (now + expires_in) if expires_in is not None else None

        record = URLRecord(
            code=code,
            url=url,
            created_at=now,
            expires_at=expires_at,
        )
        self._storage.save(record)
        return code

    def resolve(self, code: str) -> str:
        """Resolve a short code to the original URL.

        Raises :class:`NotFoundError` if the code does not exist and
        :class:`ExpiredError` if the code has expired.

        Each successful resolve increments the record's click count and
        updates its ``last_accessed`` timestamp.
        """
        record = self._storage.get_by_code(code)
        if record is None:
            raise NotFoundError(code)

        if record.expires_at is not None and datetime.now(timezone.utc) >= record.expires_at:
            raise ExpiredError(code)

        self._storage.increment_clicks(code)
        return record.url

    def get_stats(self, code: str) -> URLRecord:
        """Return the full :class:`URLRecord` for *code*.

        Raises :class:`NotFoundError` if the code does not exist.
        """
        record = self._storage.get_by_code(code)
        if record is None:
            raise NotFoundError(code)
        return record

    def delete(self, code: str) -> bool:
        """Delete the record for *code*.

        Returns ``True`` if the record was deleted, ``False`` if it did not
        exist.
        """
        return self._storage.delete(code)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_url(url: str) -> None:
        """Raise :class:`InvalidURLError` if *url* is not a valid HTTP(S) URL."""
        if not url or not url.startswith(("http://", "https://")):
            raise InvalidURLError(url)

    def _unique_code(self, url: str) -> str:
        """Generate a code that is not yet present in storage.

        Uses incrementing attempt counter for collision resolution.
        Raises RuntimeError after 1000 failed attempts as a safety guard.
        """
        max_attempts = 1000
        for attempt in range(max_attempts):
            code = _generate_code(url, self._code_length, attempt)
            if self._storage.get_by_code(code) is None:
                return code
        raise RuntimeError(
            f"Failed to generate a unique code after {max_attempts} attempts"
        )
