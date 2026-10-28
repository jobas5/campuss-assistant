"""Photo or text in, validated StudentRequest out (Module 12).

    python extract.py ../data/sample_requests/ktm_active_letter.jpg
"""
import base64
import json
import sys
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, ValidationError

from config import MODEL, VISION_MODEL, client, vision

EXTRACT = """Read this student document. Return JSON with keys:
nim, name, program, request_type (active_letter | academic_leave |
complaint | other), details. Use null for anything you cannot read."""


class StudentRequest(BaseModel):
    nim: str = Field(pattern=r"^\d{7,10}$")
    name: str
    program: str | None = None
    request_type: Literal["active_letter", "academic_leave",
                          "complaint", "other"]
    details: str


def extract_request(image_path):
    b64 = base64.b64encode(open(image_path, "rb").read()).decode()
    mime = "image/png" if str(image_path).lower().endswith(".png") else "image/jpeg"
    resp = vision.chat.completions.create(
        model=VISION_MODEL, temperature=0,
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": [
            {"type": "text", "text": EXTRACT},
            {"type": "image_url",
             "image_url": {"url": f"data:{mime};base64,{b64}"}}]}])
    return json.loads(resp.choices[0].message.content)


def extract_text_request(text):
    """Same extraction for a typed request — use this if you have no vision model."""
    resp = client.chat.completions.create(
        model=MODEL, temperature=0,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": EXTRACT.replace("document", "request")},
                  {"role": "user", "content": text}])
    return json.loads(resp.choices[0].message.content)


def ask_student_to_fix(errors):
    """Turn Pydantic errors into a message for the student."""
    fields = ", ".join(str(e["loc"][0]) for e in errors if e.get("loc"))
    return f"Data permohonan belum lengkap atau tidak terbaca ({fields}). Mohon unggah ulang atau lengkapi."


def validate(data):
    """Returns (StudentRequest, None) or (None, message for the student). This is the workflow gate."""
    try:
        return StudentRequest(**data), None
    except ValidationError as e:
        return None, ask_student_to_fix(e.errors())


if __name__ == "__main__":
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "../data/sample_requests/ktm_active_letter.jpg")
    data = extract_request(path)
    print(json.dumps(data, indent=2, ensure_ascii=False))
    req, problem = validate(data)
    print("valid:", req is not None, "|", problem or req.request_type)
