"""
src/week1/env_setup.py
======================
Week 1: Environment setup — Load .env, initialize LLM client, print provider info.
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from dotenv import load_dotenv
from src.llm_provider import get_llm_client, resolve_model

load_dotenv()


def setup() -> tuple:
    """Initialize and return (client, provider) with startup diagnostics."""
    client, provider = get_llm_client()
    print(f"[EnvSetup] Provider: {provider.upper()}")
    print(f"[EnvSetup] Speedster model: {resolve_model('speedster', provider)}")
    print(f"[EnvSetup] Worker model:    {resolve_model('worker', provider)}")
    print(f"[EnvSetup] Planner model:   {resolve_model('planner', provider)}")
    return client, provider


if __name__ == "__main__":
    client, provider = setup()
    print(f"\n[EnvSetup] ✅ Client initialized for {provider}")
