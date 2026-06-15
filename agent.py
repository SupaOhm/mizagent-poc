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
import os

from db_tools import (
    calculate_stock_coverage,
    get_employee_record,
    get_low_stock_items,
    query_products,
    search_employees,
)

APP_NAME = "mizuhada_internal_poc"
MODEL = "gemini-2.0-flash"

SYSTEM_INSTRUCTION = """\
You are the Mizuhada internal assistant (POC). You help staff with org-chart
lookups and warehouse/inventory questions across three brands (MizuMi, Bomi, GS)
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
    async for event in runner.run_async(
        user_id=_DEFAULT_USER, session_id=session_id, new_message=message
    ):
        if event.is_final_response() and event.content and event.content.parts:
            reply = "".join(p.text or "" for p in event.content.parts)
    return reply.strip()


def get_agent_response(user_message, session_id):
    """Run the agent for one turn and return the final text reply (string).

    This is the entry point the Streamlit app calls. Conversation history is
    kept in-process per session_id.
    """
    if not os.getenv("GOOGLE_API_KEY"):
        return (
            "GOOGLE_API_KEY is not set. Copy .env.example to .env and add your "
            "key, then restart the app."
        )
    try:
        return asyncio.run(_respond(session_id, user_message))
    except Exception as exc:  # POC: surface errors instead of crashing the UI
        return f"Agent error: {exc}"


async def _run_query(runner, user_id, session_id, text):
    from google.genai import types

    print(f"\n>>> USER: {text}")
    message = types.Content(role="user", parts=[types.Part(text=text)])
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=message
    ):
        if event.is_final_response() and event.content and event.content.parts:
            reply = "".join(p.text or "" for p in event.content.parts)
            print(f"<<< AGENT: {reply.strip()}")


async def _amain():
    from google.adk.runners import InMemoryRunner

    agent = build_agent()
    runner = InMemoryRunner(agent=agent, app_name=APP_NAME)

    user_id = "demo_user"
    session = await runner.session_service.create_session(
        app_name=APP_NAME, user_id=user_id
    )

    # Test queries use ONLY placeholder seed names (never real people).
    queries = [
        "Who is Quinn and who do they report to?",
        "List all MizuMi products that are low on stock.",
        "How many days of supply does SKU MZ-SK-001 have?",
        "What needs reordering across the whole company right now?",
    ]
    for q in queries:
        await _run_query(runner, user_id, session.id, q)


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
