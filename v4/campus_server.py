"""campus-data MCP server: the class schedule as tools (Module 11).

    mcp dev campus_server.py        # try it in the MCP Inspector
    python campus_server.py         # run over stdio (hosts start it for you)
"""
import sqlite3
from pathlib import Path

from mcp.server.mcpserver import MCPServer

DB = Path(__file__).resolve().parent / "campus.db"
mcp = MCPServer("campus-data")


def query(sql, params=()):
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)       # read-only
    con.row_factory = sqlite3.Row
    return [dict(r) for r in con.execute(sql, params)]


@mcp.tool()
def get_schedule(course_code: str) -> list[dict]:
    """Weekly schedule (day, time, room, lecturer) for a course code like 'AI301'."""
    return query("SELECT * FROM schedule WHERE course_code = ?", (course_code.upper(),))


@mcp.tool()
def find_courses(day: str) -> list[dict]:
    """All courses held on a given day, e.g. 'Senin'."""
    return query("SELECT course_code, name, start, room FROM schedule WHERE day = ?",
                 (day.capitalize(),))


@mcp.resource("campus://courses")
def all_courses() -> str:
    """Every course code and name."""
    rows = query("SELECT DISTINCT course_code, name FROM schedule ORDER BY course_code")
    return "\n".join(f"{r['course_code']} {r['name']}" for r in rows)


if __name__ == "__main__":
    mcp.run()                                                    # stdio
