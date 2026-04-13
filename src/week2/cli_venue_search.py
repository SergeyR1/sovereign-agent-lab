"""
src/week2/cli_venue_search.py
==============================
Week 2, Lab 1: CLI tool — safe grep wrapper for venue file search.
"""

import json
import os
import subprocess
from pathlib import Path


# ─── Workspace setup ──────────────────────────────────────────────────────────

WORKSPACE = Path("/tmp/edinburgh_workspace")
VENUE_FILE = WORKSPACE / "venues.txt"

VENUES_DATA = """\
The Albanach | capacity: 180 | vegan: yes | address: 2 Hunter Square, Edinburgh | status: available
The Haymarket Vaults | capacity: 160 | vegan: yes | address: 1 Dalry Road, Edinburgh | status: available
The Guilford Arms | capacity: 200 | vegan: no | address: 1 West Register Street, Edinburgh | status: available
The Bow Bar | capacity: 80 | vegan: yes | address: 80 West Bow, Edinburgh | status: full
The Ensign Ewart | capacity: 120 | vegan: yes | address: 14 Lawnmarket, Edinburgh | status: available
The Holyrood 9A | capacity: 150 | vegan: yes | address: 9A Holyrood Road, Edinburgh | status: available
"""


def ensure_workspace() -> None:
    """Create the workspace directory and venues.txt if they don't exist."""
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    if not VENUE_FILE.exists():
        VENUE_FILE.write_text(VENUES_DATA)
        print(f"[CLI] Created {VENUE_FILE}")


def search_venue_notes(query: str) -> dict:
    """
    Safe grep wrapper for searching the venues file.

    Args:
        query: Search term to grep for (case-insensitive).

    Returns:
        dict with keys: success (bool), matches (list[str]), count (int), error (str|None).

    Security: No shell=True, timeout=5, output capped at 8192 bytes.
    Do NOT use this for live data — it searches a static local file only.
    """
    ensure_workspace()

    if not VENUE_FILE.exists():
        return {"success": False, "matches": [], "count": 0, "error": "venues.txt not found"}

    try:
        result = subprocess.run(
            ["grep", "-i", "--", query, str(VENUE_FILE)],
            capture_output=True,
            text=True,
            timeout=5,
        )

        stdout = result.stdout[:8192]
        matches = [line.strip() for line in stdout.splitlines() if line.strip()]

        return {
            "success": True,
            "matches": matches,
            "count": len(matches),
            "error": None,
        }

    except subprocess.TimeoutExpired:
        return {"success": False, "matches": [], "count": 0, "error": "grep timed out after 5 seconds"}
    except Exception as e:
        return {"success": False, "matches": [], "count": 0, "error": str(e)}


# Tool schema for LLM tool calling
SEARCH_VENUE_NOTES_SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_venue_notes",
        "description": (
            "Search the local Edinburgh venue notes file using grep. "
            "Returns matching lines from venues.txt. Case-insensitive. "
            "Do NOT use for live data — searches a static local file only."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The text to search for in venue notes (e.g., 'vegan', 'available', pub name)",
                }
            },
            "required": ["query"],
        },
    },
}


if __name__ == "__main__":
    ensure_workspace()
    print("CLI Venue Search Demo")
    print("=" * 50)
    for q in ["vegan", "available", "Albanach", "capacity: 200"]:
        result = search_venue_notes(q)
        print(f"\n  Query: '{q}' → {result['count']} match(es)")
        for m in result["matches"]:
            print(f"    {m}")
