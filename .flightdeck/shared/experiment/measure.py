#!/usr/bin/env python3
"""Measurement framework for the communication efficiency experiment.

Tracks token usage, message counts, clarifications, task success, and
elapsed time across five experimental conditions:

  A: Baseline English (free-form natural language)
  B: SIP only (structured intent protocol — JSON message envelopes)
  C: SBDS + SIP (shared blackboard + structured messages)
  D: Full stack (SBDS + SIP + PCC + communication by exception + regulatory triggers)
  E: Full + content-addressing (everything in D plus content-addressable context hashes)

Usage:
    # As a library
    from measure import ExperimentTracker, ConditionResult
    tracker = ExperimentTracker()
    tracker.add_result("A", ConditionResult(...))
    print(tracker.summary())

    # As a CLI
    python measure.py results_a.json results_b.json ...
"""

import json
import math
import sys
import time
from dataclasses import dataclass, field, asdict
from typing import List, Optional


# ---------------------------------------------------------------------------
# Token estimation
# ---------------------------------------------------------------------------

TOKEN_MULTIPLIER = 1.3  # approximate tokens ≈ word_count × 1.3


def estimate_tokens(text: str) -> int:
    """Estimate token count from text using word_count × 1.3."""
    word_count = len(text.split())
    return math.ceil(word_count * TOKEN_MULTIPLIER)


def count_tokens_in_messages(messages: List[dict]) -> int:
    """Sum estimated tokens across a list of message dicts.

    Each message dict should have a "content" key with the text body.
    """
    total = 0
    for message in messages:
        content = message.get("content", "")
        total += estimate_tokens(content)
    return total


# ---------------------------------------------------------------------------
# Clarification detection
# ---------------------------------------------------------------------------

CLARIFICATION_MARKERS = [
    "what do you mean",
    "can you clarify",
    "i don't understand",
    "could you explain",
    "not sure what",
    "please clarify",
    "what exactly",
    "can you elaborate",
    "i'm confused",
    "unclear",
]


def is_clarification_request(message_content: str) -> bool:
    """Heuristic check: does this message ask for clarification?"""
    lowered = message_content.lower()
    return any(marker in lowered for marker in CLARIFICATION_MARKERS)


def count_clarifications(messages: List[dict]) -> int:
    """Count how many messages in a conversation are clarification requests."""
    return sum(
        1 for msg in messages
        if is_clarification_request(msg.get("content", ""))
    )


# ---------------------------------------------------------------------------
# Condition result
# ---------------------------------------------------------------------------

CONDITION_LABELS = {
    "A": "Baseline English",
    "B": "SIP only",
    "C": "SBDS + SIP",
    "D": "Full stack",
    "E": "Full + content-addressing",
}


@dataclass
class ConditionResult:
    """Metrics captured for a single experimental condition run."""
    condition: str  # A, B, C, D, or E
    messages: List[dict] = field(default_factory=list)
    task_success: bool = False
    start_time: Optional[float] = None
    end_time: Optional[float] = None

    @property
    def total_tokens(self) -> int:
        return count_tokens_in_messages(self.messages)

    @property
    def message_count(self) -> int:
        return len(self.messages)

    @property
    def clarification_count(self) -> int:
        return count_clarifications(self.messages)

    @property
    def elapsed_seconds(self) -> float:
        if self.start_time is not None and self.end_time is not None:
            return self.end_time - self.start_time
        return 0.0

    def to_dict(self) -> dict:
        return {
            "condition": self.condition,
            "condition_label": CONDITION_LABELS.get(self.condition, "Unknown"),
            "total_tokens": self.total_tokens,
            "message_count": self.message_count,
            "clarification_count": self.clarification_count,
            "task_success": self.task_success,
            "elapsed_seconds": round(self.elapsed_seconds, 2),
        }


# ---------------------------------------------------------------------------
# Timer context manager for easy measurement
# ---------------------------------------------------------------------------

class MeasureTimer:
    """Context manager to capture start/end time for a condition run."""

    def __init__(self):
        self.start_time: float = 0.0
        self.end_time: float = 0.0

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        return False

    @property
    def elapsed(self) -> float:
        return self.end_time - self.start_time


