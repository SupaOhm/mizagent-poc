"""Function-calling agent layer for the Mizuhada Internal AI Agent POC (Project 2).

Google ADK LlmAgent (Gemini 2.0 Flash) wired to the 5 read-only db_tools.
No-auth POC: no login, no permissions; intended for local demo only.

Setup:
    pip install google-adk
    export GOOGLE_API_KEY=...        # required to actually run queries
    python seed_db.py                # build mock_company.db first
    python agent.py

The agent NEVER does arithmetic itself: every number comes from a tool result.
"""

import asyncio
import json
import os

from dotenv import load_dotenv

load_dotenv()  # read GOOGLE_API_KEY and DEBUG from .env

DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

from db_tools import (
    calculate_stock_coverage,
    get_employee_record,
    get_low_stock_items,
    query_products,
    search_employees,
)

APP_NAME = "mizuhada_internal_poc"
MODEL = "gemini-3.1-flash-lite"

# Maps each tool to the lettered routing rule it implements in SYSTEM_INSTRUCTION.
# Used by the debug page to show which rule fired for each call.
TOOL_ROUTING = {
    "search_employees": "(a) People/org lookup",
    "get_employee_record": "(a) People/org lookup",
    "query_products": "(b) Simple product filter",
    "calculate_stock_coverage": "(c) Stock coverage calculation",
    "get_low_stock_items": "(d) Low-stock / reorder check",
}

SYSTEM_INSTRUCTION = """\
You are the Mizuhada internal assistant (POC). You help staff with org-chart
lookups and warehouse/inventory questions across three brands (Mihihi, Bobi, Harshcolor)
plus Corporate. You answer ONLY from tool results — never from prior knowledge or
guesses.

ROUTING RULES:
a. People / org questions: first call search_employees to resolve a name or team
   into an employee_id, then call get_employee_record for full details
   (role, team, brand, manager, contact).
b. Simple product filters (by brand / category / low|ok stock): use query_products.
c. "Days of supply" / "how long will stock last" questions: ALWAYS call
   calculate_stock_coverage. NEVER compute the stock/sales ratio yourself.
d. "What's running low" / "what needs reordering": ALWAYS call get_low_stock_items.
   NEVER scan query_products output by hand to decide what is low.
e. Any numeric value you report (days of supply, shortfall, counts) MUST come from
   a tool result. Do NOT do arithmetic in your reasoning.
f. If a tool returns found:false or an empty result set, say so plainly. Never
   invent an employee, product, or number that a tool did not return.
g. No-auth POC: if the user asks about "my" personal data (e.g. "who is my
   manager") and no employee_id is known, ask them for their employee_id first
   before calling any tool.
h. Reply in the same language as the user (Thai or English).
"""


def build_agent():
    """Construct the LlmAgent. Imports ADK lazily so the module loads without it."""
    from google.adk.agents import LlmAgent

    return LlmAgent(
        name="mizuhada_assistant",
        model=MODEL,
        instruction=SYSTEM_INSTRUCTION,
        tools=[
            search_employees,
            get_employee_record,
            query_products,
            calculate_stock_coverage,
            get_low_stock_items,
        ],
    )


# --- Streamlit-facing API -------------------------------------------------
# Lazily-built singletons so the Streamlit app reuses one runner across reruns
# and keeps per-session_id conversation history in memory.
_RUNNER = None
_KNOWN_SESSIONS = set()
_DEFAULT_USER = "streamlit_user"
# Most recent turn's tool-call trace, keyed by session_id (for the debug page).
_LAST_TRACE = {}


def _get_runner():
    global _RUNNER
    if _RUNNER is None:
        from google.adk.runners import InMemoryRunner

        _RUNNER = InMemoryRunner(agent=build_agent(), app_name=APP_NAME)
    return _RUNNER


async def _ensure_session(runner, session_id):
    if session_id in _KNOWN_SESSIONS:
        return
    await runner.session_service.create_session(
        app_name=APP_NAME, user_id=_DEFAULT_USER, session_id=session_id
    )
    _KNOWN_SESSIONS.add(session_id)


