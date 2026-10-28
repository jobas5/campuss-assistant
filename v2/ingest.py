"""v2 ingestion: same as v1, plus metadata (year, type) for filtering.

Also indexes data/archive/ so you can see why the year filter matters.
    python ingest.py
"""
import json
import os

import faiss
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

from config import DATA_DIR, EMBED_MODEL, INDEX_DIR

META = json.load(open(DATA_DIR / "documents.json"))


def load_chunks(path, size=800, overlap=150):
    name = os.path.basename(path)
    meta = META.get(name, {})
    chunks = []
    for page_no, page in enumerate(PdfReader(path).pages, 1):
        text = page.extract_text() or ""
        for start in range(0, len(text), size - overlap):
            chunks.append({
                "text": text[start:start + size],
                "source": name,
                "page": page_no,
                "year": meta.get("year"),
                "type": meta.get("type"),
            })
    return chunks


if __name__ == "__main__":
    chunks = []
    for pdf in sorted(DATA_DIR.glob("*.pdf")) + sorted(DATA_DIR.glob("archive/*.pdf")):
        found = load_chunks(str(pdf))
        print(f"{pdf.name}: {len(found)} chunks  {META.get(pdf.name, {})}")
        chunks += found

    model = SentenceTransformer(EMBED_MODEL)
    vectors = model.encode([c["text"] for c in chunks], normalize_embeddings=True, show_progress_bar=True)
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)

    INDEX_DIR.mkdir(exist_ok=True)
    faiss.write_index(index, str(INDEX_DIR / "index.faiss"))
    json.dump(chunks, open(INDEX_DIR / "chunks.json", "w"), ensure_ascii=False, indent=1)
    print(f"Saved {len(chunks)} chunks to {INDEX_DIR}")
