"""
src/llm_provider.py
====================
Dual-provider LLM abstraction: Yandex Cloud (primary) / Nebius Token Factory (fallback).

Usage:
    from src.llm_provider import get_llm_client, resolve_model

    client, provider = get_llm_client()
    model = resolve_model("worker", provider)
    resp = client.chat.completions.create(model=model, messages=[...])
"""

import os
from openai import OpenAI


def get_llm_client() -> tuple:
    """
    Returns (OpenAI-compatible client, provider_name).
    Priority: Yandex Cloud (if env vars set) > Nebius Token Factory (fallback).
    """
    yandex_key = os.getenv("YANDEX_CLOUD_API_KEY", "").strip()
    yandex_url = os.getenv("YANDEX_BASE_URL", "").strip()
    yandex_folder = os.getenv("YANDEX_CLOUD_FOLDER", "").strip()

    if yandex_key and yandex_url and yandex_folder:
        client = OpenAI(
            api_key=yandex_key,
            base_url=yandex_url,
        )
        provider = "yandex"
    else:
        nebius_key = os.getenv("NEBIUS_KEY", "").strip()
        if not nebius_key:
            nebius_key = os.getenv("NEBIUS_API_KEY", "").strip()
        client = OpenAI(
            base_url="https://api.tokenfactory.nebius.com/v1",
            api_key=nebius_key,
        )
        provider = "nebius"

    return client, provider


def resolve_model(role: str, provider: str) -> str:
    """
    Maps a logical model role to the actual model ID for the active provider.

    Roles: "planner", "worker", "speedster", "coder", "guardrail", "default"

    Updated 2026-04-13: removed deprecated Nebius models (Meta-Llama-3.1-8B,
    Llama-Guard-3-8B, FLUX). See CHANGELOG.md for details.
    """
    # Respect instructor override via RESEARCH_MODEL env var
    env_override = os.getenv("RESEARCH_MODEL", "").strip()
    if env_override and role in ("worker", "default"):
        return env_override

    folder = os.getenv("YANDEX_CLOUD_FOLDER", "")

    NEBIUS_MODELS = {
        "planner":   "Qwen/Qwen3-235B-A22B-Thinking-2507",
        "worker":    "Qwen/Qwen3-32B",
        "speedster": "google/gemma-2-2b-it",
        "coder":     "Qwen/Qwen3-235B-A22B-Instruct-2507",
        "guardrail": "google/gemma-2-2b-it",
        "default":   "Qwen/Qwen3-32B",
    }
    YANDEX_MODELS = {
        "planner":   f"gpt://{folder}/gpt-oss-120b/latest",
        "worker":    f"gpt://{folder}/yandexgpt/rc",
        "speedster": f"gpt://{folder}/yandexgpt-lite/latest",
        "coder":     f"gpt://{folder}/gpt-oss-120b/latest",
        "guardrail": f"gpt://{folder}/yandexgpt-lite/latest",
        "default":   f"gpt://{folder}/yandexgpt/rc",
    }

    if provider == "yandex":
        return YANDEX_MODELS.get(role, YANDEX_MODELS["worker"])
    return NEBIUS_MODELS.get(role, NEBIUS_MODELS["worker"])


def get_yandex_headers() -> dict:
    """Returns extra headers needed for Yandex Cloud API calls."""
    folder = os.getenv("YANDEX_CLOUD_FOLDER", "")
    if folder:
        return {"x-folder-id": folder}
    return {}
