"""Create the sample class-schedule database (Module 11). Safe to run again.

    python setup_db.py
"""
import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent / "campus.db"

con = sqlite3.connect(DB)
con.execute("""CREATE TABLE IF NOT EXISTS schedule (
    course_code TEXT, name TEXT, day TEXT, start TEXT, end TEXT, room TEXT, lecturer TEXT)""")
con.execute("DELETE FROM schedule")
con.executemany("INSERT INTO schedule VALUES (?, ?, ?, ?, ?, ?, ?)", [
    ("AI301", "Applied Artificial Intelligence", "Senin", "08:00", "10:30", "B-301", "Dosen A"),
    ("DS210", "Data Mining",                     "Senin", "13:00", "15:30", "B-204", "Dosen B"),
    ("SE220", "Software Engineering",            "Rabu",  "10:00", "12:30", "C-101", "Dosen C"),
])
con.commit()
print("campus.db ready:", con.execute("SELECT COUNT(*) FROM schedule").fetchone()[0], "rows")
