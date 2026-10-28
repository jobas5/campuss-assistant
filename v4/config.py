"""Shared settings. Values come from ../.env (copy .env.example first)."""
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
load_dotenv(ROOT / ".env")

DATA_DIR = ROOT / "data"
INDEX_DIR = HERE / "index"

MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
RERANK_MODEL = os.getenv("RERANK_MODEL", "BAAI/bge-reranker-v2-m3")

# A missing key only fails when a request is made (401), so ingest.py works without one.
client = OpenAI(base_url=os.getenv("LLM_BASE_URL") or None,
                api_key=os.getenv("LLM_API_KEY") or "missing-key")
