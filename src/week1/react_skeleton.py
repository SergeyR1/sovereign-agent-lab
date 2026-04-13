"""
src/week1/react_skeleton.py
============================
Week 1: Basic ReAct skeleton with web_search tool schema and orchestration loop.
"""

import json
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from dotenv import load_dotenv
from src.llm_provider import get_llm_client, resolve_model

load_dotenv()

# ─── Tool definitions ─────────────────────────────────────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for information. Returns relevant text snippets.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query string",
                    }
                },
                "required": ["query"],
            },
        },
    }
]


def fake_web_search(query: str) -> str:
    """
    Mock web search — returns hardcoded results for Edinburgh-related queries.

    Args:
        query: The search query string.

    Returns:
        JSON string with search results.
    """
    query_lower = query.lower()

    if "pub" in query_lower or "venue" in query_lower or "edinburgh" in query_lower:
        return json.dumps({
            "results": [
                {
                    "title": "Best Pubs in Edinburgh for Large Groups",
                    "snippet": (
                        "The Albanach (capacity 180, vegan menu, available) at 2 Hunter Square. "
                        "The Haymarket Vaults (capacity 160, vegan options, available) at 1 Dalry Road. "
                        "The Guilford Arms (capacity 200, no vegan, available) at 1 West Register Street. "
                        "The Bow Bar (capacity 80, vegan, currently full) at 80 West Bow."
                    ),
                }
            ]
        })
    elif "weather" in query_lower:
        return json.dumps({
            "results": [
                {
                    "title": "Edinburgh Weather Tonight",
                    "snippet": "Edinburgh: 12°C, partly cloudy, light wind. Outdoor seating possible.",
                }
            ]
        })
    elif "catering" in query_lower or "cost" in query_lower:
        return json.dumps({
            "results": [
                {
                    "title": "Edinburgh Event Catering Costs",
                    "snippet": "Average catering cost in Edinburgh: £30-40 per head for buffet, £50-70 for sit-down.",
                }
            ]
        })
    else:
        return json.dumps({"results": [{"title": "No results", "snippet": f"No results for: {query}"}]})


TOOL_MAP = {
    "web_search": fake_web_search,
}


def run_agent(task: str, max_turns: int = 5) -> str:
    """
    Basic ReAct orchestration loop.

    Args:
        task: The user's task description.
        max_turns: Maximum number of turns before aborting.

    Returns:
        The agent's final text response, or an error string on max_turns exceeded.
    """
    client, provider = get_llm_client()
    model = resolve_model("worker", provider)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant that can search the web. "
                "Use the web_search tool to find information. "
                "When you have enough information, provide a final answer."
            ),
        },
        {"role": "user", "content": task},
    ]

    for turn in range(max_turns):
        print(f"\n--- Turn {turn + 1} ---")

        try:
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=TOOLS,
                temperature=0,
            )
        except Exception as e:
            print(f"[Agent] LLM call failed: {e}")
            return f"Error: LLM call failed: {e}"

        msg = resp.choices[0].message

        # If no tool calls, return the content as final answer
        if not msg.tool_calls:
            final = msg.content or ""
            print(f"[Agent] Final answer: {final[:200]}...")
            return final

        # Process tool calls
        messages.append(msg)
        for tc in msg.tool_calls:
            fn_name = tc.function.name
            fn_args = json.loads(tc.function.arguments)
            print(f"[ToolCall] {fn_name}({json.dumps(fn_args)[:80]})")

            if fn_name in TOOL_MAP:
                result = TOOL_MAP[fn_name](**fn_args)
            else:
                result = json.dumps({"error": f"Unknown tool: {fn_name}"})

            print(f"[ToolResult] {result[:120]}...")
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })

    return f"Error: max_turns ({max_turns}) exceeded without final answer."


if __name__ == "__main__":
    print("ReAct Skeleton Demo")
    print("=" * 50)
    result = run_agent(
        "Find a pub in Edinburgh for 160 guests with vegan options. "
        "What's the best option?"
    )
    print(f"\n[Result] {result}")
