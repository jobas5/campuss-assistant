"""Run once (and again whenever documents change): PDFs -> chunks -> embeddings -> FAISS index.

    python ingest.py
"""
import json
import os

import faiss
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

from config import DATA_DIR, EMBED_MODEL, INDEX_DIR


def load_chunks(path, size=800, overlap=150):
    chunks = []
    for page_no, page in enumerate(PdfReader(path).pages, 1):
        text = page.extract_text() or ""
        for start in range(0, len(text), size - overlap):
            chunks.append({
                "text": text[start:start + size],
                "source": os.path.basename(path),
                "page": page_no,
            })
    return chunks


if __name__ == "__main__":
    chunks = []
    for pdf in sorted(DATA_DIR.glob("*.pdf")):
        found = load_chunks(str(pdf))
        print(f"{pdf.name}: {len(found)} chunks")
        chunks += found
    if not chunks:
        raise SystemExit(f"No text found in {DATA_DIR}/*.pdf — scanned PDFs have no text layer.")

    model = SentenceTransformer(EMBED_MODEL)
    vectors = model.encode([c["text"] for c in chunks], normalize_embeddings=True, show_progress_bar=True)
    index = faiss.IndexFlatIP(vectors.shape[1])          # inner product on normalized vectors = cosine
    index.add(vectors)

    INDEX_DIR.mkdir(exist_ok=True)
    faiss.write_index(index, str(INDEX_DIR / "index.faiss"))
    json.dump(chunks, open(INDEX_DIR / "chunks.json", "w"), ensure_ascii=False, indent=1)
    print(f"Saved {len(chunks)} chunks to {INDEX_DIR}")
