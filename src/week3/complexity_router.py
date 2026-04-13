"""
src/week3/complexity_router.py
===============================
Week 3: Complexity router — classifies queries as SIMPLE or COMPLEX.

COMPLEX → Planner-Executor architecture
SIMPLE  → Basic ReAct loop (1-2 tool calls max)
"""

COMPLEX_KEYWORDS = [
    "plan", "compare", "itinerary", "schedule", "find and then",
    "step by step", "multiple", "coordinate", "recommend", "organise",
    "organize", "book", "reserve",
]

SIMPLE_KEYWORDS = [
    "what is", "what time", "how far", "where is", "who is",
    "define", "when does", "how much",
]


def route_query(query: str) -> str:
    """
    Classify a query as SIMPLE or COMPLEX based on keyword matching.

    Args:
        query: The user's query string.

    Returns:
        "SIMPLE" or "COMPLEX".
    """
    q = query.lower()

    # Check simple keywords first
    for kw in SIMPLE_KEYWORDS:
        if kw in q:
            # But override if complex keywords also present
            for ckw in COMPLEX_KEYWORDS:
                if ckw in q:
                    return "COMPLEX"
            return "SIMPLE"

    # Check complex keywords
    for kw in COMPLEX_KEYWORDS:
        if kw in q:
            return "COMPLEX"

    # Default: COMPLEX (safe fallback — better to over-plan than under-plan)
    return "COMPLEX"


if __name__ == "__main__":
    test_queries = [
        "Find a pub for 160 guests with vegan options and book it",
        "What is the weather in Edinburgh?",
        "Plan an event for 160 people with catering and a flyer",
        "How much does catering cost?",
        "Compare The Albanach and The Haymarket Vaults",
        "Where is Edinburgh Castle?",
        "Organise a pub crawl through Edinburgh Old Town",
        "Schedule a meeting for tomorrow",
    ]

    print("Complexity Router Demo")
    print("=" * 60)
    for q in test_queries:
        route = route_query(q)
        print(f"  [{route:<7}] {q}")
