"""Computes per-user statistics from loaded user records.

This module takes user activity records and produces aggregated statistics
for each user.
"""

from typing import List
from models import UserStats


def compute_user_stats(user_records) -> List[UserStats]:
    """Compute aggregated statistics for each user.

    Args:
        user_records: User activity records as returned by
            data_loader.load_user_records().

    Returns:
        A list of UserStats, one per user.
    """
    stats_list = []

    # BUG: This code was written when load_user_records() returned a flat
    # list of (user_id, records) tuples. After the refactor to return a dict,
    # iterating over user_records yields string keys, not (user_id, records).
    for user_id, records in user_records.items():
        total_score = sum(record.score for record in records)
        action_names = [record.action for record in records]
        average_score = total_score / len(records) if records else 0.0

        stats_list.append(UserStats(
            user_id=user_id,
            total_actions=len(records),
            total_score=round(total_score, 2),
            average_score=round(average_score, 2),
            actions=action_names,
        ))

    return stats_list


def get_top_users(stats: List[UserStats], top_n: int = 3) -> List[UserStats]:
    """Return the top N users by total score, descending."""
    sorted_stats = sorted(stats, key=lambda s: s.total_score, reverse=True)
    return sorted_stats[:top_n]
