"""
src/week2/edinburgh_orchestrator.py
====================================
Week 2: Composition demo — combines CLI + Functions + API tools in one agent loop.
Routes: grep local file → check availability → get weather → calculate cost.
"""

import json
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from dotenv import load_dotenv
from src.llm_provider import get_llm_client, resolve_model
from src.week2.cli_venue_search import search_venue_notes
from src.week2.edinburgh_functions import (
    check_pub_availability,
    calculate_catering_cost,
    get_booking_deadline,
)
from src.week2.edinburgh_apis import geocode_location, get_current_weather
from src.week2.sanitize import sanitize_tool_result

load_dotenv()

# ─── Unified tool map ─────────────────────────────────────────────────────────

TOOL_MAP = {
    "search_venue_notes": lambda **kw: json.dumps(search_venue_notes(**kw)),
    "check_pub_availability": lambda **kw: json.dumps(check_pub_availability(**kw)),
    "calculate_catering_cost": lambda **kw: json.dumps(calculate_catering_cost(**kw)),
    "get_booking_deadline": lambda **kw: json.dumps(get_booking_deadline(**kw)),
    "geocode_location": lambda **kw: json.dumps(geocode_location(**kw)),
    "get_current_weather": lambda **kw: json.dumps(get_current_weather(**kw)),
}

ALL_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_venue_notes",
            "description": "Search local venue notes file using grep. For static data only.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_pub_availability",
            "description": "Check if a named Edinburgh pub meets capacity and dietary requirements.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pub_name": {"type": "string"},
                    "required_capacity": {"type": "integer"},
                    "requires_vegan": {"type": "boolean"},
                },
                "required": ["pub_name", "required_capacity", "requires_vegan"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_catering_cost",
            "description": "Calculate total catering cost in GBP.",
            "parameters": {
                "type": "object",
                "properties": {
                    "guests": {"type": "integer"},
                    "price_per_head": {"type": "number"},
                },
                "required": ["guests", "price_per_head"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "geocode_location",
            "description": "Geocode a location name to latitude/longitude.",
            "parameters": {
                "type": "object",
                "properties": {"location": {"type": "string"}},
                "required": ["location"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get current weather at given coordinates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "latitude": {"type": "number"},
                    "longitude": {"type": "number"},
                },
                "required": ["latitude", "longitude"],
            },
        },
    },
]


def run_orchestrator(task: str, max_turns: int = 8) -> dict:
    """
    Multi-tool Edinburgh orchestrator — combines CLI, function, and API tools.

    Args:
        task: The user's task description.
        max_turns: Maximum number of reasoning turns.

    Returns:
        dict with final_answer, tool_calls_made, success.
    """
    client, provider = get_llm_client()
    model = resolve_model("worker", provider)

    messages = [
        {
            "role": "system",
            "content": (
                "You are an Edinburgh event planning assistant. "
                "Use the available tools to search venues, check availability, "
                "get weather, and calculate costs. "
                "Known venues: The Albanach, The Haymarket Vaults, The Guilford Arms, The Bow Bar. "
                "Provide a final answer when you have enough information."
            ),
        },
        {"role": "user", "content": task},
    ]

    tool_calls_made = []

    for turn in range(max_turns):
        print(f"\n--- Orchestrator Turn {turn + 1} ---")

        try:
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=ALL_TOOLS,
                temperature=0,
            )
        except Exception as e:
            print(f"[Orchestrator] LLM call failed: {e}")
            return {"final_answer": f"Error: {e}", "tool_calls_made": tool_calls_made, "success": False}

        msg = resp.choices[0].message

        if not msg.tool_calls:
            final = msg.content or ""
            print(f"[Orchestrator] Final: {final[:200]}...")
            return {"final_answer": final, "tool_calls_made": tool_calls_made, "success": True}

        messages.append(msg)
        for tc in msg.tool_calls:
            fn_name = tc.function.name
            fn_args = json.loads(tc.function.arguments)
            print(f"[ToolCall] {fn_name}({json.dumps(fn_args)[:100]})")
            tool_calls_made.append({"tool": fn_name, "args": fn_args})

            if fn_name in TOOL_MAP:
                raw_result = TOOL_MAP[fn_name](**fn_args)
                # Sanitize external API results
                if fn_name in ("geocode_location", "get_current_weather"):
                    result = sanitize_tool_result(raw_result)
                else:
                    result = raw_result
            else:
                result = json.dumps({"error": f"Unknown tool: {fn_name}"})

            print(f"[ToolResult] {result[:120]}...")
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })

    return {
        "final_answer": f"Error: max_turns ({max_turns}) exceeded",
        "tool_calls_made": tool_calls_made,
        "success": False,
    }


if __name__ == "__main__":
    print("Edinburgh Orchestrator Demo")
    print("=" * 60)
    result = run_orchestrator(
        "Find a pub in Edinburgh for 160 guests with vegan options, "
        "check the current weather, and calculate catering cost at £35/head."
    )
    print(f"\n[Final Answer]\n{result['final_answer']}")
    print(f"\n[Tools Called] {len(result['tool_calls_made'])}")
