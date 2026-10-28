"""Campus Assistant v1 — retrieve, ground, cite, remember (Module 8)."""
import json
import re
from functools import lru_cache

import faiss
from sentence_transformers import SentenceTransformer

from config import EMBED_MODEL, INDEX_DIR, MODEL, client


# ---------- retrieval (from Module 7) ----------
@lru_cache(maxsize=1)
def _load():
    if not (INDEX_DIR / "index.faiss").exists():
        raise FileNotFoundError("No index found. Run `python ingest.py` first.")
    index = faiss.read_index(str(INDEX_DIR / "index.faiss"))
    chunks = json.load(open(INDEX_DIR / "chunks.json"))
    return SentenceTransformer(EMBED_MODEL), index, chunks


def retrieve(question, k=4):
    model, index, chunks = _load()
    vector = model.encode([question], normalize_embeddings=True)
    scores, ids = index.search(vector, k)
    return [dict(chunks[i], score=float(s)) for s, i in zip(scores[0], ids[0]) if i != -1]


# ---------- grounding + citations ----------
def build_context(chunks):
    """chunks = list of dicts from retrieve()"""
    blocks = []
    for i, c in enumerate(chunks, start=1):
        tag = f"[S{i}]"
        src = f"{c['source']} p.{c['page']}"
        blocks.append(f"{tag} {src}\n{c['text']}")
    return "\n\n".join(blocks)


SYSTEM = """You are UIB Campus Assistant.
Answer ONLY from the context. Cite sources like [S1].
If the answer is not in the context, say you don't know and suggest asking BAAK.
Answer in the same language as the question."""


def answer(question, k=4):
    chunks = retrieve(question, k=k)          # from Module 7
    context = build_context(chunks)
    resp = client.chat.completions.create(
        model=MODEL, temperature=0.1,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user",
             "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ])
    return resp.choices[0].message.content, chunks


def cited_sources(answer, chunks):
    found = re.findall(r"\[S(\d+)\]", answer)
    ids = sorted({int(i) for i in found})
    return [chunks[i - 1] for i in ids
            if i <= len(chunks)]


def citation_problem(answer, chunks):
    """Cheap citation check (slide 19). Returns a warning string or None."""
    found = {int(i) for i in re.findall(r"\[S(\d+)\]", answer)}
    if not found:
        return "Answer may not come from official documents (no citation)."
    if any(i < 1 or i > len(chunks) for i in found):
        return "The answer cites a source that was not retrieved."
    return None


# ---------- memory: query rewriting ----------
REWRITE = """Rewrite the last user message as ONE standalone
search question, using the chat history for context.
Return only the question."""


def rewrite_query(history, question):
    if not history:
        return question
    recent = history[-6:]                       # last 3 turns
    convo = "\n".join(f"{m['role']}: {m['content']}" for m in recent)
    resp = client.chat.completions.create(
        model=MODEL, temperature=0,
        messages=[{"role": "system", "content": REWRITE},
                  {"role": "user", "content": f"{convo}\nuser: {question}"}])
    return resp.choices[0].message.content.strip()


# ---------- routing: not every message needs retrieval ----------
SMALLTALK = {"halo", "hai", "hi", "hello", "terima kasih", "makasih", "thanks", "thank you", "siapa kamu",
             "selamat pagi", "selamat siang", "selamat sore", "selamat malam"}


def needs_documents(message):
    text = re.sub(r"[^\w\s]", "", message.lower()).strip()
    return text not in SMALLTALK


SMALLTALK_REPLY = ("Halo! Saya UIB Campus Assistant. Tanyakan apa saja tentang peraturan akademik dan layanan "
                   "kampus — saya akan menjawab dari dokumen resmi.")
