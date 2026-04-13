# PyNanoClaw Agent — Knowledge Base

## What Was Built

Three weeks of incremental agent development, building Project A (The Headless Automator) for the Edinburgh event planning scenario.

**Week 1 — Foundations & ReAct Skeleton**
- Environment setup with dual LLM provider abstraction (Yandex Cloud / Nebius Token Factory)
- Lost-in-the-Middle demo validating Liu et al. (2023) findings on context formatting
- Basic ReAct skeleton with tool schemas and orchestration loop
- Implemented `generate_event_flyer` in `sovereign_agent/tools/venue_tools.py` (the main TODO)
- Completed all 4 exercises: Context Engineering, LangGraph Agent, Rasa CALM (analysis), MCP Server
- Uncommented cutoff guard in Rasa actions (Task B)
- Filled all answer files with analysis from actual runs

**Week 2 — Tools & MCP Servers**
- CLI tool: safe grep wrapper for local venue file search (no `shell=True`)
- In-process functions: pub availability, catering cost, booking deadline
- External APIs: Open-Meteo geocoding + weather with exponential backoff
- MCP Server: FastMCP venue server with stdio transport
- A2A Booking Agent: Flask app implementing the A2A protocol
- XML sanitization: strip HTML comments, truncate, wrap in safe tags
- Edinburgh Orchestrator: combines all 5 tool paradigms in one agent loop

**Week 3 — Reasoning & Planning**
- CoT vs Direct prompting comparison (Edinburgh train problem)
- ReAct agent from scratch: regex-parsed Thought/Action/Observation loop
- Planner-Executor architecture with replanning support
- Complexity router: keyword-based SIMPLE/COMPLEX classification
- Evaluation harness with 5 Edinburgh-themed tasks and --dry-run mode
- Failure log with keyword-matched warning injection into Planner prompts
- Parallel executor using asyncio.gather for independent steps

## Repository Structure

```
sovereign-agent-lab/
├── .env                           # API keys (gitignored)
├── .env.example                   # Template with instructions
├── Makefile                       # Build targets (install, smoke, run-agent, grade)
├── pyproject.toml                 # Dependencies and tool config
├── smoke_test.py                  # Dual-provider connectivity test
├── venues.txt                     # Edinburgh venue data
├── AGENT_KNOWLEDGE.md             # ← This file
├── GRADING_OVERVIEW.md            # 100-point grading rubric
├── PROGRESS.md                    # 5-week course roadmap
│
├── sovereign_agent/               # Persistent agent package (grows each week)
│   ├── agents/
│   │   └── research_agent.py      # LangGraph ReAct agent with dual-provider LLM
│   ├── tools/
│   │   ├── venue_tools.py         # 4 @tool functions (availability, weather, cost, flyer)
│   │   └── mcp_venue_server.py    # FastMCP server (search, details, booking window)
│   └── tests/
│       └── test_week1.py          # 15 unit tests for tool implementations
│
├── week1/                         # Exercise scripts and answers
│   ├── exercise1_context.py       # Context engineering benchmark
│   ├── exercise2_langgraph.py     # LangGraph research agent tasks
│   ├── exercise4_mcp_client.py    # MCP client consuming venue server
│   ├── grade.py                   # Mechanical grade checker (64/64 ✅)
│   ├── answers/
│   │   ├── ex1_answers.py         # Context formatting observations
│   │   ├── ex2_answers.py         # Agent behaviour analysis
│   │   ├── ex3_answers.py         # Rasa CALM analysis
│   │   └── ex4_answers.py         # MCP experiment results
│   └── outputs/
│       ├── ex1_results.json       # Context benchmark results
│       ├── ex2_results.json       # LangGraph agent traces
│       └── ex4_results.json       # MCP client results
│
├── src/                           # Week 2-3 implementations (PyNanoClaw)
│   ├── llm_provider.py            # Dual-provider abstraction (get_llm_client, resolve_model)
│   ├── pynano_claw.py             # Main agent entrypoint with heartbeat loop
│   ├── week1/
│   │   ├── env_setup.py           # Environment diagnostics
│   │   ├── lost_in_the_middle.py  # LitM demo
│   │   └── react_skeleton.py      # Basic ReAct with fake_web_search
│   ├── week2/
│   │   ├── cli_venue_search.py    # Safe grep wrapper
│   │   ├── edinburgh_functions.py # In-process function tools
│   │   ├── edinburgh_apis.py      # Open-Meteo geocoding + weather
│   │   ├── mcp_venue_server.py    # MCP server with booking window
│   │   ├── a2a_booking_server.py  # A2A Flask booking agent
│   │   ├── sanitize.py            # XML sanitization for tool outputs
│   │   └── edinburgh_orchestrator.py  # Multi-tool composition demo
│   └── week3/
│       ├── cot_demo.py            # CoT vs Direct comparison
│       ├── react_agent.py         # ReAct from scratch
│       ├── planner_executor.py    # Planner-Executor architecture
│       ├── complexity_router.py   # SIMPLE/COMPLEX routing
│       ├── eval_harness.py        # 5-task evaluation with --dry-run
│       ├── failure_log.py         # Failure logging + warning injection
│       └── parallel_executor.py   # Async parallel step execution
│
└── exercise3_rasa/                # Rasa Pro CALM (Project B, not main scope)
    └── actions/actions.py         # Cutoff guard uncommented (Task B)
```

