"""Data classes and validation helpers for the user analytics pipeline."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class ActivityRecord:
    """A single user activity event."""
    user_id: str
    action: str
    score: float
    timestamp: str


@dataclass
class UserStats:
    """Aggregated statistics for a single user."""
    user_id: str
    total_actions: int
    total_score: float
    average_score: float
    actions: List[str] = field(default_factory=list)


def validate_record(record: dict) -> bool:
    """Check that a raw record dict has all required fields."""
    required_fields = {"user_id", "action", "score", "timestamp"}
    if not isinstance(record, dict):
        return False
    return required_fields.issubset(record.keys())


def parse_activity_record(record: dict) -> ActivityRecord:
    """Convert a raw dict into an ActivityRecord, raising on invalid data."""
    if not validate_record(record):
        raise ValueError(f"Invalid record: missing required fields in {record}")
    return ActivityRecord(
        user_id=str(record["user_id"]),
        action=str(record["action"]),
        score=float(record["score"]),
        timestamp=str(record["timestamp"]),
    )