async def _respond(session_id, user_message):
    from google.genai import types

    runner = _get_runner()
    await _ensure_session(runner, session_id)

    message = types.Content(role="user", parts=[types.Part(text=user_message)])
    reply = ""
    # Collect tool calls + their raw return dicts straight from the event stream
    # (the runner already dispatches the tools — we only read what it emits).
    pending_calls = []  # FIFO of {tool_name, arguments} awaiting their response
    trace = []
    async for event in runner.run_async(
        user_id=_DEFAULT_USER, session_id=session_id, new_message=message
    ):
        for call in event.get_function_calls() or []:
            pending_calls.append(
                {"tool_name": call.name, "arguments": dict(call.args or {})}
            )
        for resp in event.get_function_responses() or []:
            entry = _match_call(pending_calls, resp.name)
            entry["result"] = resp.response
            entry["routing_rule"] = TOOL_ROUTING.get(resp.name, "(unmapped)")
            trace.append(entry)
        if event.is_final_response() and event.content and event.content.parts:
            reply = "".join(p.text or "" for p in event.content.parts)
    return reply.strip(), trace


def _match_call(pending_calls, name):
    """Pop the earliest pending call matching `name` to pair it with its response."""
    for i, call in enumerate(pending_calls):
        if call["tool_name"] == name:
            return pending_calls.pop(i)
    return {"tool_name": name, "arguments": {}}


def _print_trace(session_id, user_message, trace, reply):
    SEP = "─" * 45
    print(SEP)
    print(f"[AGENT TURN] session={session_id}")
    print(f"USER: {user_message}")
    if trace:
        for i, entry in enumerate(trace, 1):
            print(f"\n[TOOL CALL {i}]")
            print(f"  Tool:         {entry['tool_name']}")
            print(f"  Routing rule: {entry.get('routing_rule', '(unmapped)')}")
            print(f"  Arguments:    {json.dumps(entry.get('arguments', {}), ensure_ascii=False)}")
            print(f"  Result:       {json.dumps(entry.get('result', {}), ensure_ascii=False, indent=2)}")
    else:
        print("\n[NO TOOL CALLS]")
    print(f"\nRESPONSE: {reply}")
    print(SEP)


def get_agent_response(user_message, session_id):
    """Run the agent for one turn.

    Returns a (reply_text, trace) tuple. `trace` is a list of one dict per tool
    call: {tool_name, arguments, result, routing_rule}. The entry point the
    Streamlit app calls; conversation history is kept in-process per session_id.
    """
    if not os.getenv("GOOGLE_API_KEY"):
        return (
            "GOOGLE_API_KEY is not set. Copy .env.example to .env and add your "
            "key, then restart the app.",
            [],
        )
    try:
        reply, trace = asyncio.run(_respond(session_id, user_message))
    except Exception as exc:  # POC: surface errors instead of crashing the UI
        return f"Agent error: {exc}", []
    _LAST_TRACE[session_id] = trace
    if DEBUG:
        _print_trace(session_id, user_message, trace, reply)
    return reply, trace


async def _amain():
    from google.adk.runners import InMemoryRunner

    global _RUNNER, _KNOWN_SESSIONS
    agent = build_agent()
    _RUNNER = InMemoryRunner(agent=agent, app_name=APP_NAME)

    session = await _RUNNER.session_service.create_session(
        app_name=APP_NAME, user_id=_DEFAULT_USER
    )
    _KNOWN_SESSIONS.add(session.id)

    # Test queries use ONLY placeholder seed names (never real people).
    queries = [
        "Who is Quinn and who do they report to?",
        "List all Mihihi products that are low on stock.",
        "How many days of supply does SKU MH-SK-001 have?",
        "What needs reordering across the whole company right now?",
    ]
    for q in queries:
        reply, trace = await _respond(session.id, q)
        if DEBUG:
            _print_trace(session.id, q, trace, reply)
        else:
            print(f"\n>>> USER: {q}")
            print(f"<<< AGENT: {reply}")


def main():
    if not os.getenv("GOOGLE_API_KEY"):
        print(
            "WARNING: GOOGLE_API_KEY not set. "
            "Set it to run live queries:\n"
            "    export GOOGLE_API_KEY=...\n"
            "Skipping agent run."
        )
        return
    asyncio.run(_amain())


if __name__ == "__main__":
    main()