# ---------------------------------------------------------------------------
# Experiment tracker — aggregates results across conditions
# ---------------------------------------------------------------------------

class ExperimentTracker:
    """Collects and compares results across experimental conditions."""

    def __init__(self):
        self.results: dict[str, ConditionResult] = {}

    def add_result(self, condition: str, result: ConditionResult):
        """Register the result for a condition (A-E)."""
        if condition not in CONDITION_LABELS:
            raise ValueError(
                f"Unknown condition '{condition}'. Expected one of: {list(CONDITION_LABELS.keys())}"
            )
        self.results[condition] = result

    def summary(self) -> str:
        """Generate a human-readable comparison table."""
        lines = [
            "=" * 78,
            "COMMUNICATION EFFICIENCY EXPERIMENT — RESULTS SUMMARY",
            "=" * 78,
            "",
            f"{'Condition':<30} {'Tokens':>8} {'Msgs':>6} {'Clarif':>8} {'Success':>9} {'Time(s)':>9}",
            "-" * 78,
        ]

        baseline_tokens = None

        for cond_key in ["A", "B", "C", "D", "E"]:
            if cond_key not in self.results:
                lines.append(f"  {cond_key}: {CONDITION_LABELS[cond_key]:<24} {'(no data)':>8}")
                continue

            result = self.results[cond_key]
            metrics = result.to_dict()

            if baseline_tokens is None:
                baseline_tokens = metrics["total_tokens"]

            savings = ""
            if baseline_tokens and baseline_tokens > 0 and cond_key != "A":
                pct = (1 - metrics["total_tokens"] / baseline_tokens) * 100
                savings = f" ({pct:+.0f}%)"

            label = f"{cond_key}: {metrics['condition_label']}"
            success_str = "PASS" if metrics["task_success"] else "FAIL"

            lines.append(
                f"  {label:<28} {metrics['total_tokens']:>8} {metrics['message_count']:>6} "
                f"{metrics['clarification_count']:>8} {success_str:>9} {metrics['elapsed_seconds']:>9.1f}"
                f"{savings}"
            )

        lines.append("-" * 78)

        if baseline_tokens and baseline_tokens > 0:
            lines.append("")
            lines.append("Token savings vs baseline (A):")
            for cond_key in ["B", "C", "D", "E"]:
                if cond_key in self.results:
                    cond_tokens = self.results[cond_key].total_tokens
                    pct = (1 - cond_tokens / baseline_tokens) * 100
                    lines.append(f"  {cond_key}: {pct:+.1f}% tokens")

        lines.append("")
        lines.append("=" * 78)
        return "\n".join(lines)

    def to_json(self) -> str:
        """Export all results as JSON."""
        data = {}
        for cond_key, result in self.results.items():
            data[cond_key] = result.to_dict()
        return json.dumps(data, indent=2)


# ---------------------------------------------------------------------------
# CLI: load results from JSON files and print summary
# ---------------------------------------------------------------------------

def load_result_from_file(filepath: str) -> ConditionResult:
    """Load a ConditionResult from a JSON file.

    Expected JSON format:
    {
        "condition": "A",
        "messages": [{"role": "agent", "content": "..."}, ...],
        "task_success": true,
        "start_time": 1234567890.0,
        "end_time": 1234567900.0
    }
    """
    with open(filepath, "r") as f:
        data = json.load(f)

    return ConditionResult(
        condition=data["condition"],
        messages=data.get("messages", []),
        task_success=data.get("task_success", False),
        start_time=data.get("start_time"),
        end_time=data.get("end_time"),
    )


def main():
    if len(sys.argv) < 2:
        print("Usage: python measure.py <result_a.json> [result_b.json] ...")
        print("")
        print("Each JSON file should contain a condition result with fields:")
        print('  condition (str): "A", "B", "C", "D", or "E"')
        print("  messages (list): [{role, content}, ...]")
        print("  task_success (bool)")
        print("  start_time (float, optional)")
        print("  end_time (float, optional)")
        sys.exit(1)

    tracker = ExperimentTracker()
    for filepath in sys.argv[1:]:
        result = load_result_from_file(filepath)
        tracker.add_result(result.condition, result)

    print(tracker.summary())
    print("")
    print("JSON export:")
    print(tracker.to_json())


if __name__ == "__main__":
    main()