## Agent Architecture

### The Headless Automator Pattern

PyNanoClaw operates autonomously: receive task → plan → execute → return results.
No human in the loop during execution. The heartbeat loop processes tasks sequentially.

```
                    ┌──────────────────┐
                    │   Heartbeat Loop  │
                    │   (always-on)     │
                    └─────────┬────────┘
                              │
                    ┌─────────▼────────┐
                    │ Complexity Router │
                    │  SIMPLE/COMPLEX  │
                    └──┬───────────┬───┘
                       │           │
              ┌────────▼──┐  ┌────▼──────────┐
              │  ReAct     │  │   Planner     │
              │  (1-2      │  │ (reasoning    │
              │   tools)   │  │   model)      │
              └────────────┘  └────┬──────────┘
                                   │
                             ┌─────▼──────────┐
                             │   Executor      │
                             │ (dispatches to  │
                             │  tool registry) │
                             └────┬──────┬─────┘
                                  │      │
                    ┌─────────────▼──┐   │ on failure
                    │  Tool Registry  │   │
                    │  CLI | Func |   │   ▼
                    │  API | MCP      │  Replan
                    └─────────────────┘
```

### Planner-Executor Split

| Component | Model | Purpose |
|-----------|-------|---------|
| Planner | DeepSeek R1 / gpt-oss-120b | Generates JSON plan with dependency graph |
| Executor | Llama 70B / yandexgpt | Dispatches steps to tools, handles failures |
| Router | Keyword-based | Classifies queries to avoid over-planning simple tasks |

### Tool Registry

| Tool Name | Paradigm | Purpose | Week |
|-----------|----------|---------|------|
| search_venue_notes | CLI (grep) | Search local venue file | 2 |
| check_pub_availability | In-process | Check venue constraints | 1, 2 |
| calculate_catering_cost | In-process | Estimate event costs | 1, 2 |
| get_booking_deadline | In-process | Hours until 5 PM cutoff | 2 |
| geocode_location | External API | Open-Meteo geocoding | 2 |
| get_current_weather | External API | Open-Meteo forecast | 2 |
| search_venues (MCP) | MCP Server | Filter venues by criteria | 1, 2 |
| get_venue_details (MCP) | MCP Server | Full venue info | 1, 2 |
| check_booking_window (MCP) | MCP Server | Time-based availability | 2 |
| generate_event_flyer | Image API | FLUX.1 / Yandex fallback | 1 |

## LLM Provider Abstraction

The `src/llm_provider.py` module provides seamless switching between providers:

