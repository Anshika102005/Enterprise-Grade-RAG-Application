# Advanced RAG — Agentic Retrieval with Self-RAG Correction

**A production-shaped RAG service, not a demo notebook.** FastAPI + LangGraph orchestrates a five-node agent that plans, retrieves with hybrid search, grades its own context, rewrites the query when the evidence is weak, and answers with cited sources — behind NeMo Guardrails, through an LLM gateway, with two independent evaluation suites gating CI.

<p>
  <img alt="Python" src="https://img.shields.io/badge/Python-3.12+-3776AB?style=flat&logo=python&logoColor=white">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-async%20API-009688?style=flat&logo=fastapi&logoColor=white">
  <img alt="LangGraph" src="https://img.shields.io/badge/LangGraph-5--node%20agent-1C3C3C?style=flat">
  <img alt="Qdrant" src="https://img.shields.io/badge/Qdrant-hybrid%20index-DC244C?style=flat">
  <img alt="React" src="https://img.shields.io/badge/React-19-61DAFB?style=flat&logo=react&logoColor=black">
  <img alt="Tests" src="https://img.shields.io/badge/pytest-16%20passing-0A9EDC?style=flat">
</p>

| | |
|---|---|
| **Answer pipeline** | planner → retriever → grader → rewriter → responder (LangGraph, checkpointed per `thread_id`) |
| **Retrieval** | Hybrid dense (`all-mpnet-base-v2`, 768-d) + BM25 sparse → Reciprocal Rank Fusion → FlashRank cross-encoder rerank |
| **Corrective loop** | Self-RAG grading with a bounded rewrite budget (`MAX_RETRIEVAL_RETRIES = 2`) |
| **Index** | Qdrant collection `rag-v1`: **1174 points** across **674 source documents**, 13 technical domains |
| **Quality gates** | RAGAS + DeepEval suites with thresholds, 16 offline unit tests, GitHub Actions |
| **Observability** | Logfire spans + LangSmith traces; Self-RAG telemetry returned on every response |

---

## The system at a glance

![System architecture](docs/diagrams/architecture.svg)

A request enters FastAPI, passes the guardrail gate, and is executed by the LangGraph agent inside the same process. Retrieval and reranking run against local models plus the Qdrant Cloud index; synthesis goes out through the Portkey gateway to Groq. An explorable version of this diagram (pan, zoom, dark/light) is in [`.archify/architecture-rag-system-20261028-021934/advanced-rag.architecture.html`](.archify/architecture-rag-system-20261028-021934/advanced-rag.architecture.html).

---

## Why this is more than a vector-search wrapper

- **Hybrid retrieval, not vector-only.** Every Qdrant point carries a 768-dimensional dense vector *and* a BM25 sparse vector, so paraphrase and exact identifiers (acronyms, error strings, API names) both score. The two rankings are fused with **Reciprocal Rank Fusion** — no hand-tuned weights.
- **A cross-encoder decides what the LLM sees.** The fused list is reranked by a local FlashRank ONNX cross-encoder, then a **relevance grader** accepts or rejects each passage before synthesis. The model never sees context a grader rejected.
- **The agent corrects itself.** On an irrelevant verdict, a rewriter reformulates the query and retrieval re-runs — bounded at two attempts so the loop always terminates and the last context is still usable.
- **Guardrails sit before the expensive work.** NeMo Guardrails handles greetings, off-topic questions and jailbreak attempts before retrieval, planning, or spend.
- **Provider failures are absorbed.** Synthesis runs through Portkey with fallback targets, response caching and retries on 429/503, so a single provider blip doesn't surface as an error.
- **Failures are reported honestly.** An unreachable vector store raises `RetrievalUnavailableError` instead of quietly returning zero results: grading and rewriting are skipped, the answer discloses that retrieval failed, and the UI shows *"Retrieval unavailable"* rather than blaming the query with *"0% confidence"*.
- **Quality is measured, not assumed.** RAGAS and DeepEval score faithfulness, relevancy, context precision/recall, hallucination and scope adherence; breaching a threshold in `evals/thresholds.py` fails the build.

