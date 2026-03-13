"""URL shortener data models and error types.

Owner: Developer A (architect defines interfaces, dev implements)

Implement:
    @dataclass URLRecord — see task-description.md for fields
    ShortenerError(Exception) — base error
    NotFoundError(ShortenerError) — code not found
    ExpiredError(ShortenerError) — code expired
    InvalidURLError(ShortenerError) — malformed URL
    StorageBackend(Protocol) — storage interface (6 methods)
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


# TODO: Implement all models, errors, and StorageBackend protocol per spec
