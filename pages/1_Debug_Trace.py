"""Debug page: full trace of agent tool calls for the current conversation.

Reads st.session_state.turns (populated by the main chat page in app.py).
Shows, per turn, the user question and every tool call the agent made:
tool name, routing rule, arguments, and the raw return dict from db_tools.py
(before the LLM phrases it). The main chat page stays free of this detail.
"""

import streamlit as st

st.set_page_config(page_title="Tool Call Trace", page_icon=None)

st.title("Tool call trace")
st.caption("What the agent called behind each answer.")

turns = st.session_state.get("turns", [])

if not turns:
    st.info("No conversation yet. Ask something on the chat page first.")
else:
    for i, turn in enumerate(turns, start=1):
        st.markdown(f"### Turn {i}")
        st.markdown(f"**User:** {turn['question']}")

        trace = turn.get("trace") or []
        if not trace:
            st.info("No tool calls — agent responded directly.")
        else:
            for call in trace:
                label = f"{call['tool_name']} — {call.get('routing_rule', '(unmapped)')}"
                with st.expander(label):
                    st.markdown("**Arguments**")
                    st.json(call.get("arguments", {}))
                    st.markdown("**Raw result**")
                    st.json(call.get("result", {}))
        st.divider()
