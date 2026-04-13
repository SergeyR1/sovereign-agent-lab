"""
src/week3/eval_harness.py
==========================
Week 3: Evaluation harness — 5 Edinburgh-themed test tasks.

Metrics: task_completion, plan_quality, step_efficiency, error_recovery, latency.

Usage:
    python src/week3/eval_harness.py             # Full run (uses API budget)
    python src/week3/eval_harness.py --dry-run    # Validate structure only
"""

import json
import sys
import time
from pathlib import Path

# ─── Test tasks ───────────────────────────────────────────────────────────────

EVAL_TASKS = [
    {
        "id": 1,
        "task": "What is the current temperature in Edinburgh?",
        "complexity": "SIMPLE",
        "expected_steps": 2,
        "expected_tools": ["geocode_location", "get_current_weather"],
    },
    {
        "id": 2,
        "task": "Find a pub in Edinburgh for 160 guests with vegan options",
        "complexity": "COMPLEX",
        "expected_steps": 3,
        "expected_tools": ["search_venues", "check_availability"],
    },
    {
        "id": 3,
        "task": (
            "Plan a complete event: find venue for 160 vegan guests, "
            "check weather, calculate catering at £35/head, generate flyer"
        ),
        "complexity": "COMPLEX",
        "expected_steps": 5,
        "expected_tools": ["search_venues", "check_availability", "get_weather", "calculate_cost", "generate_flyer"],
    },
    {
        "id": 4,
        "task": "How much would catering cost for 200 guests at £40 per head?",
        "complexity": "SIMPLE",
        "expected_steps": 1,
        "expected_tools": ["calculate_cost"],
    },
    {
        "id": 5,
        "task": (
            "Compare The Albanach and The Haymarket Vaults for a 160-guest vegan event "
            "and recommend the better option with weather considerations"
        ),
        "complexity": "COMPLEX",
        "expected_steps": 4,
        "expected_tools": ["check_availability", "get_weather"],
    },
]


def validate_task_structure(task: dict) -> dict:
    """Validate a task has all required fields."""
    required = ["id", "task", "complexity", "expected_steps", "expected_tools"]
    missing = [f for f in required if f not in task]
    return {
        "id": task.get("id"),
        "valid": len(missing) == 0,
        "missing_fields": missing,
    }


def run_task(task: dict) -> dict:
    """
    Run a single evaluation task and collect metrics.

    Args:
        task: Task dict from EVAL_TASKS.

    Returns:
        dict with metrics: task_completion, plan_quality, step_efficiency,
        error_recovery, latency.
    """
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    from src.week3.complexity_router import route_query
    from src.week3.planner_executor import run_planner_executor
    from src.week3.react_agent import react_agent

    start = time.time()
    route = route_query(task["task"])

    try:
        if route == "COMPLEX":
            result = run_planner_executor(task["task"])
            completed = result.get("completed", {})
            actual_steps = len(completed)
            task_completed = actual_steps > 0
            error_recovered = result.get("replans_used", 0) > 0
        else:
            answer = react_agent(task["task"], max_turns=4)
            task_completed = bool(answer) and "Error" not in answer
            actual_steps = 1
            error_recovered = False

        latency = time.time() - start

        return {
            "task_id": task["id"],
            "task_description": task["task"][:60],
            "complexity": task["complexity"],
            "routed_as": route,
            "task_completion": task_completed,
            "plan_quality": 4 if task_completed else 2,
            "step_efficiency": round(actual_steps / max(task["expected_steps"], 1), 2),
            "error_recovery": error_recovered,
            "latency_seconds": round(latency, 2),
        }

    except Exception as e:
        latency = time.time() - start
        return {
            "task_id": task["id"],
            "task_description": task["task"][:60],
            "complexity": task["complexity"],
            "routed_as": route,
            "task_completion": False,
            "plan_quality": 1,
            "step_efficiency": 0,
            "error_recovery": False,
            "latency_seconds": round(latency, 2),
            "error": str(e),
        }


def run_evaluation(dry_run: bool = False) -> dict:
    """
    Run the full evaluation harness.

    Args:
        dry_run: If True, validate structure only (no API calls).

    Returns:
        dict with task_results and aggregated metrics.
    """
    print("Evaluation Harness")
    print("=" * 60)

    if dry_run:
        print("[DRY RUN] Validating task structure only (no API calls)")
        validations = [validate_task_structure(t) for t in EVAL_TASKS]
        all_valid = all(v["valid"] for v in validations)
        for v in validations:
            icon = "✅" if v["valid"] else "❌"
            print(f"  {icon} Task {v['id']}: {'valid' if v['valid'] else 'missing: ' + str(v['missing_fields'])}")

        result = {
            "mode": "dry_run",
            "tasks_validated": len(EVAL_TASKS),
            "all_valid": all_valid,
            "validations": validations,
        }
        Path("eval_results.json").write_text(json.dumps(result, indent=2))
        print(f"\n{'✅' if all_valid else '❌'} Validation {'passed' if all_valid else 'failed'}")
        return result

    # Full run
    task_results = []
    for task in EVAL_TASKS:
        print(f"\n--- Evaluating Task {task['id']}: {task['task'][:50]}... ---")
        result = run_task(task)
        task_results.append(result)
        icon = "✅" if result["task_completion"] else "❌"
        print(f"  {icon} Completed: {result['task_completion']} | Latency: {result['latency_seconds']}s")

    # Aggregate metrics
    completions = [r["task_completion"] for r in task_results]
    efficiencies = [r["step_efficiency"] for r in task_results if r["step_efficiency"] > 0]

    output = {
        "mode": "full",
        "task_results": task_results,
        "aggregate": {
            "completion_rate": sum(completions) / len(completions) if completions else 0,
            "avg_step_efficiency": sum(efficiencies) / len(efficiencies) if efficiencies else 0,
            "total_tasks": len(EVAL_TASKS),
            "tasks_completed": sum(completions),
        },
    }

    Path("eval_results.json").write_text(json.dumps(output, indent=2))
    print(f"\n{'=' * 60}")
    print(f"Completion rate: {output['aggregate']['completion_rate']:.0%}")
    print(f"Avg step efficiency: {output['aggregate']['avg_step_efficiency']:.2f}")
    print(f"Results saved to eval_results.json")
    return output


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    run_evaluation(dry_run=dry_run)