---

## Request lifecycle

![Request lifecycle](docs/diagrams/request-lifecycle.svg)

One `POST /query`, end to end: guardrail gate → planner → hybrid search → RRF fusion → cross-encoder rerank → relevance grading → (optional bounded rewrite) → synthesised answer with sources, plan steps and telemetry.

Explorable HTML: [`.archify/sequence-request-lifecycle-20261028-022800/request-lifecycle.sequence.html`](.archify/sequence-request-lifecycle-20261028-022800/request-lifecycle.sequence.html)

---

## The Self-RAG corrective loop

![Self-RAG corrective loop](docs/diagrams/self-rag-loop.svg)

- The **planner** decides between a conversational answer (memory only) and a documentation search at `temperature = 0`.
- The **grader** reads each retrieved passage against the question and returns the useful indices plus a confidence score.
- An **irrelevant** verdict routes to the **rewriter**, which produces a new query; `retry_count` bounds the loop at two attempts.
- A **vector-store outage** takes the short path: no grading, no rewrites, disclosed in the answer — because reformulating a query cannot fix a dead connection.

Explorable HTML: [`.archify/workflow-self-rag-loop-20261028-022233/self-rag-loop.workflow.html`](.archify/workflow-self-rag-loop-20261028-022233/self-rag-loop.workflow.html)

---

## Ingestion pipeline

![Ingestion pipeline](docs/diagrams/ingestion-pipeline.svg)

Documents are parsed locally (pypdf, BeautifulSoup, python-pptx/docx), split into ~1500-character paragraph chunks, encoded both densely (`all-mpnet-base-v2`) and sparsely (`Qdrant/bm25` via fastembed), and written to Qdrant in one upsert per file. Chunk metadata is also archived to `processed_data/<domain>/` as JSON, so the corpus is inspectable without touching the vector database.

```bash
# wipe + rebuild the hybrid collection from a corpus folder
python -m app.Ingestion.processor data/true_data --wipe
```

Explorable HTML: [`.archify/dataflow-ingestion-pipeline-20261028-023107/ingestion-pipeline.dataflow.html`](.archify/dataflow-ingestion-pipeline-20261028-023107/ingestion-pipeline.dataflow.html)

---

## Retrieval parameters

All tunable without code changes (`app/config.py`, environment overrides):

| Setting | Default | Role |
|---|---|---|
| `RETRIEVAL_DENSE_TOP_K` | 20 | dense candidates |
| `RETRIEVAL_SPARSE_TOP_K` | 20 | BM25 candidates |
| `RETRIEVAL_FUSED_TOP_K` | 15 | candidates kept after RRF |
| `RRF_K` | 60 | Reciprocal Rank Fusion constant |
| `RERANK_TOP_N` | 5 | chunks passed to the grader/responder |
| `MAX_RETRIEVAL_RETRIES` | 2 | bounded rewrite attempts |

Dense encoder `sentence-transformers/all-mpnet-base-v2` (768-d, cosine) · sparse encoder `Qdrant/bm25` · reranker FlashRank `ms-marco-MiniLM-L-6-v2` (local ONNX) · reasoning model `openai/gpt-oss-20b` on Groq.

---

## Stack

| Layer | Choice | Why it's there |
|---|---|---|
| API | FastAPI + uvicorn | async `/query`, `/docs`, `/graph`, CORS for the SPA |
| Orchestration | LangGraph + MemorySaver | cyclic agent graph with per-thread memory and a bounded corrective loop |
| Vector store | Qdrant Cloud (named dense + sparse vectors) | hybrid search and payload filtering in one collection |
| Retrieval models | sentence-transformers, fastembed, FlashRank | local encode + local rerank, so only synthesis costs an API call |
| LLM | Groq (`openai/gpt-oss-20b`) | fast grader/rewriter/planner calls |
| Gateway | Portkey | fallback targets, caching, retries, unified observability |
| Guardrails | NVIDIA NeMo Guardrails | off-topic, jailbreak and dialog rails before retrieval |
| Observability | Pydantic Logfire + LangSmith | span-level traces from API to vector search |
| Evaluation | RAGAS + DeepEval + pytest | two independent judges and offline unit tests in CI |
| Frontend | React 19 · Vite 8 · TypeScript · Tailwind v4 | chat UI with reasoning timeline, sources and telemetry |

