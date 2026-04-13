"""
Exercise 4 — Answers
====================
Fill this in after running exercise4_mcp_client.py.
"""

# ── Basic results ──────────────────────────────────────────────────────────

TOOLS_DISCOVERED = ["search_venues", "get_venue_details"]

QUERY_1_VENUE_NAME    = "The Albanach"
QUERY_1_VENUE_ADDRESS = "2 Hunter Square, Edinburgh"
QUERY_2_FINAL_ANSWER  = "Unfortunately, there are no venues available in Edinburgh that can accommodate 300 people and offer vegan options at the moment. You might want to consider either reducing the number of guests or relaxing the dietary requirements."

# ── The experiment ─────────────────────────────────────────────────────────

EX4_EXPERIMENT_DONE = True

EX4_EXPERIMENT_RESULT = """
Changed The Albanach's status from 'available' to 'full' in mcp_venue_server.py.
Re-ran exercise4_mcp_client.py. Query 1 now returned only The Haymarket Vaults
(capacity 160, vegan, available) as the best match — The Albanach was filtered out
by the MCP server's search_venues tool before the agent ever saw it. The agent code
(exercise4_mcp_client.py) was NOT modified at all. Only the server data changed.
This demonstrates the core MCP value: data and logic live on the server, clients
consume the results dynamically. Reverted the change after the experiment.
"""

# ── MCP vs hardcoded ───────────────────────────────────────────────────────

LINES_OF_TOOL_CODE_EX2 = 85
LINES_OF_TOOL_CODE_EX4 = 12

MCP_VALUE_PROPOSITION = """
MCP provides dynamic tool discovery and a standard transport protocol that decouples
the tool implementation from the tool consumer. Beyond just moving code to a separate
file, MCP allows multiple heterogeneous clients (LangGraph, Rasa, any MCP-compatible
agent) to connect to the same server and discover tools at runtime. When the server
adds a new tool or changes venue data, all clients pick it up automatically — no
client code changes needed. This is the same principle as a web API vs hardcoded
functions, but with a standardised schema discovery protocol that enables true
plug-and-play tool sharing between agents.
"""

# ── PyNanoClaw architecture — SPECULATION QUESTION ─────────────────────────

WEEK_5_ARCHITECTURE = """
- The Planner (a strong-reasoning model such as Qwen3-235B-Thinking or gpt-oss-120b) receives the raw task and produces an ordered list of subgoals with dependency edges. It lives upstream of the ReAct loop in the autonomous-loop half of PyNanoClaw, so the Executor never sees an ambiguous task — only concrete, tool-aligned steps.
- The Executor (Qwen3-32B or yandexgpt, fast and reliable at tool calling) dispatches each plan step to the tool registry via the ReAct loop from Exercise 2. It lives in the autonomous-loop half and handles failure recovery by requesting replans from the Planner when a step fails.
- The MCP Venue Server (sovereign_agent/tools/mcp_venue_server.py) is the shared data layer between both halves. The research agent (Exercise 4 client) and the Rasa confirmation agent both connect to the same MCP server, ensuring they operate on identical venue data without any synchronisation overhead.
- The Rasa CALM Confirmation Agent (Exercise 3) handles the structured half — the pub-manager callback where every word has legal/financial weight. It enforces hard business rules in Python (deposit limits, capacity checks, cutoff guard) and uses CALM flows for auditable, bounded conversations. A Handoff Bridge routes the conversation from the autonomous loop to Rasa when the task transitions from open-ended research to structured confirmation.
- The CLAUDE.md Memory Layer persists search results, confirmed bookings, and agent failure logs to the filesystem so the agent can learn from past sessions. The Planner reads this memory at plan-generation time, injecting relevant warnings from previous failures into its prompt. This shared memory layer bridges both halves.
- The Observability Pipeline (LangSmith) traces every LLM call, tool invocation, and planning decision across both halves, enabling post-hoc auditing and cost tracking for the full PyNanoClaw system.
- The Complexity Router classifies incoming tasks as SIMPLE or COMPLEX: simple queries (e.g. 'what is the weather?') are routed directly to the ReAct loop without Planner involvement, saving reasoning tokens for tasks that genuinely require multi-step planning.
"""

# ── The guiding question ───────────────────────────────────────────────────

GUIDING_QUESTION_ANSWER = """
The research — finding venues, checking weather, estimating costs, generating
flyers — belongs to the LangGraph Headless Automator. In Exercise 2, the agent
autonomously pivoted from The Bow Bar (full, capacity 80) to The Albanach without
human guidance. It chained five tools across two turns in an order it discovered
at runtime. This open-ended exploration is exactly what the research problem demands.

The call from the pub manager belongs to the Rasa CALM Confirmation Agent. In
Exercise 3, the ActionValidateBooking enforced a hard deposit limit of £300 that
the LLM could not override. When the manager proposed £500, Python escalated
immediately. No amount of conversational persuasion could change that outcome.

Swapping them would fail because: if Rasa handled the research, it could not
discover an alternative venue that was not pre-declared in flows.yml — when The
Bow Bar was full, there would be no flow step for 'try another venue'. If LangGraph
handled the confirmation call, the LLM might reason that a £500 deposit is acceptable
for a particularly good venue — it would negotiate rather than enforce. The
fundamental asymmetry is that research requires creative exploration while
confirmation requires deterministic enforcement. Using the wrong architecture
creates either rigidity where flexibility is needed, or flexibility where
rigidity is essential.
"""
