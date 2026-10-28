# UIB Campus Assistant — lab code for Modules 8–12

One project that grows every week. Each folder is a **complete, runnable checkpoint**:
it is the finished lab for one module *and* the starter for the next. Missed a week? Start from the previous folder.

| Folder | Module | What it adds | Run |
|---|---|---|---|
| `v1/` | 8 · RAG chatbot | grounded answers, `[S1]` citations, follow-up rewriting, chat UI | `streamlit run app.py` |
| `v2/` | 9 · Evaluate & optimize | test set, hit@K / MRR, LLM judge, hybrid search, reranking, year filter | `python eval.py --retrieval-only` |
| `v3/` | 10 · AI agent | agent loop from scratch with 3 tools, step trace | `streamlit run app.py` |
| `v4/` | 11 · MCP | `campus-data` MCP server (SQLite schedule) used by the agent and by Claude Desktop / VS Code | `streamlit run app.py` |
| `v5/` | 12 · Workflow | photo → JSON → validation gate → triage + 3 agents → staff approval queue | see below |

> All documents in `data/` are **fictional lab material**, not official UIB regulations.

## 1 · Setup (once)

Python **3.10+** is required (3.11 recommended — the MCP SDK needs 3.10+).

```bash
cd campus-assistant
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                 # Windows: copy .env.example .env
```

Fill in `.env` with your OpenAI-compatible endpoint (CommandCode / DeepSeek / …), then check everything:

```bash
python check_setup.py
```

First runs download two local models from Hugging Face: the embedding model (~0.9 GB) and, from v2 on,
the reranker `BAAI/bge-reranker-v2-m3` (~4 GB on disk). On a slow connection or a small laptop, set
`RERANK_MODEL=cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` in `.env` (~0.9 GB) — on our test set it scores a bit
lower (hit@4 0.88 / MRR 0.82 vs 1.00 / 0.90), which is itself a good trade-off to discuss in Module 9.

## 2 · Every checkpoint starts the same way

```bash
cd v1                  # or v2, v3, v4, v5
python ingest.py       # builds index/ from ../data — run again whenever the PDFs change
```

## v1 · RAG chatbot (Module 8)

```bash
streamlit run app.py
```

`rag.py` holds everything from the slides: `retrieve`, `build_context`, `answer`, `cited_sources`,
`rewrite_query`, plus the citation check and the small-talk router. Try the five test questions from the slides.

## v2 · Evaluate & optimize (Module 9)

```bash
python eval.py --retrieval-only        # no API key needed — compares every retrieval config
python eval.py --mode vector           # full run: retrieval + LLM judge + latency (baseline)
python eval.py --mode hybrid_rerank    # full run for the improved config
```

`testset.csv` has 20 questions across six types. Measured on the sample data (retrieval only):

| config | hit@4 | MRR |
|---|---|---|
| vector, no year filter | 0.82 | 0.49 |
| vector + year filter | 0.94 | 0.67 |
| hybrid | 0.88 | 0.70 |
| rerank | 1.00 | 0.90 |
| hybrid + rerank | 1.00 | 0.90 |

The 2024 rules in `data/archive/` are indexed on purpose: without the year filter the bot can quote outdated rules.
Full runs save `eval_results_<mode>.csv` — read the `faith_reason` column to diagnose failures.

## v3 · AI agent (Module 10)

```bash
python agent.py "Nilai saya A (3 SKS), B+ (3 SKS), A- (2 SKS). Boleh ambil 24 SKS?"
streamlit run app.py
```

`tools.py` = the three tools and their JSON schemas. `agent.py` = `run_agent()`, the loop from the slides,
with `max_steps`, error handling (`run_tool`) and the step log.

## v4 · MCP (Module 11)

```bash
python setup_db.py                 # creates campus.db (sample schedule)
mcp dev campus_server.py           # MCP Inspector: call get_schedule / find_courses by hand
python mcp_client.py               # your own client: list + call tools
python agent.py "Kelas apa saja hari Senin?"
streamlit run app.py
```

**Claude Desktop** (Settings → Developer → Edit Config) or **VS Code** (`.vscode/mcp.json`, key `"servers"`):
use the **full path to your venv's Python** — the host does not know about your virtual environment.

```json
{
  "mcpServers": {
    "campus-data": {
      "command": "/full/path/to/campus-assistant/.venv/bin/python",
      "args": ["/full/path/to/campus-assistant/v4/campus_server.py"]
    }
  }
}
```

> The code uses the MCP Python SDK **v2** API (`from mcp.server.mcpserver import MCPServer`).
> Tutorials written for SDK v1 use `FastMCP` — same ideas, old name.

## v5 · Student Service Desk (Module 12)

Needs a **vision-capable** model for photos (`VISION_*` in `.env`). No vision model? Use the text form or `--text`.

```bash
python workflow.py ../data/sample_requests/ktm_active_letter.jpg     # photo → extract → route → queue
python workflow.py --text "Saya Budi, NIM 2231002, mau cuti akademik semester depan."
streamlit run submit_app.py              # trigger 1: student form
uvicorn api:app --reload                 # trigger 2: webhook (POST /requests)
python daily_summary.py                  # trigger 3: run it from cron
streamlit run approve_app.py             # staff approval queue
```

Nothing is "sent" until staff click **Approve**; approved replies are written to `v5/outbox/` (a stand-in for email),
and every decision is logged with user and time. Sample students in `db.py`: `2231001`–`2231004`
(2231003 has only 1 semester and 2231004 has unpaid fees — both should fail the leave check).

## What was tested

Every script and all six Streamlit apps were run with Python 3.11 and the package versions in `requirements.txt`
(openai 3.x, mcp 2.x, openai-agents 0.24), using the sample data and a scripted stand-in for the LLM.
Retrieval, evaluation metrics, the MCP server/client, the validation gate, the database and the UIs ran for real;
answer *quality* depends on your real LLM — run `check_setup.py`, then each checkpoint's test questions.

## For the lecturer

`tools/make_sample_data.py` regenerates the fictional PDFs and sample photos (`pip install reportlab pillow`).
Edit the text there to change rules — then update `v2/testset.csv` (expected page numbers) to match.
