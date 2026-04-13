"""
src/week2/edinburgh_functions.py
=================================
Week 2, Lab 2: In-process function tools for the Edinburgh agent.
"""

import json
from datetime import datetime, timedelta

# ─── Venue database ───────────────────────────────────────────────────────────

VENUES = {
    "The Albanach": {
        "capacity": 180,
        "vegan": True,
        "status": "available",
        "address": "2 Hunter Square, Edinburgh",
    },
    "The Guilford Arms": {
        "capacity": 200,
        "vegan": False,
        "status": "available",
        "address": "1 West Register Street, Edinburgh",
    },
    "The Haymarket Vaults": {
        "capacity": 160,
        "vegan": True,
        "status": "available",
        "address": "1 Dalry Road, Edinburgh",
    },
    "The Bow Bar": {
        "capacity": 80,
        "vegan": True,
        "status": "full",
        "address": "80 West Bow, Edinburgh",
    },
}


def check_pub_availability(pub_name: str, required_capacity: int, requires_vegan: bool) -> dict:
    """
    Check if a named Edinburgh pub meets capacity and dietary requirements.

    Args:
        pub_name: Exact name of the pub to check.
        required_capacity: Minimum number of guests the venue must hold.
        requires_vegan: Whether vegan menu is required.

    Returns:
        dict with success, venue details, and meets_all_constraints.
    """
    venue = VENUES.get(pub_name)
    if not venue:
        return {
            "success": False,
            "error": f"Venue not found: '{pub_name}'",
            "known_venues": list(VENUES.keys()),
        }

    meets_all = (
        venue["capacity"] >= required_capacity
        and (not requires_vegan or venue["vegan"])
        and venue["status"] == "available"
    )

    return {
        "success": True,
        "pub_name": pub_name,
        "address": venue["address"],
        "capacity": venue["capacity"],
        "vegan": venue["vegan"],
        "status": venue["status"],
        "meets_all_constraints": meets_all,
    }


def calculate_catering_cost(guests: int, price_per_head: float) -> dict:
    """
    Estimate total catering cost in GBP.

    Args:
        guests: Number of guests.
        price_per_head: Cost per person in GBP.

    Returns:
        dict with success, total_cost_gbp, and input parameters.
    """
    if guests <= 0 or price_per_head < 0:
        return {
            "success": False,
            "error": "guests must be > 0 and price_per_head must be >= 0",
        }
    return {
        "success": True,
        "guests": guests,
        "price_per_head_gbp": price_per_head,
        "total_cost_gbp": round(guests * price_per_head, 2),
    }


def get_booking_deadline(event_date: str) -> dict:
    """
    Calculate hours remaining until the 5 PM booking cutoff.

    Args:
        event_date: Date string in YYYY-MM-DD format.

    Returns:
        dict with success, deadline, hours_remaining, is_past_deadline.
    """
    try:
        date = datetime.strptime(event_date, "%Y-%m-%d")
        deadline = date.replace(hour=17, minute=0, second=0)
        now = datetime.now()
        remaining = (deadline - now).total_seconds() / 3600.0

        return {
            "success": True,
            "deadline": deadline.isoformat(),
            "hours_remaining": round(remaining, 2),
            "is_past_deadline": remaining <= 0,
        }
    except ValueError as e:
        return {"success": False, "error": f"Invalid date format: {e}"}


# ─── Tool dispatch map ────────────────────────────────────────────────────────

TOOL_MAP = {
    "check_pub_availability": check_pub_availability,
    "calculate_catering_cost": calculate_catering_cost,
    "get_booking_deadline": get_booking_deadline,
}

# Tool schemas for LLM tool calling
FUNCTION_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "check_pub_availability",
            "description": "Check if a named Edinburgh pub meets capacity and dietary requirements.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pub_name": {"type": "string", "description": "Exact pub name to check"},
                    "required_capacity": {"type": "integer", "description": "Minimum guest capacity"},
                    "requires_vegan": {"type": "boolean", "description": "Whether vegan menu is required"},
                },
                "required": ["pub_name", "required_capacity", "requires_vegan"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_catering_cost",
            "description": "Calculate total catering cost in GBP for an event.",
            "parameters": {
                "type": "object",
                "properties": {
                    "guests": {"type": "integer", "description": "Number of guests"},
                    "price_per_head": {"type": "number", "description": "Cost per person in GBP"},
                },
                "required": ["guests", "price_per_head"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_booking_deadline",
            "description": "Check hours remaining until the 5 PM booking cutoff for a given date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_date": {"type": "string", "description": "Event date in YYYY-MM-DD format"},
                },
                "required": ["event_date"],
            },
        },
    },
]


if __name__ == "__main__":
    print("Edinburgh Functions Demo")
    print("=" * 50)

    r1 = check_pub_availability("The Albanach", 160, True)
    print(f"\n[check_pub_availability] The Albanach → {json.dumps(r1, indent=2)}")

    r2 = calculate_catering_cost(160, 35.0)
    print(f"\n[calculate_catering_cost] 160 × £35 → {json.dumps(r2, indent=2)}")

    today = datetime.now().strftime("%Y-%m-%d")
    r3 = get_booking_deadline(today)
    print(f"\n[get_booking_deadline] {today} → {json.dumps(r3, indent=2)}")
