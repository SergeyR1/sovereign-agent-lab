"""
src/week1/lost_in_the_middle.py
================================
Week 1: Lost-in-the-Middle demonstration (Liu et al., 2023).

Tests whether LLMs retrieve information better from start/end of context
versus the middle — the U-shaped recall curve phenomenon.
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from dotenv import load_dotenv
from src.llm_provider import get_llm_client, resolve_model

load_dotenv()

NEEDLE = "The secret code is PINEAPPLE42."

# ~900 chars of repetitive noise filler
FILLER = (
    "This is background information about various topics. "
    "Edinburgh is known for its historic architecture and cultural festivals. "
    "The city has many restaurants and pubs serving local and international cuisine. "
    "The weather in Scotland is often unpredictable with frequent rain showers. "
    "Many tourists visit Edinburgh Castle which overlooks the city from Castle Rock. "
    "The Royal Mile connects Edinburgh Castle to the Palace of Holyroodhouse. "
    "Arthur's Seat is an ancient volcano in the heart of the city. "
    "The Edinburgh Festival Fringe is the world's largest arts festival. "
    "Scottish cuisine features dishes like haggis, neeps and tatties. "
    "The Forth Bridge is a cantilever railway bridge across the Firth of Forth. "
    "Scotland has a rich history of whisky production dating back centuries. "
    "The University of Edinburgh is one of the oldest universities in the English-speaking world. "
)


def build_context(position: str) -> str:
    """
    Place the NEEDLE at start, middle, or end of the context.
    
    Args:
        position: One of "start", "middle", "end"
    
    Returns:
        Context string with needle placed at the specified position.
    """
    if position == "start":
        return f"{NEEDLE}\n{FILLER}\n{FILLER}"
    elif position == "middle":
        return f"{FILLER}\n{NEEDLE}\n{FILLER}"
    elif position == "end":
        return f"{FILLER}\n{FILLER}\n{NEEDLE}"
    else:
        raise ValueError(f"Unknown position: {position}")


def ask(position: str) -> str:
    """
    Ask the LLM to find the secret code, with the needle placed at `position`.

    Args:
        position: One of "start", "middle", "end"

    Returns:
        The model's response string.
    """
    client, provider = get_llm_client()
    model = resolve_model("speedster", provider)

    context = build_context(position)
    prompt = (
        f"Read the following text carefully and find the secret code.\n\n"
        f"{context}\n\n"
        f"What is the secret code? Reply with only the code, nothing else."
    )

    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=50,
        temperature=0,
    )
    answer = resp.choices[0].message.content.strip()
    return answer


def run_demo() -> dict:
    """Run the Lost-in-the-Middle demo for all three positions."""
    results = {}
    for pos in ["start", "middle", "end"]:
        answer = ask(pos)
        correct = "PINEAPPLE42" in answer.upper()
        results[pos] = {"answer": answer, "correct": correct}
        icon = "✅" if correct else "❌"
        print(f"  [{pos.upper():<6}] {icon}  → \"{answer}\"")
    return results


if __name__ == "__main__":
    print("Lost-in-the-Middle Demo")
    print("=" * 50)
    run_demo()
