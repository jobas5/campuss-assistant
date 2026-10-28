"""Small SQLite helper: the approval queue + sample student records (Module 12)."""
import sqlite3
from datetime import datetime, timedelta
from types import SimpleNamespace

from config import HERE

DB = HERE / "service_desk.db"

SAMPLE_STUDENTS = [            # fictional records for the lab
    ("2231001", "Siti Rahma", 5, 0),
    ("2231002", "Budi Santoso", 3, 0),
    ("2231003", "Andi Wijaya", 1, 0),
    ("2231004", "Dewi Lestari", 4, 2_500_000),
]


def _con():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def init():
    with _con() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT, nim TEXT, name TEXT, program TEXT,
            request_type TEXT, details TEXT, agent TEXT, draft TEXT, status TEXT,
            final_text TEXT, decided_by TEXT, decided_at TEXT)""")
        con.execute("CREATE TABLE IF NOT EXISTS students (nim TEXT PRIMARY KEY, name TEXT, semester INT, unpaid INT)")
        con.executemany("INSERT OR IGNORE INTO students VALUES (?, ?, ?, ?)", SAMPLE_STUDENTS)


def add_pending(req, draft, agent):
    with _con() as con:
        cur = con.execute(
            "INSERT INTO requests (created_at, nim, name, program, request_type, details, agent, draft, status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'PENDING')",
            (datetime.now().isoformat(timespec="seconds"), req.nim, req.name, req.program, req.request_type,
             req.details, agent, draft))
        return cur.lastrowid


def _rows(sql, params=()):
    with _con() as con:
        return [SimpleNamespace(**dict(r)) for r in con.execute(sql, params)]


def pending():
    return _rows("SELECT * FROM requests WHERE status = 'PENDING' ORDER BY id")


def decided(limit=20):
    return _rows("SELECT * FROM requests WHERE status != 'PENDING' ORDER BY decided_at DESC LIMIT ?", (limit,))


def since(hours=24, request_type=None):
    after = (datetime.now() - timedelta(hours=hours)).isoformat(timespec="seconds")
    sql = "SELECT * FROM requests WHERE created_at >= ?" + (" AND request_type = ?" if request_type else "")
    return _rows(sql, (after, request_type) if request_type else (after,))


def mark(request_id, status, final_text=None, user=None):
    """Record a human decision: who, when, what was finally sent."""
    with _con() as con:
        con.execute("UPDATE requests SET status = ?, final_text = ?, decided_by = ?, decided_at = ? WHERE id = ?",
                    (status, final_text, user, datetime.now().isoformat(timespec="seconds"), request_id))


class StudentDB:
    def get(self, nim):
        rows = _rows("SELECT * FROM students WHERE nim = ?", (nim,))
        return rows[0] if rows else None


student_db = StudentDB()
init()
