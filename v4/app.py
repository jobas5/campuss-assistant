"""Campus Assistant v3 chat UI — the agent shows its steps.   streamlit run app.py"""
import streamlit as st

import asyncio

from agent import run_agent

st.title("UIB Campus Assistant · v4 agent + MCP")
st.caption("Jawaban berdasarkan dokumen resmi. Cek kembali ke BAAK untuk keputusan penting.")
if "history" not in st.session_state:
    st.session_state.history = []
if st.sidebar.button("Clear chat"):
    st.session_state.history = []
    st.rerun()

for m in st.session_state.history:
    st.chat_message(m["role"]).write(m["content"])

if q := st.chat_input("Tanya peraturan, jadwal kuliah, IPK, atau kalender…"):
    st.chat_message("user").write(q)
    with st.chat_message("assistant"):
        with st.status("Thinking…", expanded=False) as status:
            def show_step(step, name, args, result):
                st.write(f"**step {step} · {name}**({args})")
                st.caption(str(result)[:300])
            text = asyncio.run(run_agent(q, history=st.session_state.history, on_step=show_step))
            status.update(label="Steps", state="complete")
        st.write(text)
    st.session_state.history += [{"role": "user", "content": q},
                                 {"role": "assistant", "content": text}]
