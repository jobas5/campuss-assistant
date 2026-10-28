"""Campus Assistant v3 — an agent loop from scratch, no framework (Module 10).

    python agent.py "Nilai saya A (3 SKS), B+ (3 SKS), A- (2 SKS). Boleh ambil 24 SKS?"
"""
import json
import sys

from config import MODEL, client
from tools import FUNCS, TOOLS

SYSTEM = """You are UIB Campus Assistant, helping students with academic questions.
Use search_documents for any campus policy. Use calc_gpa for any IPK math — never compute it yourself.
Use get_academic_calendar for dates.
Cite document facts like [S1]. If the tools don't give the answer, say you don't know.
Search at most twice per question. When you have enough information, answer briefly in the user's language."""


def log(step, name, args, result):
    print(f"[step {step}] {name}({args})")
    print(f"   → {str(result)[:120]}")


def run_tool(name, args):
    if name not in FUNCS:
        return f"Error: unknown tool {name}"
    try:
        return FUNCS[name](**args)
    except Exception as e:
        return f"Error: {e}. Check the arguments and try again."


def run_agent(question, max_steps=6, history=None, on_step=log):
    messages = [{"role": "system", "content": SYSTEM},
                *(history or [])[-6:],
                {"role": "user", "content": question}]
    for step in range(max_steps):
        resp = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS)
        msg = resp.choices[0].message
        if not msg.tool_calls:                    # no tool → final answer
            return msg.content
        messages.append(msg)                      # keep the tool request
        for call in msg.tool_calls:
            try:
                args = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                args, result = {}, "Error: arguments were not valid JSON."
            else:
                result = run_tool(call.function.name, args)
            on_step(step, call.function.name, args, result)
            messages.append({"role": "tool", "tool_call_id": call.id,
                             "content": str(result)})
    return "Maaf, saya belum bisa menyelesaikan permintaan ini."


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "Nilai saya A (3 SKS), B+ (3 SKS), A- (2 SKS). Boleh ambil 24 SKS?"
    print("[final]", run_agent(question))