---

## Repository layout

```
app/
├── main.py                     FastAPI app: guardrails gate → LangGraph → response payload
├── config.py                   settings, retrieval tunables, gateway/eval keys
├── agents/
│   ├── graph.py                5-node StateGraph, checkpointed per thread_id
│   ├── state.py                AgentState (documents, plan, grade, confidence, retrieval_error)
│   └── nodes/                  planner · retriever · grader · rewriter · responder
├── services/Retrieval/
│   ├── qdrant_service.py       hybrid search, RRF fusion, legacy fallback, outage signalling
│   ├── embeddings.py           all-mpnet-base-v2 (768-d)
│   ├── ranking_service.py      FlashRank cross-encoder reranking
│   └── fusion.py · schema.py   RRF + named-vector contract
├── Ingestion/                  loaders (pdf/html/text/office) · chunker · processor CLI
└── guardrails/                 Colang intents/flows + LLMRails wiring
evals/                          RAGAS + DeepEval runners, golden dataset, thresholds
frontend/                       React UI (see frontend/README.md)
tests/                          offline unit tests (RRF fusion, grader parsing)
docs/diagrams/                  diagram assets used by this README
.archify/                       diagram sources (JSON) and explorable HTML exports
```

---

## Quickstart

```bash
# 1. Install
python -m venv .venv && source .venv/Scripts/activate    # Windows: .venv\Scripts\activate
pip install -r requirement.txt

# 2. Configure — create .env and fill in the keys from the table below

# 3. Ingest a corpus (first run creates the hybrid collection)
python -m app.Ingestion.processor data/true_data --wipe

# 4. Run the API
uvicorn app.main:app --reload --port 8000                 # docs at /docs

# 5. Run the UI
cd frontend && npm install && npm run dev                 # http://localhost:5173
```

The dev server proxies `/api/*` to `http://localhost:8000`, so there is no CORS friction locally.

### Configuration

| Variable | Required | Purpose |
|---|---|---|
| `QDRANT_CLUSTER_ENDPOINT` | ✅ | Qdrant Cloud cluster URL |
| `QDRANT_API_KEY` | ✅ | Qdrant API key |
| `GROQ_API_KEY` | ✅ | planner / grader / rewriter model calls |
| `PORTKEY_API_KEY` | ✅ | synthesis gateway (fallback, cache, retries) |
| `GROQ_FALLBACK_API_KEY` | – | secondary provider key for the gateway |
| `JUDGE_GROQ` | – | dedicated eval budget; falls back to `GROQ_API_KEY` |
| `LOGFIRE_TOKEN` | – | span export to Logfire |
| `LANGSMITH_API_KEY` | – | LangGraph tracing |
| `HUGGINGFACE_EMBEDDING_MODEL` | – | override the dense encoder |
| `CORS_ORIGINS` | – | comma-separated allowed origins for the SPA |

---

## API

`POST /query`

```json
{ "q": "What is a database? Types and use cases for relational and NoSQL systems.",
  "thread_id": "user-42" }
```

```json
{
  "answer": "…",
  "thought_process": ["Intent: Technical", "Search Term: …", "Context Retrieved (attempt 1)",
                      "Grade: relevant (2 passages, conf 0.80)"],
  "status": "Response generated.",
  "sources": ["CONTENT: # NoSQL databases …", "CONTENT: # relational database fundamentals …"],
  "retrieval_grade": "relevant",
  "retrieval_confidence": 0.8,
  "retrieval_retries": 0,
  "retrieval_error": null
}
```

