"""
src/week3/failure_log.py
=========================
Week 3: Failure logging — records agent failures and provides relevant warnings for planning.
"""

import json
import os
from pathlib import Path

FAILURE_LOG_PATH = Path("agent_failures.json")


def log_failure(task: str, approach: str, reason: str) -> None:
    """
    Append a failure entry to agent_failures.json.

    Args:
        task: The task that failed.
        approach: Which approach was used (e.g., "planner-executor", "react").
        reason: Why it failed.
    """
    entries = []
    if FAILURE_LOG_PATH.exists():
        try:
            entries = json.loads(FAILURE_LOG_PATH.read_text())
        except (json.JSONDecodeError, FileNotFoundError):
            entries = []

    entries.append({
        "task": task,
        "approach": approach,
        "reason": reason,
    })

    FAILURE_LOG_PATH.write_text(json.dumps(entries, indent=2))
    print(f"[FailureLog] Logged failure: {reason[:80]}...")


def get_relevant_warnings(goal: str, max_entries: int = 3) -> str:
    """
    Retrieve relevant past failures to inject into the Planner prompt.

    Args:
        goal: The current goal to match against.
        max_entries: Maximum number of warnings to return.

    Returns:
        Formatted warning string, or empty string if no relevant failures.
    """
    if not FAILURE_LOG_PATH.exists():
        return ""

    try:
        entries = json.loads(FAILURE_LOG_PATH.read_text())
    except (json.JSONDecodeError, FileNotFoundError):
        return ""

    if not entries:
        return ""

    # Simple keyword matching — find entries with overlapping words
    goal_words = set(goal.lower().split())
    scored = []
    for entry in entries:
        task_words = set(entry["task"].lower().split())
        overlap = len(goal_words & task_words)
        if overlap > 0:
            scored.append((overlap, entry))

    scored.sort(key=lambda x: x[0], reverse=True)
    relevant = [e for _, e in scored[:max_entries]]

    if not relevant:
        return ""

    warnings = ["WARNINGS FROM PAST FAILURES:"]
    for entry in relevant:
        warnings.append(f"- Task: {entry['task'][:60]}... | Reason: {entry['reason']}")

    return "\n".join(warnings)


if __name__ == "__main__":
    # Demo
    log_failure(
        "Find a pub for 300 guests",
        "planner-executor",
        "No venue in Edinburgh has capacity for 300 guests"
    )
    log_failure(
        "Book The Bow Bar for tonight",
        "react",
        "The Bow Bar is currently full"
    )

    warnings = get_relevant_warnings("Find a pub for a large group in Edinburgh")
    print(f"\n{warnings}")
