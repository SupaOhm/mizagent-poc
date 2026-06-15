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
        "- `E009` — Quinn (Warehouse Manager, MizuMi)\n"
        "- `E012` — Reese (Brand Lead, Bomi)"
    )

    st.divider()
    st.subheader("Example prompts")
    examples = [
        "Who is Quinn and who do they report to?",
        "List all MizuMi products that are low on stock.",
        "How many days of supply does SKU MZ-SK-001 have?",
        "What needs reordering across the whole company?",
    ]
    for i, ex in enumerate(examples):
        if st.button(ex, key=f"ex_{i}", use_container_width=True):
            st.session_state.pending = ex

    st.divider()
    if st.button("🔄 New conversation", use_container_width=True):
        st.session_state.messages = []
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
            reply = agent.get_agent_response(
                user_input, st.session_state.session_id
            )
        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
