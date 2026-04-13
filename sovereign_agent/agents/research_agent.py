"""
sovereign_agent/agents/research_agent.py
=========================================
The Research Agent for your Sovereign Agent project.

This is the file that grows across the module:

  Week 1 (now):      Basic ReAct loop with 4 venue tools
  Week 2 session:    Add real web search and file operation tools
                     (feeds into the final assignment — no separate homework)
  Final assignment:  Becomes the executor inside PyNanoClaw. A planner
                     runs upstream, memory runs alongside, a handoff bridge
                     routes human-conversation tasks to the Rasa half.
                     Observability, cost tracking, and safety guardrails land.

The public interface — run_research_agent(task, max_turns) → dict — stays the
same throughout. Later code imports and calls this function exactly as Week 1
leaves it. You add capability inside; the callers don't change.

────────────────────────────────────────────────────────────────────────────
NOTE ON THE MODEL CHOICE  (updated 2026-04-09)
────────────────────────────────────────────────────────────────────────────
The first version of this file used meta-llama/Llama-3.3-70B-Instruct. That
model is excellent at reasoning but, on the Nebius Token Factory endpoint,
it does not reliably emit native `tool_calls` objects — it tends to emit the
tool call as a stringified JSON blob inside `content`, which LangGraph's
ReAct loop cannot consume directly. You would see traces like this:

    [AI] "{\"type\": \"function\", \"name\": \"check_pub_availability\", ...}"
    ⚠️  No tool calls were made.

We have switched to `Qwen/Qwen3-32B`, which natively supports the OpenAI
tool-calling spec on Nebius and works out of the box with `create_react_agent`.

We have also made the result parser below robust to BOTH formats, so if you
experiment with a different model and it emits the older stringified-JSON
shape, your trace will still be captured correctly instead of coming back
empty. That defensive parsing is how the Week-2/3/4 code will stay stable
as you try different models.
────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import json
import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from sovereign_agent.tools.venue_tools import (
    calculate_catering_cost,
    check_pub_availability,
    generate_event_flyer,
    get_edinburgh_weather,
)

load_dotenv()

# ─── Model ────────────────────────────────────────────────────────────────────
# Qwen3-32B on Nebius natively supports tool_calls. If you want to try another
# model, good alternatives that also emit correct tool_calls on Nebius and
# survived the 2026-04-13 deprecation round are:
#   - nvidia/nemotron-3-super-120b-a12b
#   - Qwen/Qwen3-Next-80B-A3B-Thinking
#
# Avoid:
#   - meta-llama/Llama-3.3-70B-Instruct for anything that needs tools on
#     this provider — see note at the top of the file.
#   - deepseek-ai/DeepSeek-R1-0528 — deprecated 2026-04-13, no longer served.
#   - Any model suffixed `_fast` in the Qwen, Llama, or DeepSeek families —
#     also deprecated 2026-04-13. See CHANGELOG.md §Fixed for the full list.

RESEARCH_MODEL = os.getenv("RESEARCH_MODEL", "Qwen/Qwen3-32B")

# Dual-provider: Yandex Cloud (if configured) > Nebius Token Factory
_yandex_key = os.getenv("YANDEX_CLOUD_API_KEY", "").strip()
_yandex_url = os.getenv("YANDEX_BASE_URL", "").strip()
_yandex_folder = os.getenv("YANDEX_CLOUD_FOLDER", "").strip()

if _yandex_key and _yandex_url and _yandex_folder:
    llm = ChatOpenAI(
        base_url=_yandex_url,
        api_key=_yandex_key,
        model=f"gpt://{_yandex_folder}/yandexgpt/rc",
        temperature=0,
    )
else:
    llm = ChatOpenAI(
        base_url="https://api.tokenfactory.nebius.com/v1/",
        api_key=os.getenv("NEBIUS_KEY"),
        model=RESEARCH_MODEL,
        temperature=0,
    )

# ─── Tool registry ────────────────────────────────────────────────────────────
# Week 1: 4 venue tools
# Week 2: add search_web, read_file, write_file here

TOOLS = [
    check_pub_availability,
    get_edinburgh_weather,
    calculate_catering_cost,
    generate_event_flyer,
]

# Build the agent once at module load time.
_agent = create_react_agent(llm, TOOLS)


# ─── Defensive tool-call extraction ───────────────────────────────────────────
# This helper understands two shapes:
#
#   (a) LangChain native:  message.tool_calls is a list of
#         {"name": ..., "args": {...}, "id": ...}
#       Every compliant provider (Qwen, DeepSeek, Nemotron, OpenAI, Anthropic)
#       populates this. It is the format the ReAct loop uses internally.
#
#   (b) Stringified-JSON-in-content:  older Llama models on Nebius return
#       something like:
#         content = "[\"{\\\"type\\\": \\\"function\\\", \\\"name\\\": ..."
#       This is not a tool call the loop can act on, but we still want to
#       SEE it in the trace so you can diagnose "why did no tool run".
#
# Returning both lets us keep the instructor-facing trace honest even when
# students swap models for experimentation.

def _extract_tool_calls_from_message(m) -> list[dict]:
    out: list[dict] = []

    # (a) Native LangChain tool_calls — preferred path.
    native = getattr(m, "tool_calls", None) or []
    for tc in native:
        if isinstance(tc, dict):
            out.append({"tool": tc.get("name", ""), "args": tc.get("args", {}) or {}})
        else:
            out.append({"tool": getattr(tc, "name", ""), "args": getattr(tc, "args", {}) or {}})
    if out:
        return out

    # (b) Fallback: stringified JSON embedded in content.
    content = getattr(m, "content", "")
    if not isinstance(content, str):
        return out
    stripped = content.strip()
    if not (stripped.startswith("[") or stripped.startswith("{")):
        return out
    try:
        parsed = json.loads(stripped)
    except (json.JSONDecodeError, ValueError):
        return out

    items = parsed if isinstance(parsed, list) else [parsed]
    for item in items:
        # Sometimes it is double-encoded: list of JSON strings.
        if isinstance(item, str):
            try:
                item = json.loads(item)
            except (json.JSONDecodeError, ValueError):
                continue
        if not isinstance(item, dict):
            continue
        if item.get("type") not in ("function", "tool_use", "tool_call"):
            continue
        name = (
            item.get("name")
            or item.get("function", {}).get("name", "")
            or ""
        )
        args = (
            item.get("parameters")
            or item.get("arguments")
            or item.get("input")
            or {}
        )
        if name:
            out.append({"tool": name, "args": args})
    return out


# ─── Public interface ─────────────────────────────────────────────────────────

def run_research_agent(task: str, max_turns: int = 8) -> dict:
    """
    Run the research agent on a task and return a structured result.

    Args:
        task:      Natural language task description
        max_turns: Maximum number of reasoning turns before giving up

    Returns:
        dict with keys:
          final_answer:    str — the agent's final response
          tool_calls_made: list of dicts — each tool call with name and args
          full_trace:      list of dicts — every message in the conversation
          success:         bool — True if agent gave a final answer

    This return shape is the contract that Week 2+ code depends on.
    Do not change the key names.
    """
    result = _agent.invoke(
        {"messages": [("user", task)]},
        config={"recursion_limit": max_turns * 2},
    )

    tool_calls_made: list[dict] = []
    full_trace: list[dict] = []
    final_answer = ""

    for m in result["messages"]:
        msg_type = getattr(m, "type", "unknown")
        content = m.content

        # Capture tool calls (native or fallback).
        calls = _extract_tool_calls_from_message(m)
        for c in calls:
            tool_calls_made.append(c)
            full_trace.append({"role": "tool_call", **c})

        # Capture tool RESULTS — these are ToolMessages that come back from
        # the executed tools. Showing them in the trace is what makes the
        # trace actually useful: you can see what the tool returned, not
        # just that it was called.
        if msg_type == "tool":
            result_text = str(content) if content is not None else ""
            full_trace.append(
                {
                    "role": "tool_result",
                    "tool": getattr(m, "name", "unknown"),
                    "content": result_text[:600],
                }
            )
            continue

        # Capture the model's natural-language messages.
        if isinstance(content, str) and content and not calls:
            full_trace.append({"role": msg_type, "content": content})
            if msg_type == "ai":
                final_answer = content

    return {
        "final_answer": final_answer,
        "tool_calls_made": tool_calls_made,
        "full_trace": full_trace,
        "success": bool(final_answer),
    }