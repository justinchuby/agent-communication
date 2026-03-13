"""Tests for the user analytics pipeline.

Run with: python -m pytest test_pipeline.py -v
"""

import sys
import os

# Ensure the bug-hunt-codebase directory is importable
sys.path.insert(0, os.path.dirname(__file__))

from models import validate_record, parse_activity_record, ActivityRecord
from data_loader import load_user_records
from processor import compute_user_stats, get_top_users


# ---------------------------------------------------------------------------
# models.py tests
# ---------------------------------------------------------------------------

class TestValidateRecord:
    def test_valid_record(self):
        record = {"user_id": "u1", "action": "login", "score": 1.0, "timestamp": "2026-01-01"}
        assert validate_record(record) is True

    def test_missing_field(self):
        record = {"user_id": "u1", "action": "login"}
        assert validate_record(record) is False

    def test_non_dict_input(self):
        assert validate_record("not a dict") is False
        assert validate_record(42) is False


class TestParseActivityRecord:
    def test_parses_valid_record(self):
        raw = {"user_id": "u1", "action": "view", "score": 2.5, "timestamp": "2026-01-01"}
        record = parse_activity_record(raw)
        assert isinstance(record, ActivityRecord)
        assert record.user_id == "u1"
        assert record.score == 2.5

    def test_rejects_invalid_record(self):
        try:
            parse_activity_record({"user_id": "u1"})
            assert False, "Should have raised ValueError"
        except ValueError:
            pass


# ---------------------------------------------------------------------------
# data_loader.py tests
# ---------------------------------------------------------------------------

SAMPLE_RAW_DATA = [
    {"user_id": "u1", "action": "login",   "score": 0.0, "timestamp": "2026-01-01T08:00:00Z"},
    {"user_id": "u1", "action": "purchase", "score": 10.0, "timestamp": "2026-01-01T08:15:00Z"},
    {"user_id": "u2", "action": "login",   "score": 0.0, "timestamp": "2026-01-01T09:00:00Z"},
]


class TestLoadUserRecords:
    def test_returns_dict_keyed_by_user_id(self):
        result = load_user_records(SAMPLE_RAW_DATA)
        assert isinstance(result, dict)
        assert "u1" in result
        assert "u2" in result

    def test_groups_records_correctly(self):
        result = load_user_records(SAMPLE_RAW_DATA)
        assert len(result["u1"]) == 2
        assert len(result["u2"]) == 1

    def test_records_are_activity_record_instances(self):
        result = load_user_records(SAMPLE_RAW_DATA)
        for records in result.values():
            for record in records:
                assert isinstance(record, ActivityRecord)


# ---------------------------------------------------------------------------
# processor.py tests — these tests FAIL due to the cross-file bug
# ---------------------------------------------------------------------------

class TestComputeUserStats:
    def test_computes_stats_for_each_user(self):
        """This test fails because compute_user_stats tries to iterate over
        the dict returned by load_user_records as if it were a list of tuples."""
        user_records = load_user_records(SAMPLE_RAW_DATA)
        stats = compute_user_stats(user_records)
        assert len(stats) == 2

    def test_total_score_calculation(self):
        user_records = load_user_records(SAMPLE_RAW_DATA)
        stats = compute_user_stats(user_records)
        stats_by_id = {s.user_id: s for s in stats}
        assert stats_by_id["u1"].total_score == 10.0

    def test_action_count(self):
        user_records = load_user_records(SAMPLE_RAW_DATA)
        stats = compute_user_stats(user_records)
        stats_by_id = {s.user_id: s for s in stats}
        assert stats_by_id["u1"].total_actions == 2


class TestGetTopUsers:
    def test_returns_top_n(self):
        user_records = load_user_records(SAMPLE_RAW_DATA)
        stats = compute_user_stats(user_records)
        top = get_top_users(stats, top_n=1)
        assert len(top) == 1
        assert top[0].user_id == "u1"


# ---------------------------------------------------------------------------
# End-to-end pipeline test
# ---------------------------------------------------------------------------

class TestEndToEnd:
    def test_full_pipeline(self):
        """Integration test: load → process → report."""
        from main import generate_report
        report = generate_report()
        assert "User Analytics Report" in report
        assert "u001" in report
