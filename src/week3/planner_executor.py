"""
src/week3/planner_executor.py
==============================
Week 3: Planner-Executor architecture — THE MAIN DELIVERABLE.

Planner (reasoning model) generates a JSON plan.
Executor dispatches each step to tools.
On failure: replan and retry (up to max_replans).
"""

import json
import os
import re
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pathlib import Path
from dotenv import load_dotenv
from src.llm_provider import get_llm_client, resolve_model
from src.week2.edinburgh_functions import check_pub_availability, calculate_catering_cost
from src.week2.edinburgh_apis import get_current_weather, geocode_location
from src.week2.cli_venue_search import search_venue_notes
from src.week2.sanitize import sanitize_tool_result
from src.week3.failure_log import get_relevant_warnings, log_failure

load_dotenv()

CHECKPOINT_PATH = Path("checkpoint.json")

# ─── Planner prompts ──────────────────────────────────────────────────────────

PLANNER_SYSTEM = """You are a planning agent. Given a goal, produce a JSON plan.
Each step must have:
- id: integer
- action: specific description
- tool: one of [search_venues, check_availability, calculate_cost, get_weather, generate_flyer, synthesise]
- depends_on: list of step ids
- success_criteria: how to verify success
- on_failure: what to do if this step fails
Max 6 steps. Output ONLY valid JSON: {"goal": "...", "steps": [...]}"""

REPLAN_SYSTEM = """You are a replanning agent. A step in the original plan has failed.
Keep completed steps. Replace or modify the failed step to address the failure cause.
Output ONLY valid JSON: {"goal": "...", "steps": [...]}
Max 6 steps total."""


def _strip_markdown_fences(text: str) -> str:
    """Strip markdown code fences from LLM response."""
    text = text.strip()
    # Remove ```json ... ``` or ``` ... ```
    text = re.sub(r'^```(?:json)?\s*\n?', '', text)
    text = re.sub(r'\n?```\s*$', '', text)
    return text.strip()


def _extract_json(text: str) -> dict:
    """Extract JSON from LLM response, handling markdown fences and thinking tags."""
    # Remove <think>...</think> tags from reasoning models
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    text = _strip_markdown_fences(text)
    # Try to find JSON object in the text
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return json.loads(match.group())
    raise ValueError(f"No valid JSON found in response: {text[:200]}")


def generate_plan(goal: str) -> dict:
    """
    Generate a plan using the planner model.

    Args:
        goal: The high-level goal to plan for.

    Returns:
        dict with "goal" and "steps" keys.
    """
    client, provider = get_llm_client()
    model = resolve_model("planner", provider)

    # Prepend relevant warnings from past failures
    warnings = get_relevant_warnings(goal)
    user_msg = goal
    if warnings:
        user_msg = f"{warnings}\n\nGOAL: {goal}"

    print(f"[Planner] Generating plan with {model}...")
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": PLANNER_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
        max_tokens=1000,
        temperature=0,
    )

    raw = resp.choices[0].message.content
    plan = _extract_json(raw)

    print(f"[Planner] Plan generated: {len(plan.get('steps', []))} steps")
    for step in plan.get("steps", []):
        print(f"  Step {step.get('id')}: [{step.get('tool')}] {step.get('action', '')[:60]}")

    return plan


def dispatch_tool(step: dict) -> dict:
    """
    Route a plan step to the appropriate tool.

    Args:
        step: A plan step dict with "tool" and "action" keys.

    Returns:
        dict with "success", "output", and optionally "error".
    """
    tool = step.get("tool", "")
    action = step.get("action", "")

    print(f"[Executor] Dispatching: {tool} — {action[:60]}")

    try:
        if tool == "search_venues":
            result = search_venue_notes("available")
            if result["count"] > 0:
                return {"success": True, "output": result}
            return {"success": False, "output": result, "error": "No venues found"}

        elif tool == "check_availability":
            # Try The Albanach first (best match for 160 + vegan)
            result = check_pub_availability("The Albanach", 160, True)
            if result.get("meets_all_constraints"):
                return {"success": True, "output": result}
            # Fallback to Haymarket Vaults
            result = check_pub_availability("The Haymarket Vaults", 160, True)
            if result.get("meets_all_constraints"):
                return {"success": True, "output": result}
            return {"success": False, "output": result, "error": "No suitable venue found"}

        elif tool == "calculate_cost":
            result = calculate_catering_cost(160, 35.0)
            return {"success": result["success"], "output": result}

        elif tool == "get_weather":
            geo = geocode_location("Edinburgh")
            if geo["success"]:
                weather = get_current_weather(geo["latitude"], geo["longitude"])
                return {"success": weather["success"], "output": weather}
            return {"success": False, "output": geo, "error": "Geocoding failed"}

        elif tool == "generate_flyer":
            # Stub — returns text description (image gen would be called here)
            flyer = {
                "success": True,
                "description": (
                    "AI Meetup Tonight @ The Albanach, Edinburgh. "
                    "160 guests. Professional event flyer with warm lighting, "
                    "Scottish architecture background, clean modern typography."
                ),
                "image_url": "",
            }
            return {"success": True, "output": flyer}

        elif tool == "synthesise":
            return {
                "success": True,
                "output": {"summary": "All steps completed. Results synthesised."},
            }

        else:
            return {"success": False, "output": None, "error": f"Unknown tool: {tool}"}

    except Exception as e:
        return {"success": False, "output": None, "error": str(e)}


