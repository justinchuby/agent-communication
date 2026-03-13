#!/usr/bin/env python3
"""Run the communication efficiency experiment across all 5 conditions.

Loads pre-recorded message logs from conditions/ and uses measure.py to
analyze token usage, message counts, clarification requests, and task
success for each communication protocol condition.

Usage:
    python run_experiment.py
    python run_experiment.py --json          # also output raw JSON
    python run_experiment.py --conditions A C E  # run subset
"""

import argparse
import json
import os
import sys

# Ensure the experiment directory is importable
EXPERIMENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, EXPERIMENT_DIR)

from measure import (
    ConditionResult,
    ExperimentTracker,
    CONDITION_LABELS,
    estimate_tokens,
    count_clarifications,
)

CONDITIONS_DIR = os.path.join(EXPERIMENT_DIR, "conditions")

CONDITION_FILES = {
    "A": "condition_a.json",
    "B": "condition_b.json",
    "C": "condition_c.json",
    "D": "condition_d.json",
    "E": "condition_e.json",
}


def load_condition(condition_key: str) -> ConditionResult:
    """Load a condition's message log from its JSON file."""
    filename = CONDITION_FILES[condition_key]
    filepath = os.path.join(CONDITIONS_DIR, filename)

    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"Condition {condition_key} log not found at {filepath}. "
            f"Create it first under conditions/"
        )

    with open(filepath, "r") as f:
        data = json.load(f)

    return ConditionResult(
        condition=data["condition"],
        messages=data.get("messages", []),
        task_success=data.get("task_success", False),
        start_time=data.get("start_time"),
        end_time=data.get("end_time"),
    )


def print_condition_detail(condition_key: str, result: ConditionResult):
    """Print detailed breakdown of a single condition's messages."""
    label = CONDITION_LABELS.get(condition_key, "Unknown")
    print(f"\n{'─' * 70}")
    print(f"  Condition {condition_key}: {label}")
    print(f"{'─' * 70}")
    print(f"  Messages: {result.message_count}")
    print(f"  Total tokens: {result.total_tokens}")
    print(f"  Clarifications: {result.clarification_count}")
    print(f"  Task success: {'YES' if result.task_success else 'NO'}")
    print(f"  Elapsed: {result.elapsed_seconds:.1f}s")
    print()

    for i, msg in enumerate(result.messages, 1):
        role = msg.get("role", "unknown")
        to = msg.get("to", "all")
        content = msg.get("content", "")
        tokens = estimate_tokens(content)
        is_clarif = " [CLARIFICATION]" if "clarif" in content.lower() or "what do you mean" in content.lower() or "can you clarify" in content.lower() else ""

        # Truncate content for display
        display_content = content if len(content) <= 100 else content[:97] + "..."
        print(f"  [{i:2d}] {role:>14} → {to:<14} ({tokens:3d} tok){is_clarif}")
        print(f"       {display_content}")
        print()


def run_experiment(conditions: list[str], show_detail: bool = True, show_json: bool = False):
    """Run the experiment for the specified conditions and print results."""
    tracker = ExperimentTracker()

    print("=" * 70)
    print("  COMMUNICATION EFFICIENCY EXPERIMENT")
    print("  Bug Hunt Task: dict/list type mismatch across 2 files")
    print("  Agents: Investigator, Fixer, Reviewer")
    print("=" * 70)

    for cond_key in conditions:
        try:
            result = load_condition(cond_key)
            tracker.add_result(cond_key, result)
            if show_detail:
                print_condition_detail(cond_key, result)
        except FileNotFoundError as e:
            print(f"\n  ⚠ Skipping condition {cond_key}: {e}")

    # Print the comparison summary from measure.py
    print("\n")
    print(tracker.summary())

    # Print per-message token breakdown
    print()
    print("PER-MESSAGE TOKEN BREAKDOWN")
    print("-" * 50)
    for cond_key in conditions:
        if cond_key in tracker.results:
            result = tracker.results[cond_key]
            tokens_per_msg = [estimate_tokens(m.get("content", "")) for m in result.messages]
            avg = sum(tokens_per_msg) / len(tokens_per_msg) if tokens_per_msg else 0
            print(f"  {cond_key}: {CONDITION_LABELS[cond_key]}")
            print(f"     Per-message tokens: {tokens_per_msg}")
            print(f"     Average: {avg:.1f} tokens/message")
            print()

    if show_json:
        print("\nJSON EXPORT")
        print("-" * 50)
        print(tracker.to_json())


def main():
    parser = argparse.ArgumentParser(
        description="Run the communication efficiency experiment"
    )
    parser.add_argument(
        "--conditions",
        nargs="+",
        choices=["A", "B", "C", "D", "E"],
        default=["A", "B", "C", "D", "E"],
        help="Which conditions to run (default: all)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Also output raw JSON results",
    )
    parser.add_argument(
        "--brief",
        action="store_true",
        help="Skip per-condition message detail",
    )
    args = parser.parse_args()

    run_experiment(
        conditions=args.conditions,
        show_detail=not args.brief,
        show_json=args.json,
    )


if __name__ == "__main__":
    main()
