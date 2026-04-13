"""
src/week3/parallel_executor.py
===============================
Week 3: Parallel execution — runs independent steps concurrently with asyncio.
"""

import asyncio
import json
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.week3.planner_executor import dispatch_tool


async def async_tool_call(step_id: int, tool: str, action: str) -> dict:
    """
    Async wrapper around dispatch_tool.

    Args:
        step_id: The step ID for tracking.
        tool: Tool name to dispatch to.
        action: Action description.

    Returns:
        dict with step_id, success, output, and error.
    """
    print(f"[Parallel] Starting step {step_id}: {tool}")

    # Run synchronous dispatch_tool in a thread pool
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        dispatch_tool,
        {"id": step_id, "tool": tool, "action": action},
    )

    print(f"[Parallel] Step {step_id} {'✅' if result['success'] else '❌'}")
    return {
        "step_id": step_id,
        "success": result["success"],
        "output": result.get("output"),
        "error": result.get("error"),
    }


async def parallel_execute(steps: list) -> list:
    """
    Execute independent steps in parallel using asyncio.gather.

    A step is "independent" if its depends_on list is empty or
    all dependencies are already completed.

    Args:
        steps: List of step dicts with id, tool, action, depends_on.

    Returns:
        List of result dicts.
    """
    completed = set()
    all_results = []
    remaining = list(steps)

    while remaining:
        # Find independent steps
        ready = []
        still_waiting = []

        for step in remaining:
            deps = set(step.get("depends_on", []))
            if deps.issubset(completed):
                ready.append(step)
            else:
                still_waiting.append(step)

        if not ready:
            # Deadlock — no steps can proceed
            print("[Parallel] ⚠️ Deadlock detected: no ready steps.")
            break

        # Execute ready steps in parallel
        print(f"\n[Parallel] Executing {len(ready)} steps in parallel...")
        tasks = [
            async_tool_call(
                step.get("id", 0),
                step.get("tool", ""),
                step.get("action", ""),
            )
            for step in ready
        ]
        results = await asyncio.gather(*tasks)

        for result in results:
            all_results.append(result)
            if result["success"]:
                completed.add(result["step_id"])

        remaining = still_waiting

    return all_results


if __name__ == "__main__":
    # Demo: parallel execution of independent steps
    test_steps = [
        {"id": 1, "tool": "search_venues", "action": "Search for venues", "depends_on": []},
        {"id": 2, "tool": "get_weather", "action": "Check weather", "depends_on": []},
        {"id": 3, "tool": "check_availability", "action": "Check best venue", "depends_on": [1]},
        {"id": 4, "tool": "calculate_cost", "action": "Calculate cost", "depends_on": [3]},
    ]

    print("Parallel Executor Demo")
    print("=" * 60)
    results = asyncio.run(parallel_execute(test_steps))
    print(f"\n{'=' * 60}")
    for r in results:
        icon = "✅" if r["success"] else "❌"
        print(f"  {icon} Step {r['step_id']}: {r.get('error', 'OK')}")
