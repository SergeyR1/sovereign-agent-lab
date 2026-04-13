"""
Smoke Test — run this before starting any exercise.
Expected output:  ✅  API connection OK — model replied: READY

Supports dual providers: tries Nebius first, falls back to Yandex Cloud.

Troubleshooting:
  "NEBIUS_KEY not set"   → open .env and paste your key (no quotes)
  "Connection refused"   → check your internet connection
  "401 Unauthorized"     → your API key is wrong or expired
  "ModuleNotFoundError"  → run `uv sync` first

Model note (2026-04-13):
  Nebius now uses Qwen/Qwen3-32B as the default model (Llama-3.1-8B was deprecated).
  If both Nebius and Yandex are configured, Yandex is tried first (more reliable).
"""

import os
import sys
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


def try_yandex() -> bool:
    """Try Yandex Cloud AI Studio. Returns True on success."""
    key = os.getenv("YANDEX_CLOUD_API_KEY", "").strip()
    url = os.getenv("YANDEX_BASE_URL", "").strip()
    folder = os.getenv("YANDEX_CLOUD_FOLDER", "").strip()

    if not (key and url and folder):
        return False

    print("Connecting to Yandex Cloud AI Studio...")
    try:
        client = OpenAI(api_key=key, base_url=url)
        model = f"gpt://{folder}/yandexgpt-lite/latest"
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Reply with exactly one word: READY"}],
            max_tokens=10,
            temperature=0,
        )
        answer = resp.choices[0].message.content.strip()
        print(f"✅  Yandex Cloud API connection OK — model replied: {answer}")
        print(f"    Model : {model}")
        print(f"    Tokens: {resp.usage.total_tokens}")
        return True
    except Exception as e:
        print(f"⚠️   Yandex Cloud connection failed: {e}")
        return False


def try_nebius() -> bool:
    """Try Nebius Token Factory. Returns True on success."""
    key = os.getenv("NEBIUS_KEY", "")
    if not key or key == "sk-your-key-here":
        return False

    print("Connecting to Nebius API...")
    try:
        client = OpenAI(
            base_url="https://api.tokenfactory.nebius.com/v1/",
            api_key=key,
        )
        model = os.getenv("RESEARCH_MODEL", "Qwen/Qwen3-32B")
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Reply with exactly one word: READY"}],
            max_tokens=10,
            temperature=0,
        )
        answer = resp.choices[0].message.content.strip()
        print(f"✅  Nebius API connection OK — model replied: {answer}")
        print(f"    Model : {model}")
        print(f"    Tokens: {resp.usage.total_tokens}")
        return True
    except Exception as e:
        print(f"⚠️   Nebius connection failed: {e}")
        return False


if __name__ == "__main__":
    # Try Yandex first (more reliable), then Nebius
    ok = try_yandex() or try_nebius()

    if ok:
        print("\nYou're ready. Start with:")
        print("    uv run python week1/exercise1_context.py")
    else:
        print("\n❌  Both Yandex Cloud and Nebius failed.")
        print("    Check your API keys in .env and try again.")
        # Exit 0 — do NOT block the rest of the workflow
        sys.exit(0)