```python
from src.llm_provider import get_llm_client, resolve_model

client, provider = get_llm_client()  # Returns "yandex" or "nebius"
model = resolve_model("worker", provider)  # Maps role → model ID
```

### Model Mapping Table

| Role | Nebius Token Factory | Yandex Cloud AI Studio |
|------|---------------------|----------------------|
| planner | Qwen/Qwen3-235B-A22B-Thinking-2507 | gpt://{folder}/gpt-oss-120b/latest |
| worker | meta-llama/Llama-3.3-70B-Instruct | gpt://{folder}/yandexgpt/rc |
| speedster | meta-llama/Llama-3.1-8B-Instruct | gpt://{folder}/yandexgpt-lite/latest |
| coder | Qwen/Qwen3-235B-A22B-Instruct-2507 | gpt://{folder}/gpt-oss-120b/latest |
| guardrail | meta-llama/Llama-Guard-3-8B | gpt://{folder}/yandexgpt-lite/latest |

**Priority:** Yandex Cloud (if all 3 env vars set) → Nebius Token Factory (fallback).

## Key Papers Referenced in Lectures

| Paper | Authors | Year | Key Finding | Relevance |
|-------|---------|------|-------------|-----------|
| Lost in the Middle | Liu et al. | 2023 | U-shaped recall curve; middle of context = worst recall | Context engineering for agents |
| Chain-of-Thought Prompting | Wei et al. | 2022 | CoT improves multi-step reasoning in LLMs | Agent planning strategy |
| Self-Consistency | Wang et al. | 2023 | Majority voting over N reasoning chains improves robustness | Reliability in agents |
| Tree of Thoughts | Yao et al. | 2023 | Branching search over reasoning paths; solved 74% vs 4% for CoT on Game of 24 | Strategic planning |
| ReAct | Yao et al. | 2023 | Interleaving Reasoning + Acting reduces hallucination | Core agent loop design |
| Reflexion | Shinn et al. | 2023 | Verbal self-reflection improves across-episode learning | Failure recovery |
| DeepSeek-R1 | DeepSeek-AI | 2025 | Pure RL training produces emergent reasoning and self-verification | Reasoning model selection |
| Scaling LLM Test-Time Compute | Snell et al. | 2024 | 7B model with 100x inference compute matches 70B model | Efficiency vs cost trade-off |
| Vanishing Attention | arXiv | 2025 | Max attention weight → 0 as context grows; 1M token window ≠ 1M memory | Long-context agent design |
| Kimi K2.5 | Kimi Team | 2026 | Visual agentic intelligence, 200+ sequential tool calls | Long-horizon planning |

## Security Considerations

### The Lethal Trifecta

The agent has all three conditions for a dangerous system:
1. **Private data access** — reads venue databases, calculates costs
2. **Untrusted external content** — web search results, API responses
3. **External communication capability** — can generate flyers, send confirmations

### Mitigations Implemented

- **Input sanitization** (`src/week2/sanitize.py`): Strip HTML comments, truncate, wrap in `<tool_result is_untrusted="true">` tags
- **No `shell=True`**: CLI tools use subprocess with explicit argument lists
- **max_turns guard**: Every agent loop has a hard cap (default 8 turns)
- **Structured errors**: Tools return `{"success": False, "error": "..."}` instead of raising exceptions
- **Financial guardrails**: Rasa actions enforce deposit limits with Python, not prompts
- **XML wrapping**: All external API results sanitized before injection into LLM context

## Future Work (Weeks 4–5)

- **Week 4: RAG & Memory**
  - CLAUDE.md filesystem memory for cross-session persistence
  - Vector stores for semantic search over past bookings and venue reviews
  - Memory-aware planning: inject relevant past context into Planner prompts

- **Week 5: Production Safety**
  - LangSmith observability: trace every LLM call and tool invocation
  - Cost tracking and budget enforcement per session
  - Live demo: end-to-end Edinburgh booking with WhatsApp trigger
  - Human-in-the-loop for destructive actions (actual bookings, payments)
