"""
src/week3/react_agent.py
=========================
Week 3: ReAct agent built from scratch — no framework, just LLM + tools + regex parsing.

Uses strict Thought/Action/Observation format with stop-token control.
"""

import json
import os
import re
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from dotenv import load_dotenv
from src.llm_provider import get_llm_client, resolve_model

load_dotenv()

# ─── Mock tools ───────────────────────────────────────────────────────────────


def mock_web_search(query: str) -> str:
    """
    Mock web search with hardcoded Edinburgh/Ethiopia data.

    Args:
        query: Search query string.

    Returns:
        String with search results.
    """
    q = query.lower()
    if "edinburgh marathon" in q or "2025 edinburgh" in q:
        return (
            "The 2025 Edinburgh Marathon was won by Hailemichael Gidey from Ethiopia "
            "with a time of 2:12:45. The women's race was won by Tigist Memuye, "
            "also from Ethiopia, in 2:28:12."
        )
    elif "ethiopia" in q and "population" in q:
        return (
            "Ethiopia has an estimated population of approximately 126 million people "
            "as of 2025, making it the second most populous country in Africa "
            "after Nigeria."
        )
    elif "edinburgh" in q:
        return (
            "Edinburgh is the capital of Scotland with a population of about 500,000. "
            "It is famous for its historic castle, cultural festivals, and architecture."
        )
    else:
        return f"No specific results found for: {query}"


def calculator(expression: str) -> str:
    """
    Safe calculator — only allows digits, operators, parentheses, and decimal points.

    Args:
        expression: Mathematical expression to evaluate.

    Returns:
        String with the result or an error message.
    """
    # Allowlist: only 0-9, ., +, -, *, /, (, ), and whitespace
    if not re.match(r'^[\d\.\+\-\*\/\(\)\s]+$', expression):
        return f"Error: unsafe characters in expression: {expression}"
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {e}"


TOOL_MAP = {
    "web_search": mock_web_search,
    "calculator": calculator,
}

# ─── ReAct system prompt ──────────────────────────────────────────────────────

REACT_SYSTEM = """You are a research assistant that answers questions using tools.

You have access to these tools:
- web_search[query]: Search the web for information
- calculator[expression]: Evaluate a mathematical expression

You MUST follow this EXACT format for every step:

Thought: <your reasoning about what to do next>
Action: <tool_name>[<argument>]

After each Action, you will receive an Observation with the result.

When you have enough information to answer, respond with:
Thought: I now have enough information to answer.
Final Answer: <your complete answer>

IMPORTANT: 
- Always start with a Thought.
- Only use one Action per step.
- Wait for the Observation before your next Thought.
- The action format must be exactly: tool_name[argument]"""


def react_agent(task: str, max_turns: int = 8) -> str:
    """
    ReAct agent from scratch — uses regex to parse actions, dispatches tools.

    Args:
        task: The user's question or task.
        max_turns: Maximum number of Thought/Action/Observation cycles.

    Returns:
        The agent's final answer string.
    """
    client, provider = get_llm_client()
    model = resolve_model("worker", provider)

    # Build conversation with the full history
    conversation = f"Question: {task}\n"

    for turn in range(max_turns):
        print(f"\n--- ReAct Turn {turn + 1} ---")

        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": REACT_SYSTEM},
                {"role": "user", "content": conversation},
            ],
            max_tokens=500,
            temperature=0,
            stop=["Observation:"],
        )

        output = resp.choices[0].message.content.strip()
        print(f"[LLM Output]\n{output}")

        # Check for Final Answer
        final_match = re.search(r'Final Answer:\s*(.+)', output, re.DOTALL)
        if final_match:
            answer = final_match.group(1).strip()
            print(f"\n[Final Answer] {answer}")
            return answer

        # Parse Action: tool_name[argument]
        action_match = re.search(r'Action:\s*(\w+)\[([^\]]*)\]', output)
        if action_match:
            tool_name = action_match.group(1)
            tool_arg = action_match.group(2)
            print(f"[Action] {tool_name}[{tool_arg}]")

            if tool_name in TOOL_MAP:
                observation = TOOL_MAP[tool_name](tool_arg)
            else:
                observation = f"Error: unknown tool '{tool_name}'"

            print(f"[Observation] {observation[:200]}")
            conversation += f"{output}\nObservation: {observation}\n"
        else:
            # No action found — LLM might have given answer without proper format
            conversation += f"{output}\n"
            # Try to extract any useful answer
            if "Final Answer:" not in output and turn == max_turns - 1:
                return output

    return f"Error: max_turns ({max_turns}) exceeded without final answer."


if __name__ == "__main__":
    print("ReAct Agent from Scratch")
    print("=" * 60)
    answer = react_agent(
        "Who won the 2025 Edinburgh Marathon and what is the approximate "
        "population of their home country?"
    )
    print(f"\n{'=' * 60}")
    print(f"Answer: {answer}")
