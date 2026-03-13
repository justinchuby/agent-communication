"""Tests for the URL shortener library.

Owner: Tester

Write 18 tests covering:
    1. shorten() returns a 6-char base62 code
    2. shorten() same URL returns same code (dedup)
    3. resolve() returns original URL
    4. resolve() increments click count
    5. resolve() updates last_accessed
    6. resolve() raises NotFoundError for unknown code
    7. resolve() raises ExpiredError for expired URL
    8. shorten() with expires_in sets expiry
    9. delete() removes the record
    10. delete() returns False for unknown code
    11. get_stats() returns correct record
    12. get_stats() raises NotFoundError for unknown
    13. shorten() raises InvalidURLError for bad URL
    14. shorten() raises InvalidURLError for empty string
    15. list_all() returns all records
    16. concurrent shorten() calls don't collide
    17. code is deterministic (same URL → same hash)
    18. collision resolution works (forced collision scenario)
"""

import re
import string
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor

import pytest

from urlshort.models import (
    URLRecord,
    ShortenerError,
    NotFoundError,
    ExpiredError,
    InvalidURLError,
    StorageBackend,
)
from urlshort.storage import InMemoryStorage
from urlshort.shortener import URLShortener

BASE62 = set(string.digits + string.ascii_letters)


@pytest.fixture
def shortener() -> URLShortener:
    return URLShortener(storage=InMemoryStorage())


# ---- 1. shorten() returns a 6-char base62 code ----

def test_shorten_returns_6_char_base62(shortener: URLShortener) -> None:
    code = shortener.shorten("https://example.com")
    assert len(code) == 6
    assert all(c in BASE62 for c in code)


# ---- 2. shorten() same URL returns same code (dedup) ----

def test_shorten_dedup(shortener: URLShortener) -> None:
    code1 = shortener.shorten("https://example.com")
    code2 = shortener.shorten("https://example.com")
    assert code1 == code2


# ---- 3. resolve() returns original URL ----

def test_resolve_returns_original_url(shortener: URLShortener) -> None:
    code = shortener.shorten("https://example.com")
    assert shortener.resolve(code) == "https://example.com"


# ---- 4. resolve() increments click count ----

def test_resolve_increments_click_count(shortener: URLShortener) -> None:
    code = shortener.shorten("https://example.com")
    shortener.resolve(code)
    shortener.resolve(code)
    stats = shortener.get_stats(code)
    assert stats.click_count == 2


# ---- 5. resolve() updates last_accessed ----

def test_resolve_updates_last_accessed(shortener: URLShortener) -> None:
    code = shortener.shorten("https://example.com")
    before = datetime.now(timezone.utc)
    shortener.resolve(code)
    stats = shortener.get_stats(code)
    assert stats.last_accessed is not None
    assert stats.last_accessed >= before


# ---- 6. resolve() raises NotFoundError for unknown code ----

def test_resolve_not_found(shortener: URLShortener) -> None:
    with pytest.raises(NotFoundError):
        shortener.resolve("zzzzzz")


# ---- 7. resolve() raises ExpiredError for expired URL ----

def test_resolve_expired(shortener: URLShortener) -> None:
    code = shortener.shorten("https://example.com", expires_in=timedelta(seconds=-1))
    with pytest.raises(ExpiredError):
        shortener.resolve(code)


# ---- 8. shorten() with expires_in sets expiry ----

def test_shorten_expires_in(shortener: URLShortener) -> None:
    before = datetime.now(timezone.utc)
    code = shortener.shorten("https://example.com", expires_in=timedelta(hours=1))
    stats = shortener.get_stats(code)
    assert stats.expires_at is not None
    assert stats.expires_at > before


# ---- 9. delete() removes the record ----

def test_delete_removes_record(shortener: URLShortener) -> None:
    code = shortener.shorten("https://example.com")
    result = shortener.delete(code)
    assert result is True
    with pytest.raises(NotFoundError):
        shortener.resolve(code)


# ---- 10. delete() returns False for unknown code ----

def test_delete_unknown(shortener: URLShortener) -> None:
    assert shortener.delete("zzzzzz") is False


# ---- 11. get_stats() returns correct record ----

def test_get_stats(shortener: URLShortener) -> None:
    code = shortener.shorten("https://example.com")
    stats = shortener.get_stats(code)
    assert isinstance(stats, URLRecord)
    assert stats.code == code
    assert stats.url == "https://example.com"
    assert stats.click_count == 0


# ---- 12. get_stats() raises NotFoundError for unknown ----

