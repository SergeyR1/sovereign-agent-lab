"""
src/week2/mcp_venue_server.py
==============================
Week 2, Lab 4: Edinburgh Venue MCP Server.

Exposes venue search, details, and booking window tools via MCP stdio transport.
"""

import json
from datetime import datetime
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("EdinburghVenueServer")

VENUES = {
    "The Albanach": {
        "capacity": 180,
        "vegan": True,
        "status": "available",
        "address": "2 Hunter Square, Edinburgh",
    },
    "The Haymarket Vaults": {
        "capacity": 160,
        "vegan": True,
        "status": "available",
        "address": "1 Dalry Road, Edinburgh",
    },
    "The Guilford Arms": {
        "capacity": 200,
        "vegan": False,
        "status": "available",
        "address": "1 West Register Street, Edinburgh",
    },
    "The Bow Bar": {
        "capacity": 80,
        "vegan": True,
        "status": "full",
        "address": "80 West Bow, Edinburgh",
    },
}


@mcp.tool()
def search_venues(min_capacity: int, requires_vegan: bool) -> str:
    """
    Search Edinburgh venues by minimum capacity and dietary requirements.
    Returns only venues that are currently available (status = available).
    """
    matches = [
        {"name": name, **info}
        for name, info in VENUES.items()
        if info["capacity"] >= min_capacity
        and (not requires_vegan or info["vegan"])
        and info["status"] == "available"
    ]
    return json.dumps({"matches": matches, "count": len(matches)})


@mcp.tool()
def get_venue_details(pub_name: str) -> str:
    """
    Get full details for a specific Edinburgh venue by exact name.
    """
    venue = VENUES.get(pub_name)
    if not venue:
        return json.dumps({
            "success": False,
            "error": f"Venue not found: '{pub_name}'",
            "known_venues": list(VENUES.keys()),
        })
    return json.dumps({"success": True, "name": pub_name, **venue})


@mcp.tool()
def check_booking_window() -> str:
    """
    Check if we are within the booking window (before 5 PM today).
    Returns hours remaining until the 5 PM cutoff.
    """
    now = datetime.now()
    deadline = now.replace(hour=17, minute=0, second=0, microsecond=0)
    remaining = (deadline - now).total_seconds() / 3600.0

    return json.dumps({
        "current_time": now.strftime("%H:%M"),
        "deadline": "17:00",
        "hours_remaining": round(remaining, 2),
        "within_window": remaining > 0,
    })


if __name__ == "__main__":
    print(f"Edinburgh Venue MCP Server | {len(VENUES)} venues | stdio transport")
    mcp.run(transport="stdio")
