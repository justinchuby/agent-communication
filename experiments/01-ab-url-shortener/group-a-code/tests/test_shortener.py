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
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from urlshort import (
    ExpiredError,
    InMemoryStorage,
    InvalidURLError,
    NotFoundError,
    URLRecord,
    URLShortener,
)

BASE62 = string.digits + string.ascii_lowercase + string.ascii_uppercase
BASE62_PATTERN = re.compile(r"^[0-9a-zA-Z]{6}$")


@pytest.fixture
def storage():
    return InMemoryStorage()


@pytest.fixture
def shortener(storage):
    return URLShortener(storage=storage)


# 1. shorten() returns a 6-char base62 code
def test_shorten_returns_6_char_base62_code(shortener):
    code = shortener.shorten("https://example.com")
    assert len(code) == 6
    assert BASE62_PATTERN.match(code), f"Code {code!r} is not base62"


# 2. shorten() same URL returns same code (dedup)
def test_shorten_same_url_returns_same_code(shortener):
    code1 = shortener.shorten("https://example.com")
    code2 = shortener.shorten("https://example.com")
    assert code1 == code2


# 3. resolve() returns original URL
def test_resolve_returns_original_url(shortener):
    code = shortener.shorten("https://example.com/page")
    url = shortener.resolve(code)
    assert url == "https://example.com/page"


# 4. resolve() increments click count
def test_resolve_increments_click_count(shortener, storage):
    code = shortener.shorten("https://example.com")
    shortener.resolve(code)
    shortener.resolve(code)
    record = storage.get_by_code(code)
    assert record is not None
    assert record.click_count == 2


# 5. resolve() updates last_accessed
def test_resolve_updates_last_accessed(shortener, storage):
    code = shortener.shorten("https://example.com")
    before = datetime.now(timezone.utc)
    shortener.resolve(code)
    record = storage.get_by_code(code)
    assert record is not None
    assert record.last_accessed is not None
    assert record.last_accessed >= before


# 6. resolve() raises NotFoundError for unknown code
def test_resolve_raises_not_found_for_unknown_code(shortener):
    with pytest.raises(NotFoundError):
        shortener.resolve("zzzzzz")


# 7. resolve() raises ExpiredError for expired URL
def test_resolve_raises_expired_error(shortener):
    code = shortener.shorten("https://example.com", expires_in=timedelta(seconds=-1))
    with pytest.raises(ExpiredError):
        shortener.resolve(code)


# 8. shorten() with expires_in sets expiry
def test_shorten_with_expires_in_sets_expiry(shortener, storage):
    code = shortener.shorten("https://example.com", expires_in=timedelta(hours=1))
    record = storage.get_by_code(code)
    assert record is not None
    assert record.expires_at is not None
    assert record.expires_at > datetime.now(timezone.utc)


# 9. delete() removes the record
def test_delete_removes_record(shortener):
    code = shortener.shorten("https://example.com")
    result = shortener.delete(code)
    assert result is True
    with pytest.raises(NotFoundError):
        shortener.resolve(code)


# 10. delete() returns False for unknown code
def test_delete_returns_false_for_unknown_code(shortener):
    result = shortener.delete("zzzzzz")
    assert result is False


# 11. get_stats() returns correct record
def test_get_stats_returns_correct_record(shortener):
    code = shortener.shorten("https://example.com")
    shortener.resolve(code)
    stats = shortener.get_stats(code)
    assert isinstance(stats, URLRecord)
    assert stats.code == code
    assert stats.url == "https://example.com"
    assert stats.click_count == 1
    assert stats.last_accessed is not None


# 12. get_stats() raises NotFoundError for unknown
def test_get_stats_raises_not_found_for_unknown(shortener):
    with pytest.raises(NotFoundError):
        shortener.get_stats("zzzzzz")


# 13. shorten() raises InvalidURLError for bad URL
def test_shorten_raises_invalid_url_for_bad_url(shortener):
    with pytest.raises(InvalidURLError):
        shortener.shorten("not-a-url")


# 14. shorten() raises InvalidURLError for empty string
def test_shorten_raises_invalid_url_for_empty_string(shortener):
    with pytest.raises(InvalidURLError):
        shortener.shorten("")


# 15. list_all() returns all records
def test_list_all_returns_all_records(shortener, storage):
    shortener.shorten("https://example.com")
    shortener.shorten("https://other.com")
    records = storage.list_all()
    assert len(records) == 2
    urls = {r.url for r in records}
    assert urls == {"https://example.com", "https://other.com"}


# 16. concurrent shorten() calls don't collide
def test_concurrent_shorten_calls_dont_collide(storage):
    shortener = URLShortener(storage=storage)
    urls = [f"https://example.com/{i}" for i in range(20)]

    with ThreadPoolExecutor(max_workers=4) as executor:
        codes = list(executor.map(shortener.shorten, urls))

    assert len(set(codes)) == 20


# 17. code is deterministic (same URL → same hash)
def test_code_is_deterministic(storage):
    s1 = URLShortener(storage=InMemoryStorage())
    s2 = URLShortener(storage=InMemoryStorage())
    code1 = s1.shorten("https://example.com/deterministic")
    code2 = s2.shorten("https://example.com/deterministic")
    assert code1 == code2


# 18. collision resolution works (forced collision scenario)
def test_collision_resolution(storage):
    shortener = URLShortener(storage=storage)
    code1 = shortener.shorten("https://example.com/a")

    # Force a collision by inserting a record with the same code but different URL
    from urlshort.models import URLRecord as _URLRecord

    fake_record = _URLRecord(
        code=code1,
        url="https://collision.com/fake",
        created_at=datetime.now(timezone.utc),
    )
    # Replace the stored record to simulate a collision scenario
    # We need to trick the shortener: remove the original, insert fake with same code
    storage.delete(code1)
    storage.save(fake_record)

    # Now shorten a new URL that would hash to the same code
    # Since "https://example.com/a" hashes to code1, shortening it again
    # should detect that code1 is taken by a different URL and resolve collision
    code2 = shortener.shorten("https://example.com/a")
    assert code2 != code1
    assert len(code2) == 6
