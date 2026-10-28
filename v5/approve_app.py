"""Staff approval queue — nothing is sent without a human decision.   streamlit run approve_app.py"""
import streamlit as st

import db
from config import OUTBOX


def send_reply(r, text):
    """The real action. In the lab it writes to outbox/ instead of emailing the student."""
    OUTBOX.mkdir(exist_ok=True)
    (OUTBOX / f"request_{r.id}_{r.nim}.txt").write_text(text, encoding="utf-8")


st.title("BAAK · Approval queue")
for r in db.pending():
    with st.container(border=True):
        st.markdown(f"**{r.request_type}** · {r.name} ({r.nim}) · by {r.agent}")
        st.caption(r.details)
        draft = st.text_area("Draft", r.draft, key=f"d{r.id}", height=220)
        approve, reject = st.columns(2)
        if approve.button("Approve", key=f"a{r.id}"):
            send_reply(r, draft)                      # the real action
            db.mark(r.id, "APPROVED", draft, user="staff01")
            st.rerun()
        if reject.button("Reject", key=f"r{r.id}"):
            db.mark(r.id, "REJECTED", user="staff01")
            st.rerun()
if not db.pending():
    st.info("No pending requests. Submit one with submit_app.py, api.py or workflow.py.")

with st.expander("Audit trail"):
    for r in db.decided():
        st.caption(f"#{r.id} {r.status} by {r.decided_by} at {r.decided_at} · {r.request_type} · {r.nim}")
