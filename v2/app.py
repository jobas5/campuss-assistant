"""Campus Assistant v1 chat UI.   streamlit run app.py"""
import streamlit as st

from rag import (SMALLTALK_REPLY, answer, citation_problem, cited_sources, needs_documents,
                 rewrite_query)

st.title("UIB Campus Assistant")
st.caption("Jawaban berdasarkan dokumen resmi. Cek kembali ke BAAK untuk keputusan penting.")
if "history" not in st.session_state:
    st.session_state.history = []
if st.sidebar.button("Clear chat"):
    st.session_state.history = []
    st.rerun()

for m in st.session_state.history:
    st.chat_message(m["role"]).write(m["content"])

if q := st.chat_input("Tanya seputar akademik UIB…"):
    st.chat_message("user").write(q)
    with st.chat_message("assistant"):
        if not needs_documents(q):
            text, chunks = SMALLTALK_REPLY, []
            st.write(text)
        else:
            query = rewrite_query(st.session_state.history, q)
            with st.spinner("Mencari di dokumen…"):
                text, chunks = answer(query)
            st.write(text)
            if warning := citation_problem(text, chunks):
                st.warning(warning)
            with st.expander("Sources"):
                st.caption(f"Search query: {query}")
                for c in cited_sources(text, chunks):
                    st.caption(f"{c['source']} · page {c['page']}")
    st.session_state.history += [{"role": "user", "content": q},
                                 {"role": "assistant", "content": text}]
