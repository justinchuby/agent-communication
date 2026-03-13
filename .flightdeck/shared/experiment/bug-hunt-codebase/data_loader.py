"""Loads and parses raw user activity data.

This module provides the data loading layer for the analytics pipeline.
It accepts raw activity records and returns structured user data grouped
by user ID.
"""

from typing import Dict, List
from models import ActivityRecord, parse_activity_record


# Simulated raw data source — in a real system this would read from a
# database or API.
RAW_ACTIVITY_DATA = [
    {"user_id": "u001", "action": "login",    "score": 0.0,  "timestamp": "2026-03-01T08:00:00Z"},
    {"user_id": "u001", "action": "purchase",  "score": 49.99, "timestamp": "2026-03-01T08:15:00Z"},
    {"user_id": "u002", "action": "login",    "score": 0.0,  "timestamp": "2026-03-01T09:00:00Z"},
    {"user_id": "u002", "action": "view",     "score": 1.5,  "timestamp": "2026-03-01T09:05:00Z"},
    {"user_id": "u002", "action": "purchase",  "score": 29.99, "timestamp": "2026-03-01T09:30:00Z"},
    {"user_id": "u003", "action": "login",    "score": 0.0,  "timestamp": "2026-03-01T10:00:00Z"},
    {"user_id": "u003", "action": "view",     "score": 2.0,  "timestamp": "2026-03-01T10:10:00Z"},
]


def load_user_records(raw_data: List[dict] = None) -> Dict[str, List[ActivityRecord]]:
    """Load raw activity data and return user records grouped by user ID.

    Returns:
        A dict mapping user_id -> list of ActivityRecord objects.

    NOTE: This function was recently refactored to return a dict keyed by
    user_id for O(1) lookups, instead of the previous flat list return type.
    All downstream consumers should have been updated accordingly.
    """
    if raw_data is None:
        raw_data = RAW_ACTIVITY_DATA

    records_by_user: Dict[str, List[ActivityRecord]] = {}
    for raw_record in raw_data:
        record = parse_activity_record(raw_record)
        if record.user_id not in records_by_user:
            records_by_user[record.user_id] = []
        records_by_user[record.user_id].append(record)

    return records_by_user
