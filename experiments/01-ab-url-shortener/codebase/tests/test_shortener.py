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

import pytest


# TODO: Implement all 18 tests per spec above
