"""Entry point for the user analytics pipeline."""

from data_loader import load_user_records
from processor import compute_user_stats, get_top_users


def generate_report() -> str:
    """Run the full pipeline and return a formatted summary report."""
    user_records = load_user_records()
    stats = compute_user_stats(user_records)
    top_users = get_top_users(stats)

    lines = ["=== User Analytics Report ===", ""]

    for user_stat in stats:
        lines.append(f"User {user_stat.user_id}:")
        lines.append(f"  Actions: {user_stat.total_actions}")
        lines.append(f"  Total Score: {user_stat.total_score}")
        lines.append(f"  Avg Score: {user_stat.average_score}")
        lines.append(f"  Activity: {', '.join(user_stat.actions)}")
        lines.append("")

    lines.append("--- Top Users by Score ---")
    for rank, user_stat in enumerate(top_users, 1):
        lines.append(f"  #{rank}: {user_stat.user_id} (score: {user_stat.total_score})")

    return "\n".join(lines)


if __name__ == "__main__":
    print(generate_report())
