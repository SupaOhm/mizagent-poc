"""Streamlit chat UI for the Mizuhada Internal AI Agent POC (Project 2).

Run:
    python seed_db.py        # build mock_company.db
    streamlit run app.py
"""

import uuid

import streamlit as st

import agent

st.set_page_config(page_title="Internal Agent - POC", page_icon="🤖")

st.title("Internal Agent - POC")
st.caption(
    "⚠️ Demo only — runs on a mock SQLite database with fictional data. "
    "No authentication, no real records."
)

# --- Session state ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "turns" not in st.session_state:
    # One entry per user turn: {"question": str, "trace": list}. Read by the
    # 🔍 Debug Trace page; never rendered on this chat page.
    st.session_state.turns = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "pending" not in st.session_state:
    st.session_state.pending = None

# --- Sidebar ---
with st.sidebar:
    st.header("What this agent can do")
    st.markdown(
        "- **search_employees** — find staff by name and/or team\n"
        "- **get_employee_record** — full record + manager for an employee_id\n"
        "- **query_products** — filter products by brand / category / stock status\n"
        "- **calculate_stock_coverage** — days of supply for a SKU\n"
        "- **get_low_stock_items** — products below their reorder point"
    )

    st.divider()
    st.subheader("Try personal-data queries")
    st.markdown(
        "Employee IDs look like `E001`–`E023`. Examples you can use:\n"
        "- `E004` — Ohm (Dev Intern, IT/AI)\n"
        "- `E009` — Quinn (Warehouse Manager, Mihihi)\n"
        "- `E012` — Reese (Brand Lead, Bobi)"
    )

    st.divider()
    st.subheader("Example prompts")

    st.caption("Single tool")
    single_tool = [
        "Who is in the Warehouse team for Mihihi?",
        "What are the contact details for employee E005?",
        "Show me all Harshcolor products.",
        "How many days of stock do we have left for SKU BB-WL-005?",
        "Which Bobi products need restocking?",
    ]
    for i, ex in enumerate(single_tool):
        if st.button(ex, key=f"ex_s_{i}", use_container_width=True):
            st.session_state.pending = ex

    st.caption("Multi-tool chains")
    multi_tool = [
        "Who is Quinn and who do they report to?",
        "What is Morgan's role and what is their email address?",
        "Find Reese's manager and give me their phone number.",
        "Which Mihihi products are low on stock, and how many days of supply does the worst one have?",
        "List all Harshcolor items below reorder point — and how long will Lip Tint (HC-CO-002) last at current sales?",
    ]
    for i, ex in enumerate(multi_tool):
        if st.button(ex, key=f"ex_m_{i}", use_container_width=True):
            st.session_state.pending = ex

    st.divider()
    if st.button("🔄 New conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.turns = []
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.pending = None
        st.rerun()

# --- Render history ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Input (chat box or clicked example) ---
typed = st.chat_input("Ask about staff or inventory…")
user_input = typed or st.session_state.pending
st.session_state.pending = None

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            reply, trace = agent.get_agent_response(
                user_input, st.session_state.session_id
            )
        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
    # Stash the tool-call trace for the debug page (not shown here).
    st.session_state.turns.append({"question": user_input, "trace": trace})
