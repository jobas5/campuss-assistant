"""Tools for Campus Assistant v3 (Module 10). Plain Python functions + their JSON schemas."""
import json

from config import DATA_DIR
from rag import build_context, hybrid_retrieve, rerank

# Example grade scale — matches the sample handbook (page 7).
POINTS = {"A": 4.0, "A-": 3.7, "B+": 3.3, "B": 3.0, "B-": 2.7, "C+": 2.3, "C": 2.0, "D": 1.0, "E": 0.0}


def calc_gpa(courses):
    total_sks = sum(c["sks"] for c in courses)
    points = sum(POINTS[c["grade"]] * c["sks"] for c in courses)
    return round(points / total_sks, 2)


def get_academic_calendar(event):
    calendar = json.load(open(DATA_DIR / "calendar.json"))     # {"UTS": "2026-10-19 s/d ...", ...}
    events = [k for k in calendar if not k.startswith("_")]
    return calendar.get(event.upper(), f"Event not found in calendar. Known events: {', '.join(events)}")


def search_documents(query):
    chunks = rerank(query, hybrid_retrieve(query, k=20))   # from Module 9
    return build_context(chunks)                          # from Module 8


FUNCS = {"calc_gpa": calc_gpa, "get_academic_calendar": get_academic_calendar,
         "search_documents": search_documents}

TOOLS = [
    {"type": "function",
     "function": {
         "name": "search_documents",
         "description": "Search official UIB academic documents (student handbook, academic rules). "
                        "Use for any campus policy question. Returns passages tagged [S1], [S2]…",
         "parameters": {"type": "object",
                        "properties": {"query": {"type": "string", "description": "A standalone search question"}},
                        "required": ["query"]}}},
    {"type": "function",
     "function": {
         "name": "calc_gpa",
         "description": "Calculate IPK (GPA) from course grades and SKS. "
                        "Use when the user gives their grades. Never compute IPK yourself.",
         "parameters": {
             "type": "object",
             "properties": {
                 "courses": {"type": "array", "items": {
                     "type": "object",
                     "properties": {"grade": {"type": "string", "enum": list(POINTS)},
                                    "sks": {"type": "integer"}},
                     "required": ["grade", "sks"]}}},
             "required": ["courses"]}}},
    {"type": "function",
     "function": {
         "name": "get_academic_calendar",
         "description": "Look up dates in the academic calendar: UTS, UAS, KRS, PERKULIAHAN, WISUDA, BATAS CUTI.",
         "parameters": {"type": "object",
                        "properties": {"event": {"type": "string", "description": "e.g. UAS"}},
                        "required": ["event"]}}},
]
