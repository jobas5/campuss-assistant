"""Trigger #3 — a schedule. Summarize the last 24 hours of complaints for BAAK staff.

    python daily_summary.py
    # cron (Linux/macOS), every day at 07:00:
    # 0 7 * * * cd /path/to/campus-assistant/v5 && python daily_summary.py
"""
import db
from config import MODEL, client

complaints = db.since(hours=24, request_type="complaint")
if not complaints:
    print("No complaints in the last 24 hours.")
else:
    listing = "\n".join(f"- #{c.id} ({c.status}) {c.details}" for c in complaints)
    resp = client.chat.completions.create(
        model=MODEL, temperature=0.2,
        messages=[{"role": "system", "content": "Summarize these student complaints for BAAK staff in Indonesian: "
                                                "group similar issues, list the most urgent first, max 8 lines."},
                  {"role": "user", "content": listing}])
    print(resp.choices[0].message.content)
