"""
src/week3/cot_demo.py
======================
Week 3: CoT vs Direct prompting comparison.

Edinburgh train problem:
1030 + 52min → Glasgow (arrive 1122), back at 1405 - 50min (depart 1315).
Time in Glasgow: 1122 to 1315 = 1 hour 53 minutes.
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from dotenv import load_dotenv
from src.llm_provider import get_llm_client, resolve_model

load_dotenv()

QUESTION = (
    "A train leaves Edinburgh Waverley at 10:30 and takes 52 minutes to reach Glasgow Queen Street. "
    "The return train arrives back in Edinburgh at 14:05, and the journey takes 50 minutes. "
    "How long did the traveller spend in Glasgow?"
)


def ask_direct() -> dict:
    """Ask the question with direct prompting (no CoT)."""
    client, provider = get_llm_client()
    model = resolve_model("speedster", provider)

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Answer concisely."},
            {"role": "user", "content": QUESTION},
        ],
        max_tokens=200,
        temperature=0,
    )
    return {
        "answer": resp.choices[0].message.content.strip(),
        "tokens": resp.usage.total_tokens,
        "approach": "direct",
        "model": model,
    }


def ask_cot() -> dict:
    """Ask the question with Chain-of-Thought prompting."""
    client, provider = get_llm_client()
    model = resolve_model("speedster", provider)

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Think step by step before answering."},
            {"role": "user", "content": QUESTION},
        ],
        max_tokens=500,
        temperature=0,
    )
    return {
        "answer": resp.choices[0].message.content.strip(),
        "tokens": resp.usage.total_tokens,
        "approach": "chain_of_thought",
        "model": model,
    }


def run_comparison() -> dict:
    """Run both approaches and compare."""
    print("CoT vs Direct Prompting Comparison")
    print("=" * 60)
    print(f"\nQuestion: {QUESTION}\n")

    direct = ask_direct()
    print(f"[DIRECT] ({direct['tokens']} tokens)")
    print(f"  {direct['answer']}\n")

    cot = ask_cot()
    print(f"[COT] ({cot['tokens']} tokens)")
    print(f"  {cot['answer']}\n")

    print(f"Token difference: CoT used {cot['tokens'] - direct['tokens']} more tokens")
    print(f"Expected answer: 1 hour 53 minutes (113 minutes)")

    return {"direct": direct, "cot": cot}


if __name__ == "__main__":
    run_comparison()
