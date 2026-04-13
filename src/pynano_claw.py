"""
PyNanoClaw — The Headless Automator (Project A)
Sovereign Agent Lab — Nebius Academy Module 1

The autonomous agent that receives a task, plans and executes without
human guidance, and returns structured results. Always-on heartbeat loop.
"""

import json
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
from src.llm_provider import get_llm_client, resolve_model
from src.week2.edinburgh_orchestrator import run_orchestrator
from src.week3.planner_executor import run_planner_executor
from src.week3.complexity_router import route_query

load_dotenv()

client, PROVIDER = get_llm_client()
print(f"[PyNanoClaw] Provider: {PROVIDER.upper()}")


def run_headless_task(goal: str) -> dict:
    """
    Main entry point for the Headless Automator.
    Routes to Planner-Executor or simple ReAct based on complexity.

    Args:
        goal: Natural language task description.

    Returns:
        dict with "completed" and "replans_used" keys.
    """
    route = route_query(goal)
    print(f"[Router] Query classified as: {route}")

    if route == "COMPLEX":
        return run_planner_executor(goal)
    else:
        from src.week3.react_agent import react_agent
        answer = react_agent(goal)
        return {"completed": {"answer": answer}, "replans_used": 0}


def heartbeat_loop(tasks: list, poll_interval: float = 1.0) -> list:
    """
    The autonomous heartbeat — processes a list of tasks sequentially.
    Simulates the 'always-on loop' from the lecture.

    Args:
        tasks: List of task description strings.
        poll_interval: Seconds between task start messages.

    Returns:
        List of result dicts.
    """
    results = []
    for i, task in enumerate(tasks):
        print(f"\n[Heartbeat] Task {i + 1}/{len(tasks)}: {task[:60]}...")
        try:
            result = run_headless_task(task)
            results.append({"task": task, "status": "completed", "result": result})
        except Exception as e:
            results.append({"task": task, "status": "failed", "error": str(e)})

    # Save results to memory
    with open("agent_memory.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n[PyNanoClaw] Completed {len(results)} tasks. Memory saved to agent_memory.json")
    return results


if __name__ == "__main__":
    # Edinburgh case study — the 5-week running example
    EDINBURGH_TASKS = [
        "Find a pub near the venue in Edinburgh with capacity for 160 people and vegan options. Save top 3 to memory.",
        "Check current weather in Edinburgh Old Town and determine if outdoor seating is viable tonight.",
        "Calculate catering cost for 160 guests at £35 per head.",
        "Generate a promotional event flyer for the AI Meetup at the best available Edinburgh venue.",
    ]

    heartbeat_loop(EDINBURGH_TASKS)
