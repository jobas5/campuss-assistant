"""Your Python app as an MCP client — list and call the campus-data tools (Module 11).

    python mcp_client.py
"""
import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER = Path(__file__).resolve().parent / "campus_server.py"
params = StdioServerParameters(command=sys.executable, args=[str(SERVER)])


async def main():
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = (await session.list_tools()).tools
            print([t.name for t in tools])
            r = await session.call_tool("get_schedule", {"course_code": "AI301"})
            print("\n".join(c.text for c in r.content))


if __name__ == "__main__":
    asyncio.run(main())
