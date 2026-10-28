"""Campus Assistant v2 — v1 plus hybrid search, reranking and metadata filters (Module 9)."""
import json
import re
from functools import lru_cache

import faiss
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder, SentenceTransformer

from config import EMBED_MODEL, INDEX_DIR, MODEL, RERANK_MODEL, client

DEFAULT_FILTER = {"year": 2026}      # Fix 3: never quote outdated rules
DEFAULT_MODE = "hybrid_rerank"       # best config from the experiment log


def tokenize(text):
    return re.findall(r"\w+", text.lower())


@lru_cache(maxsize=1)
def _load():
    if not (INDEX_DIR / "index.faiss").exists():
        raise FileNotFoundError("No index found. Run `python ingest.py` first.")
    index = faiss.read_index(str(INDEX_DIR / "index.faiss"))
    chunks = json.load(open(INDEX_DIR / "chunks.json"))
    bm25 = BM25Okapi([tokenize(c["text"]) for c in chunks])
    return SentenceTransformer(EMBED_MODEL), index, chunks, bm25


@lru_cache(maxsize=1)
def _reranker():
    return CrossEncoder(RERANK_MODEL)


def matches(chunk, where):
    return not where or all(chunk.get(k) == v for k, v in where.items())


# ---------- retrieval ----------
def faiss_search(query, n, where=DEFAULT_FILTER):
    """Ids of the top-n chunks by vector similarity, after the metadata filter."""
    model, index, chunks, _ = _load()
    vector = model.encode([query], normalize_embeddings=True)
    _, ids = index.search(vector, index.ntotal if where else n)
    return [int(i) for i in ids[0] if i != -1 and matches(chunks[i], where)][:n]


def bm25_search(query, n, where=DEFAULT_FILTER):
    _, _, chunks, bm25 = _load()
    ranked = bm25.get_scores(tokenize(query)).argsort()[::-1]
    return [int(i) for i in ranked if matches(chunks[i], where)][:n]


def retrieve(question, k=4, where=DEFAULT_FILTER):
    """Plain vector search (the v1 baseline)."""
    _, _, chunks, _ = _load()
    return [chunks[i] for i in faiss_search(question, k, where)]


def hybrid_retrieve(query, k=4, n=20, where=DEFAULT_FILTER):
    _, _, chunks, _ = _load()
    kw = bm25_search(query, n, where)
    vec = faiss_search(query, n, where)
    score = {}
    for ranking in (kw, vec):
        for rank, cid in enumerate(ranking, start=1):
            score[cid] = score.get(cid, 0) + 1 / (60 + rank)
    best = sorted(score, key=score.get, reverse=True)[:k]
    return [chunks[i] for i in best]


def rerank(query, candidates, k=4):
    scores = _reranker().predict([(query, c["text"]) for c in candidates])
    ranked = sorted(zip(scores, candidates), key=lambda x: x[0], reverse=True)
    return [c for _, c in ranked[:k]]


def search(query, k=4, mode=DEFAULT_MODE, where=DEFAULT_FILTER):
    """One entry point for every experiment in the log (eval.py --mode ...)."""
    if mode == "vector":
        return retrieve(query, k, where)
    if mode == "hybrid":
        return hybrid_retrieve(query, k, where=where)
    if mode == "rerank":
        return rerank(query, retrieve(query, 20, where), k)
    if mode == "hybrid_rerank":
        return rerank(query, hybrid_retrieve(query, k=20, where=where), k)
    raise ValueError(f"unknown mode {mode}")


# ---------- grounding + citations (unchanged from v1) ----------
def build_context(chunks):
    blocks = []
    for i, c in enumerate(chunks, start=1):
        blocks.append(f"[S{i}] {c['source']} p.{c['page']}\n{c['text']}")
    return "\n\n".join(blocks)


SYSTEM = """You are UIB Campus Assistant.
Answer ONLY from the context. Cite sources like [S1].
If the answer is not in the context, say you don't know and suggest asking BAAK.
Answer in the same language as the question."""


def answer(question, k=4, mode=DEFAULT_MODE, where=DEFAULT_FILTER):
    chunks = search(question, k=k, mode=mode, where=where)
    context = build_context(chunks)
    resp = client.chat.completions.create(
        model=MODEL, temperature=0.1,
        messages=[{"role": "system", "content": SYSTEM},
                  {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}])
    return resp.choices[0].message.content, chunks


def cited_sources(answer, chunks):
    ids = sorted({int(i) for i in re.findall(r"\[S(\d+)\]", answer)})
    return [chunks[i - 1] for i in ids if i <= len(chunks)]


def citation_problem(answer, chunks):
    found = {int(i) for i in re.findall(r"\[S(\d+)\]", answer)}
    if not found:
        return "Answer may not come from official documents (no citation)."
    if any(i < 1 or i > len(chunks) for i in found):
        return "The answer cites a source that was not retrieved."
    return None


REWRITE = """Rewrite the last user message as ONE standalone
search question, using the chat history for context.
Return only the question."""


def rewrite_query(history, question):
    if not history:
        return question
    convo = "\n".join(f"{m['role']}: {m['content']}" for m in history[-6:])
    resp = client.chat.completions.create(
        model=MODEL, temperature=0,
        messages=[{"role": "system", "content": REWRITE},
                  {"role": "user", "content": f"{convo}\nuser: {question}"}])
    return resp.choices[0].message.content.strip()


SMALLTALK = {"halo", "hai", "hi", "hello", "terima kasih", "makasih", "thanks", "thank you", "siapa kamu",
             "selamat pagi", "selamat siang", "selamat sore", "selamat malam"}
SMALLTALK_REPLY = ("Halo! Saya UIB Campus Assistant. Tanyakan apa saja tentang peraturan akademik dan layanan "
                   "kampus — saya akan menjawab dari dokumen resmi.")


def needs_documents(message):
    return re.sub(r"[^\w\s]", "", message.lower()).strip() not in SMALLTALK
