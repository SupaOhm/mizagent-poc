"""Streamlit chat UI for the Mizuhada Internal AI Agent POC (Project 2).

Run:
    python seed_db.py        # build mock_company.db
    streamlit run app.py
"""

import uuid

import streamlit as st

import agent

st.set_page_config(page_title="Mizuhada Internal Agent", page_icon=None)

st.markdown("""
<style>
/* Sidebar section eyebrows */
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
    text-transform: uppercase;
    letter-spacing: 0.09em;
    font-size: 0.65rem;
    color: #999;
    margin-top: 0.75rem;
    margin-bottom: 0.15rem;
}

/* Example prompt buttons */
[data-testid="stSidebar"] .stButton > button {
    background: transparent;
    border: 1px solid #e2e2e2;
    text-align: left;
    justify-content: flex-start;
    font-size: 0.82rem;
    color: #2c2c2c;
    padding: 0.35rem 0.65rem;
    border-radius: 3px;
    font-weight: 400;
    line-height: 1.4;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #f7f7f7;
    border-color: #bbb;
    color: #111;
}

/* Tool list in sidebar */
[data-testid="stSidebar"] li {
    font-size: 0.85rem;
    line-height: 1.6;
}

/* Monospace for IDs */
code {
    font-size: 0.8em;
}
</style>
""", unsafe_allow_html=True)

st.title("Mizuhada Internal Agent")
st.caption("POC — mock SQLite database, fictional data, no authentication.")

# --- Session state ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "turns" not in st.session_state:
    # One entry per user turn: {"question": str, "trace": list}. Read by the
    # Debug Trace page; never rendered on this chat page.
    st.session_state.turns = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "pending" not in st.session_state:
    st.session_state.pending = None

# --- Sidebar ---
with st.sidebar:
    st.markdown(
        '<div style="height:2px;background:#B8A99A;margin-bottom:1.1rem;border-radius:1px;"></div>',
        unsafe_allow_html=True,
    )
    st.header("What this agent can do")
    st.markdown(
        "- **search_employees** — find staff by name or team\n"
        "- **get_employee_record** — full record and manager chain for an ID\n"
        "- **query_products** — filter products by brand, category, or stock status\n"
        "- **calculate_stock_coverage** — days of supply remaining for a SKU\n"
        "- **get_low_stock_items** — products below their reorder point"
    )

    st.divider()
    st.subheader("Employee lookup")
    st.markdown(
        "IDs run `E001`–`E023`. Quick references:\n"
        "- `E004` — Ohm, Dev Intern, IT/AI\n"
        "- `E009` — Quinn, Warehouse Manager, Mihihi\n"
        "- `E012` — Reese, Brand Lead, Bobi"
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
    if st.button("Clear chat", use_container_width=True):
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
