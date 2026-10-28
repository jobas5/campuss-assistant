"""Specialist tools for the Student Service Desk (Module 12). They draft and read — they never send."""
from datetime import date

from agents import function_tool

from db import student_db
from rag import build_context, search

LETTER_TEMPLATE = """SURAT KETERANGAN AKTIF KULIAH (DRAF — CONTOH)

Yang bertanda tangan di bawah ini menerangkan bahwa:
Nama : {name}
NIM  : {nim}
adalah mahasiswa aktif pada semester ganjil 2026/2027.
Surat ini dibuat untuk keperluan: {purpose}.

Batam, {today}
Kepala BAAK
(ditandatangani setelah disetujui staf)"""


@function_tool
def draft_active_letter(nim: str, name: str, purpose: str) -> str:
    """Draft a 'surat keterangan aktif kuliah'. Returns draft text only."""
    return LETTER_TEMPLATE.format(nim=nim, name=name, purpose=purpose, today=date.today().isoformat())


@function_tool
def check_leave_eligibility(nim: str) -> str:
    """Check semester count and unpaid fees for an academic-leave request."""
    s = student_db.get(nim)
    if s is None:
        return f"No student record for NIM {nim}."
    return f"semester={s.semester}, unpaid_fees={s.unpaid}"


@function_tool
def search_rules(query: str) -> str:
    """Search official academic rules (RAG from Module 9)."""
    return build_context(search(query))