Telemetry is first-class: `retrieval_grade` (`relevant` · `irrelevant` · `unavailable`), `retrieval_confidence`, `retrieval_retries`, and `retrieval_error` — non-null only when the vector store itself was unreachable. The UI renders that as a distinct *"Retrieval unavailable"* state, so an infrastructure failure is never presented as a relevance verdict.

---

## Evaluation & CI

Two independent judges over the same pipeline, so scores are not one vendor's opinion:

| Suite | Metrics | Notes |
|---|---|---|
| **RAGAS** | faithfulness, answer_relevancy, context_precision, context_recall | retrieval + grounding quality |
| **DeepEval** | faithfulness, hallucination, answer_correctness, scope_adherence | grounding, correctness, guardrail scope |

Thresholds live in [`evals/thresholds.py`](evals/thresholds.py) (for example faithfulness ≥ 0.80, context_recall ≥ 0.75, hallucination ≤ 0.30) and the runners **exit non-zero** when a metric breaches its gate, so they work directly as CI checks. See [`evals/README.md`](evals/README.md) for metric definitions and the golden dataset format.

```bash
python -m evals.run_ragas    --record evals/fixtures/samples.json   # call backend + score
python -m evals.run_deepeval --samples evals/fixtures/samples.json  # re-score, no Qdrant needed
pytest -q                                                           # 16 offline unit tests
```

`.github/workflows/rag-eval.yml` runs the offline unit tests on every push and PR, and runs the RAGAS + DeepEval gates when a deployed backend and judge key are configured — plus a weekly regression sweep.

---

## UI

The React client ([`frontend/README.md`](frontend/README.md)) renders streamed-feel answers, the agent's plan steps, every retrieved chunk with its source, and the Self-RAG telemetry chips (context verified / low relevance, grader confidence, rewrite count, latency) — with a live backend status dot and `localStorage`-persisted conversation memory keyed to `thread_id`.

---

## Known limitations

Deliberately documented rather than hidden:

- **Guardrail scope is narrower than the corpus.** `app/guardrails/colang_rules.py` still describes an enterprise-IT assistant (Kubernetes / Intel / networking), while the indexed corpus spans 13 domains; broaden the Colang intents before exposing the API publicly. The evaluation suite's `scope_adherence` metric tracks the same boundary.
- **Ingestion is not idempotent.** Point IDs are random UUIDs and content is not hashed, so re-running a folder without `--wipe` duplicates its chunks.
- **No payload index on `source_type`.** Filtered counts/searches return HTTP 400 until one is created; the current pipeline filters nothing.
- **The vector store is a hard dependency for grounded answers.** Outages are now surfaced (see `retrieval_error`) rather than silently degrading, but the service still answers from model knowledge in that state.
- **A legacy `enterprise_rag` collection** (single unnamed 768-d vector, pre-hybrid schema) remains in the cluster; nothing in the code points at it.
- **Logfire's console exporter** raises a `UnicodeEncodeError` on Windows `cp1252` terminals and prints stack traces into the server log; run with `PYTHONIOENCODING=utf-8` for clean output.

---

## Diagram provenance

Every diagram in this README is generated from a typed JSON specification with the [archify](https://github.com/tt-a1i/archify) skill and passed its validation, delivery, provenance and headless-browser gates — no hand-drawn boxes. Sources and explorable HTML exports are committed under `.archify/`; the SVG assets used above live in `docs/diagrams/`.

| Diagram | Type | Source |
|---|---|---|
| System architecture | architecture | `.archify/architecture-rag-system-20261028-021934/candidate.json` |
| Request lifecycle | sequence | `.archify/sequence-request-lifecycle-20261028-022800/candidate.json` |
| Self-RAG corrective loop | workflow | `.archify/workflow-self-rag-loop-20261028-022233/candidate.json` |
| Ingestion pipeline | dataflow | `.archify/dataflow-ingestion-pipeline-20261028-023107/candidate.json` |
