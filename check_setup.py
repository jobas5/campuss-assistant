"""Run this first:  python check_setup.py
Checks Python, packages, .env and a real call to your LLM. Fix any ✕ before the lab.
"""
import importlib
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ok = True


def report(passed, label, hint=""):
    global ok
    ok &= passed
    print(("✓ " if passed else "✕ ") + label + ("" if passed or not hint else f"\n    → {hint}"))


report(sys.version_info >= (3, 10), f"Python {sys.version.split()[0]}", "Install Python 3.11 (MCP needs 3.10+).")

for module, pip_name in [("openai", "openai"), ("dotenv", "python-dotenv"), ("pypdf", "pypdf"),
                         ("faiss", "faiss-cpu"), ("sentence_transformers", "sentence-transformers"),
                         ("streamlit", "streamlit"), ("rank_bm25", "rank_bm25"), ("mcp", "mcp[cli]"),
                         ("agents", "openai-agents"), ("pydantic", "pydantic"), ("fastapi", "fastapi")]:
    try:
        importlib.import_module(module)
        report(True, f"package {pip_name}")
    except Exception:
        report(False, f"package {pip_name}", "pip install -r requirements.txt")

env = ROOT / ".env"
report(env.exists(), ".env file", "Copy .env.example to .env and fill in your key.")
if env.exists():
    from dotenv import load_dotenv
    from openai import OpenAI

    load_dotenv(env)
    for var in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL"):
        report(bool(os.getenv(var)) and "your-key" not in os.getenv(var, ""), f"{var} is set")
    try:
        client = OpenAI(base_url=os.getenv("LLM_BASE_URL"), api_key=os.getenv("LLM_API_KEY"))
        reply = client.chat.completions.create(model=os.getenv("LLM_MODEL"), max_tokens=5,
                                               messages=[{"role": "user", "content": "Say OK"}])
        report(True, f"LLM call works ({os.getenv('LLM_MODEL')}): {reply.choices[0].message.content!r}")
    except Exception as e:
        report(False, "LLM call", f"{type(e).__name__}: {str(e)[:150]}")

print("\nAll good — follow README.md, starting with v1." if ok else "\nFix the ✕ items above, then run this again.")