def test_get_stats_not_found(shortener: URLShortener) -> None:
    with pytest.raises(NotFoundError):
        shortener.get_stats("zzzzzz")


# ---- 13. shorten() raises InvalidURLError for bad URL ----

def test_shorten_invalid_url(shortener: URLShortener) -> None:
    with pytest.raises(InvalidURLError):
        shortener.shorten("not-a-url")


# ---- 14. shorten() raises InvalidURLError for empty string ----

def test_shorten_empty_string(shortener: URLShortener) -> None:
    with pytest.raises(InvalidURLError):
        shortener.shorten("")


# ---- 15. list_all() returns all records ----

def test_list_all(shortener: URLShortener) -> None:
    shortener.shorten("https://a.com")
    shortener.shorten("https://b.com")
    shortener.shorten("https://c.com")
    # Access list_all via the storage (public API may not expose it)
    # The spec says StorageBackend has list_all; shortener may not wrap it
    # We test via storage directly if needed, but check shortener first
    storage = shortener._storage if hasattr(shortener, '_storage') else shortener.storage
    records = storage.list_all()
    assert len(records) == 3
    urls = {r.url for r in records}
    assert urls == {"https://a.com", "https://b.com", "https://c.com"}


# ---- 16. concurrent shorten() calls don't collide ----

def test_concurrent_shorten() -> None:
    storage = InMemoryStorage()
    s = URLShortener(storage=storage)
    urls = [f"https://example.com/{i}" for i in range(20)]
    with ThreadPoolExecutor(max_workers=4) as pool:
        codes = list(pool.map(s.shorten, urls))
    assert len(set(codes)) == 20


# ---- 17. code is deterministic (same URL → same hash) ----

def test_deterministic_code() -> None:
    s1 = URLShortener(storage=InMemoryStorage())
    s2 = URLShortener(storage=InMemoryStorage())
    code1 = s1.shorten("https://example.com/deterministic")
    code2 = s2.shorten("https://example.com/deterministic")
    assert code1 == code2


# ---- 18. collision resolution works (forced collision scenario) ----

def test_collision_resolution() -> None:
    storage = InMemoryStorage()
    s = URLShortener(storage=storage)

    # Shorten a first URL normally
    code1 = s.shorten("https://example.com/first")

    # Craft a second URL that would hash to the same 6-char code by
    # injecting a record with that code but a different URL into storage.
    # This forces the shortener to resolve the collision for the new URL.
    fake_record = URLRecord(
        code=code1,
        url="https://collision-fake.com",
        created_at=datetime.now(timezone.utc),
    )
    storage.save(fake_record)

    # Now shorten a new URL whose hash would collide with code1
    # Since the code slot is taken by fake_record and original record is
    # still discoverable by URL, we need a truly new URL that hashes to code1.
    # Instead: overwrite the code slot, remove the original by URL index.
    # Easiest: just shorten a different URL — if its hash collides, it gets a suffix.
    # We force collision by monkey-patching the hash to always return code1.
    import hashlib
    original_sha256 = hashlib.sha256

    class FakeSha256:
        """Always returns bytes that encode to code1 in base62."""
        def __init__(self, *args, **kwargs):
            self._real = original_sha256(*args, **kwargs)

        def hexdigest(self):
            return self._real.hexdigest()

        def digest(self):
            return self._real.digest()

        def update(self, data):
            return self._real.update(data)

    # Simpler approach: delete original, occupy the code slot, shorten new URL
    storage.delete(code1)  # free the code for hash of original URL
    # Re-save the fake with code1
    storage.save(fake_record)

    # Now shorten a new URL. Because we can't control hash output easily,
    # let's test from scratch: occupy a known code, then shorten a URL that
    # hashes to that code.
    storage2 = InMemoryStorage()
    s2 = URLShortener(storage=storage2)
    url_a = "https://example.com/aaa"
    code_a = s2.shorten(url_a)

    # Occupy code_a with a different URL record
    blocker = URLRecord(
        code=code_a,
        url="https://blocker.com",
        created_at=datetime.now(timezone.utc),
    )
    # Delete original so get_by_url won't dedup, then block the code
    storage2.delete(code_a)
    storage2.save(blocker)

    # Shorten a URL that would hash to code_a (same as url_a after deletion)
    code_new = s2.shorten(url_a)

    # The shortener should have resolved the collision — different code
    assert code_new != code_a
    assert len(code_new) == 6
    assert all(c in BASE62 for c in code_new)
    # And it should resolve back correctly
    assert s2.resolve(code_new) == url_a
