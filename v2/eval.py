"""Evaluate Campus Assistant against testset.csv (Module 9).

    python eval.py --retrieval-only          # hit@K + MRR for every config, no API key needed
    python eval.py --mode vector             # full run for one config: retrieval + LLM judge + latency
    python eval.py --mode hybrid_rerank
"""
import argparse
import json
import time

import pandas as pd

from config import HERE, MODEL, client
from rag import DEFAULT_FILTER, answer, build_context, rewrite_query, search

K = 4
MODES = ["vector", "hybrid", "rerank", "hybrid_rerank"]
tests = pd.read_csv(HERE / "testset.csv")


def history_of(t):
    """'user: ... | assistant: ...' -> list of chat messages."""
    if not isinstance(t.history, str):
        return []
    turns = [part.strip().split(":", 1) for part in t.history.split(" | ")]
    return [{"role": role.strip(), "content": text.strip()} for role, text in turns]


def query_for(t, use_llm):
    history = history_of(t)
    return rewrite_query(history, t.question) if (history and use_llm) else t.question


# ---------- retrieval: no LLM needed ----------
def rank_of_expected(chunks, source, page, tolerance=0):
    for rank, c in enumerate(chunks, start=1):
        if c["source"] == source and abs(c["page"] - page) <= tolerance:
            return rank
    return None


def retrieval_eval(mode, where=DEFAULT_FILTER, use_llm=False):
    hits, rr = [], []
    for t in tests[tests.type != "out_of_scope"].itertuples():
        chunks = search(query_for(t, use_llm), k=K, mode=mode, where=where)
        r = rank_of_expected(chunks, t.expected_source, int(t.expected_page))
        hits.append(r is not None)
        rr.append(1 / r if r else 0)
    return sum(hits) / len(hits), sum(rr) / len(rr)


# ---------- generation: LLM-as-a-judge ----------
JUDGE = """You grade a RAG answer for FAITHFULNESS.
5 = every claim is supported by the context
3 = mostly supported, one unsupported detail
1 = mostly invented or contradicts the context
Return JSON: {"score": <1-5>, "reason": "<one sentence>"}"""

RELEVANCE = """You grade whether an answer addresses the question (RELEVANCE).
5 = directly and completely answers it
3 = partly answers it
1 = does not answer it
Return JSON: {"score": <1-5>, "reason": "<one sentence>"}"""


def _judge(rubric, content):
    resp = client.chat.completions.create(
        model=MODEL, temperature=0,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": rubric}, {"role": "user", "content": content}])
    out = json.loads(resp.choices[0].message.content)
    return (out["score"] - 1) / 4, out["reason"]      # 0..1


def judge_faithfulness(question, context, answer):
    return _judge(JUDGE, f"Context:\n{context}\n\nQuestion: {question}\nAnswer: {answer}")


def judge_relevance(question, answer):
    return _judge(RELEVANCE, f"Question: {question}\nAnswer: {answer}")


REFUSAL_WORDS = ["tidak tahu", "tidak ada", "tidak menemukan", "tidak tersedia", "tidak dapat", "maaf",
                 "don't know", "do not know", "not in the", "cannot find"]


def generation_eval(mode):
    rows = []
    for t in tests.itertuples():
        q = query_for(t, use_llm=True)
        start = time.time()
        text, chunks = answer(q, mode=mode)
        row = {"question": t.question, "type": t.type, "answer": text, "latency_s": round(time.time() - start, 2)}
        if t.type == "out_of_scope":
            row["refused"] = any(w in text.lower() for w in REFUSAL_WORDS)
        else:
            row["faithfulness"], row["faith_reason"] = judge_faithfulness(q, build_context(chunks), text)
            row["relevance"], _ = judge_relevance(t.question, text)
        rows.append(row)
        print(f"  {t.type:14s} {t.question[:50]}")
    df = pd.DataFrame(rows)
    df.to_csv(HERE / f"eval_results_{mode}.csv", index=False)
    return df


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=MODES, default="hybrid_rerank")
    ap.add_argument("--retrieval-only", action="store_true")
    args = ap.parse_args()
    print(tests["type"].value_counts().to_string(), "\n")

    if args.retrieval_only:
        print("Follow-ups use the raw question here (rewriting needs the LLM).\n")
        print(f"{'config':32s} hit@{K}   MRR")
        hit, mrr = retrieval_eval("vector", where=None)
        print(f"{'vector, no year filter':32s} {hit:.2f}   {mrr:.2f}")
        for mode in MODES:
            hit, mrr = retrieval_eval(mode)
            print(f"{mode:32s} {hit:.2f}   {mrr:.2f}")
    else:
        hit, mrr = retrieval_eval(args.mode, use_llm=True)
        df = generation_eval(args.mode)
        scope = df[df.type != "out_of_scope"]
        print(f"\nconfig={args.mode}  hit@{K}={hit:.2f}  MRR={mrr:.2f}  "
              f"faithfulness={scope.faithfulness.mean():.2f}  relevance={scope.relevance.mean():.2f}  "
              f"out-of-scope refusal={df[df.type == 'out_of_scope'].refused.mean():.2f}  "
              f"latency={df.latency_s.mean():.1f}s")
        print(f"Details saved to eval_results_{args.mode}.csv — read the faith_reason column for failures.")
