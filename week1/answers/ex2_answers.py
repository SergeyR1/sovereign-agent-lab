"""
Exercise 2 — Answers
====================
Fill this in after running exercise2_langgraph.py.
Run `python grade.py ex2` to check for obvious issues.
"""

# ── Task A ─────────────────────────────────────────────────────────────────

TASK_A_TOOLS_CALLED = [
    "check_pub_availability",
    "check_pub_availability",
    "get_edinburgh_weather",
    "calculate_catering_cost",
    "generate_event_flyer",
]

TASK_A_CONFIRMED_VENUE = "The Albanach"
TASK_A_CATERING_COST_GBP = 5600.0
TASK_A_OUTDOOR_OK = True

TASK_A_NOTES = """
Used Yandex Cloud yandexgpt/rc (via dual-provider fallback; Nebius returned 401).
The agent checked both The Albanach (capacity 180, vegan, available) and
The Haymarket Vaults (capacity 160, vegan, available) in parallel on the first turn.
It then called calculate_catering_cost and generate_event_flyer together on the
second turn. Weather returned 'Mainly clear' at 8.2C with outdoor_ok=True.
5 tool calls total across 2 agent turns — efficient parallel dispatch.
"""

# ── Task B ─────────────────────────────────────────────────────────────────

TASK_B_IMPLEMENTED = True
TASK_B_MODE = "placeholder"

TASK_B_IMAGE_URL = "https://placehold.co/1200x628/1a1a2e/eaeaea?text=The+Haymarket+Vaults+%7C+160+guests&id=2ef939fbbaf6"

TASK_B_PROMPT_USED = (
    "Professional event flyer for Edinburgh AI Meetup, tech professionals, "
    "modern venue at The Haymarket Vaults, Edinburgh. 160 guests tonight. "
    "Warm lighting, Scottish architecture background, clean modern typography."
)

TASK_B_WHY_AGENT_SURVIVED = """
The tool contract (success=True, prompt_used, image_url) was satisfied by both
the live and placeholder paths, so the agent loop never saw a failure and
continued normally — the fallback was transparent to the orchestration layer.
"""

# ── Task C ─────────────────────────────────────────────────────────────────

SCENARIO_1_PIVOT_MOMENT = """
The agent checked The Bow Bar and received meets_all_constraints: false because
the venue was full (capacity 80, status full). Without any human guidance, it
immediately called check_pub_availability for The Albanach and found it met all
requirements (capacity 180, vegan true, status available).
"""

SCENARIO_1_FALLBACK_VENUE = "The Albanach"

SCENARIO_2_HALLUCINATED = False

SCENARIO_2_FINAL_ANSWER = """
None of the known venues can accommodate 300 people. The closest is The Albanach
with a capacity of 180, which offers vegan options but falls short of the required
capacity.
"""

SCENARIO_3_TRIED_A_TOOL = False

SCENARIO_3_RESPONSE = "I'm sorry, but I don't have the capability to provide information about train schedules. You might want to check the National Rail Enquiries website or use a travel app for the most accurate and up-to-date information."

SCENARIO_3_ACCEPTABLE = """
This is the correct behaviour for a production booking assistant. The agent correctly
refused to hallucinate train times and instead directed the user to an authoritative
source (National Rail Enquiries). The alternative — inventing plausible-sounding train
times — would be dangerous in a system where users might act on the information. The
agent's refusal demonstrates the 'fail safely' principle: when a query falls outside
the tool registry, returning 'I don't know' is always safer than guessing.
"""

# ── Task D ─────────────────────────────────────────────────────────────────

TASK_D_MERMAID_OUTPUT = """
---
config:
  flowchart:
    curve: linear
---
graph TD;
\t__start__([<p>__start__</p>]):::first
\tagent(agent)
\ttools(tools)
\t__end__([<p>__end__</p>]):::last
\t__start__ --> agent;
\tagent -.-> __end__;
\tagent -.-> tools;
\ttools --> agent;
\tclassDef default fill:#f2f0ff,line-height:1.2
\tclassDef first fill-opacity:0
\tclassDef last fill:#bfb6fc
"""

TASK_D_COMPARISON = """
The LangGraph agent is a single loop with one decision point: the model chooses
which tool to call (or to give a final answer) at each iteration. The graph has
just three nodes: start → agent → tools → agent → end. The agent node IS the
decision logic — the LLM decides the path at runtime, and can chain any sequence
of tools in any order it discovers.

Rasa CALM flows.yml defines every task as an explicit, pre-declared flow with
named steps and slot-filling stages. The LLM picks which flow to activate, but
then follows the declared structure. It cannot invent new steps or call tools
not specified in the flow. This is the fundamental trade-off: LangGraph gives
flexibility (open-ended tool chaining) while Rasa gives auditability (every
possible path is visible in flows.yml before runtime).
"""

# ── Reflection ─────────────────────────────────────────────────────────────

MOST_SURPRISING = """
The most surprising behaviour was in Scenario 1. When The Bow Bar returned
meets_all_constraints: false, the agent autonomously pivoted to checking The Albanach
without any human guidance or explicit fallback logic in the prompt. It did this by
examining the structured JSON response — the 'meets_all_constraints' field told it the
venue failed, while the tool's schema listed other known venues. This demonstrated that
well-designed tool output schemas enable emergent recovery behaviour: the agent reasoned
about WHY a venue failed and decided what to try next based purely on the structured data
in the tool response. If the tool had returned a plain string like 'venue is full', the
agent would have had much less to work with for its recovery strategy.
"""