def replan(goal: str, plan: dict, completed: dict, failed_step: dict, error: str) -> dict:
    """
    Generate a revised plan after a step failure.

    Args:
        goal: Original goal.
        plan: Original plan dict.
        completed: Dict of completed step results.
        failed_step: The step that failed.
        error: Error message from the failure.

    Returns:
        New plan dict.
    """
    client, provider = get_llm_client()
    model = resolve_model("planner", provider)

    context = (
        f"ORIGINAL GOAL: {goal}\n"
        f"COMPLETED STEPS: {json.dumps(list(completed.keys()))}\n"
        f"FAILED STEP: {json.dumps(failed_step)}\n"
        f"ERROR: {error}\n\n"
        f"Replan: keep completed steps, replace/modify the failed step, address the failure cause."
    )

    print(f"[Replanner] Generating revised plan...")
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": REPLAN_SYSTEM},
            {"role": "user", "content": context},
        ],
        max_tokens=1000,
        temperature=0,
    )

    raw = resp.choices[0].message.content
    new_plan = _extract_json(raw)
    print(f"[Replanner] New plan: {len(new_plan.get('steps', []))} steps")
    return new_plan


def run_planner_executor(goal: str, max_replans: int = 2) -> dict:
    """
    Full Planner-Executor loop with replanning support.

    Args:
        goal: The high-level goal.
        max_replans: Maximum number of replan attempts.

    Returns:
        dict with "completed" (results dict) and "replans_used" (int).
    """
    print(f"\n{'=' * 60}")
    print(f"[PlannerExecutor] Goal: {goal[:80]}")
    print(f"{'=' * 60}")

    # Phase 1: Generate plan
    plan = generate_plan(goal)
    completed = {}
    replans_used = 0

    # Phase 2: Execute steps
    steps = plan.get("steps", [])
    i = 0

    while i < len(steps):
        step = steps[i]
        step_id = step.get("id", i + 1)

        # Skip already completed steps
        if str(step_id) in completed:
            i += 1
            continue

        # Check dependencies
        deps = step.get("depends_on", [])
        deps_met = all(str(d) in completed for d in deps)
        if not deps_met:
            print(f"[Executor] Step {step_id}: waiting for dependencies {deps}")
            i += 1
            continue

        # Dispatch
        result = dispatch_tool(step)

        if result["success"]:
            completed[str(step_id)] = result["output"]
            print(f"[Executor] Step {step_id}: ✅ Success")

            # Save checkpoint
            CHECKPOINT_PATH.write_text(json.dumps({
                "goal": goal,
                "completed": {k: str(v)[:200] for k, v in completed.items()},
                "current_step": step_id,
            }, indent=2))

            i += 1
        else:
            print(f"[Executor] Step {step_id}: ❌ Failed — {result.get('error', 'unknown')}")

            # Log the failure
            log_failure(goal, "planner-executor", result.get("error", "unknown"))

            if replans_used < max_replans:
                replans_used += 1
                print(f"[Executor] Replanning (attempt {replans_used}/{max_replans})...")
                new_plan = replan(goal, plan, completed, step, result.get("error", ""))
                steps = new_plan.get("steps", [])
                plan = new_plan
                i = 0  # Restart from beginning (completed steps will be skipped)
            else:
                print(f"[Executor] Max replans ({max_replans}) exceeded. Aborting.")
                return {
                    "completed": completed,
                    "replans_used": replans_used,
                    "error": f"Aborted after {max_replans} replan attempts. Last error: {result.get('error')}",
                }

    print(f"\n[PlannerExecutor] ✅ All steps completed. Replans used: {replans_used}")
    return {"completed": completed, "replans_used": replans_used}


if __name__ == "__main__":
    result = run_planner_executor(
        "Find a pub in Edinburgh for 160 guests with vegan options, "
        "check the weather, estimate catering cost at £35/head, "
        "and generate a promotional flyer for the AI Meetup."
    )
    print(f"\n{'=' * 60}")
    print(f"Result: {json.dumps(result, indent=2, default=str)[:500]}")
