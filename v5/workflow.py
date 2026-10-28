"""Student Service Desk workflow: triage agent + three specialists (Module 12).

    python workflow.py ../data/sample_requests/ktm_active_letter.jpg      # photo → extract → route → queue
    python workflow.py --text "Saya Budi, NIM 2231002, mau cuti akademik semester depan."
"""
import argparse
import asyncio
import os

from agents import Agent, OpenAIChatCompletionsModel, Runner, set_tracing_disabled
from openai import AsyncOpenAI

import db
from extract import extract_request, extract_text_request, validate
from tools import check_leave_eligibility, draft_active_letter, search_rules

client = AsyncOpenAI(base_url=os.getenv("LLM_BASE_URL") or None,
                     api_key=os.getenv("LLM_API_KEY") or "missing-key")
model = OpenAIChatCompletionsModel(model=os.getenv("LLM_MODEL", "deepseek-chat"),
                                   openai_client=client)
set_tracing_disabled(True)      # default tracing sends data to OpenAI

letter = Agent(name="Letter agent", model=model,
    handoff_description="Requests for official letters",
    instructions="Prepare the requested letter with draft_active_letter. Return only the draft.",
    tools=[draft_active_letter])

leave = Agent(name="Leave agent", model=model,
    handoff_description="Academic leave (cuti akademik) requests",
    instructions="Check eligibility with check_leave_eligibility and the rules with search_rules, "
                 "then draft a short decision memo for staff, citing the rules like [S1].",
    tools=[check_leave_eligibility, search_rules])

complaint = Agent(name="Complaint agent", model=model,
    handoff_description="Complaints and problems",
    instructions="Summarize the complaint, rate urgency 1-3, draft a polite reply in Indonesian.")

triage = Agent(name="Triage", model=model,
    instructions="Read the student request and hand off to the right specialist. Do not answer yourself.",
    handoffs=[letter, leave, complaint])


async def handle(req):
    """Route one validated request. Returns (draft, name of the agent that wrote it)."""
    result = await Runner.run(triage, req.model_dump_json())
    return result.final_output, result.last_agent.name


def process(data):
    """Full pipeline for extracted data: gate → agents → PENDING queue. Never sends anything."""
    req, problem = validate(data)
    if problem:
        return {"status": "NEEDS_FIX", "message": problem}
    draft, agent = asyncio.run(handle(req))
    request_id = db.add_pending(req, draft, agent)
    return {"status": "PENDING", "id": request_id, "agent": agent, "draft": draft}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("image", nargs="?", default="../data/sample_requests/ktm_active_letter.jpg")
    ap.add_argument("--text")
    args = ap.parse_args()
    data = extract_text_request(args.text) if args.text else extract_request(args.image)
    print("extracted:", data)
    out = process(data)
    print(out["status"], "·", out.get("agent", ""), "\n")
    print(out.get("draft") or out.get("message"))
