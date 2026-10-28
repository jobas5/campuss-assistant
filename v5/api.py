"""Trigger #2 — a webhook other systems can POST to.

    uvicorn api:app --reload
    curl -X POST localhost:8000/requests -H "Content-Type: application/json" \
      -d '{"nim": "2231002", "name": "Budi Santoso", "request_type": "academic_leave", "details": "cuti semester depan"}'
"""
from agents import Runner
from fastapi import FastAPI

import db
from extract import StudentRequest
from workflow import triage

app = FastAPI()


@app.post("/requests")
async def new_request(req: StudentRequest):
    result = await Runner.run(triage, req.model_dump_json())
    request_id = db.add_pending(req, result.final_output, result.last_agent.name)
    return {"status": "pending_approval", "id": request_id}
