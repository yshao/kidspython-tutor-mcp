# kidspython-tutor-mcp

[![Python](https://img.shields.io/badge/python-3.14-blue?style=flat-square)](https://www.python.org)
[![Checked with ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json&style=flat-square)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)

**Give any MCP client a kid-safe Python tutor.** This MCP server exposes the
[kidspython-tutor](https://gitlab.com/yshaoeng/chatbot) chatbot — a flow-driven,
knowledge-base-grounded Python tutor for kids with a "helpful professor" persona — as a
protocol: ask the tutor, search its course knowledge base, screen questions through its
kid-safety guardrail, coach exercises with escalating hints (never the solution), track
student progress across sessions, and inspect or curate the RAGAS/DeepEval evaluation
layer.

Built as the final project for the Towards AI MCP course. The interesting engineering
constraint: the tutor service runs its own pinned Python environment, so this server
integrates strictly over the service's HTTP contract and a file-backed knowledge-base
fallback — zero shared code, two independently managed environments.

## What it does

| Tool | What it gives the client |
|---|---|
| `tutor_ask` | a live tutor turn: persona reply + flow state (`awaiting`, `low_confidence`, guardrail `refusal`) |
| `kb_search` / `kb_chunk` / `kb_outline` | the 580-chunk course knowledge base (12 chapters), retrieval parity with the service (idf + anchor lookup) |
| `guardrail_check` | the kid-safety scope gate: topic allowlist, PII scrub (`[removed]` + notice), refusal template |
| `exercise_hint` | guide-don't-solve coaching: `nudge → hint → path`, never the completed solution |
| `progress_get` / `progress_record` | per-student long-term memory: episodes, mastered topics, preferences — persisted in SQLite |
| `eval_scores` | the RAGAS/DeepEval scores pushed onto any tutor trace (Langfuse) |
| `synth_question` / `grade_reply` | eval-set generation from KB chunks and LLM-judge grading against the metric registry |

Resources give clients standing context (`tutor://kb/outline`,
`tutor://kb/chunks/{id}`, `tutor://personas/{id}`, `tutor://progress/{student}`,
`tutor://eval/metrics`), and three prompts encode complete agentic workflows —
`tutor_lesson` is the flagship: outline → parallel chapter search → guardrail check →
structured draft → **human accept/edit/reject gate before anything reaches a student**.

## Project setup

Requires [uv](https://docs.astral.sh/uv/) and Python 3.14 (uv fetches it).

```sh
git clone https://github.com/yshao/kidspython-tutor-mcp
cd kidspython-tutor-mcp
uv sync                      # creates .venv with Python 3.14
cp .env.sample .env          # then fill in your values (see below)
uv run pytest                # 32 tests, runs fully offline
uv run kidspython-tutor-mcp  # MCP server on stdio
```

The knowledge-base tools work with **no tutor service running** (they read the built
chunks file). `tutor_ask` needs the kidspython-tutor service reachable at `TUTOR_BASE_URL`
— either locally (`uvicorn service.app:app --port 8100` in the chatbot repo) or through
an SSH tunnel to a deployment. The client demo exercises the whole chain:

```sh
uv run python client_demo.py "for loops"
```

## Environment variables

Copy `.env.sample` to `.env` and fill in:

| Variable | Required | How to get it |
|---|---|---|
| `TUTOR_BASE_URL` | for `tutor_ask` | the tutor service URL; `http://127.0.0.1:8100` locally, or your tunnel/deployment URL |
| `TUTOR_USER` / `TUTOR_PASS` | for `tutor_ask` | any account registered on the tutor service (its `/login` page creates one) |
| `KB_PATH` | for KB tools | absolute path to the tutor's `datasets/kidspython-kb/<version>/built/chunks.jsonl` (built by the tutor repo's ingestion pipeline); any file with the same line schema works |
| `KB_DATASET` / `KB_VERSION` | optional | which KB the HTTP endpoint serves (defaults `kidspython-kb` / `1.1.0`) |
| `STORE_PATH` | optional | SQLite file for student memory (default `./data/tutor_mcp.sqlite`) |
| `ZAI_API_KEY` | for `exercise_hint`, `synth_question`, `grade_reply` | a [Z.ai](https://z.ai) API key (the tutor's LLM gateway, Anthropic protocol) — without it these tools raise a clear "not configured" error and everything else works |
| `ZAI_BASE_URL` / `LLM_MODEL` | optional | gateway override / model id (default `glm-4.6`) |
| `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` / `LANGFUSE_HOST` | for `eval_scores` | a [Langfuse](https://langfuse.com) project (keys from the project settings page) |

Never commit `.env`. There are no other credentials.

## Connect from an MCP client

Cursor (`.cursor/mcp.json`) — the course-reference shape:

```json
{
    "mcp_servers": {
        "kidspython-tutor-mcp": {
            "command": "uv",
            "args": [
                "--directory",
                "/absolute/path/to/kidspython-tutor-mcp",
                "run",
                "kidspython-tutor-mcp"
            ],
            "env": {
                "TUTOR_BASE_URL": "http://127.0.0.1:8100",
                "KB_PATH": "/absolute/path/to/chunks.jsonl",
                "ZAI_API_KEY": "your-api-key-here"
            }
        }
    }
}
```

Claude Code: `claude mcp add kidspython-tutor-mcp -- uv --directory /absolute/path/to/kidspython-tutor-mcp run kidspython-tutor-mcp`.

Then try: *"Use tutor_lesson to plan a lesson on for loops"* — the workflow stops for
your accept/edit/reject before the lesson is presented.

## Required features (course checklist)

- **FastMCP server in Python** — `src/server.py` builds the FastMCP app and registers routers; uv-managed, Python 3.14.
- **Meaningful tools** — 12 tools across the tutor, knowledge-base, guardrail, progress and eval domains (§ tool table above).
- **Prompt with an agentic workflow + human confirmation** — `tutor_lesson`: KB outline → parallel chapter search → guardrail check → structured draft → **stop for human accept/edit/reject** (`stage_lesson`/`decide_lesson`); `exercise_coach` and `curate_eval_set` also gate on the human.
- **Public GitHub repository** — this one, MIT-licensed.
- **uv initialization with Python 3.14** — `uv init --python 3.14.0`, lockfile committed.
- **Clear, organized structure** — exactly the prescribed layout: `src/server.py`, `src/routers/{tools,resources,prompts}.py`, `src/tools/`, `src/resources/`, `src/prompts/`, `src/app/`, `src/utils/`, `src/config/settings.py` (pydantic-settings).
- **Comprehensive README** — this file: setup, env table, client config, feature lists.
- **No committed secrets** — `.env` is gitignored; `.env.sample` documents the shape.

## Custom features implemented (9)

1. **MCP client application with custom orchestration** — `client_demo.py` drives a full micro-lesson programmatically: plan chapter → parallel retrieve → guardrail → stage draft → approve → tutor comprehension check → LLM grade → progress record.
2. **Useful MCP resources** — six `tutor://` resources (KB outline/chunks, personas, progress, eval metrics) for context-without-tool-call.
3. **2-3 workflow patterns** — sequential (`tutor_lesson`), conditional branching (guardrail refuse-vs-answer), parallel fan-out (multi-chapter retrieval).
4. **Advanced agentic pattern** — plan-and-execute (`exercise_coach`: diagnose against the KB → plan hint level → execute → confirm-before-escalate → re-plan).
5. **RAG** — every lesson/answer is grounded in knowledge-base retrieval (document-retrieval system with idf/anchor scoring, deliberately at parity with the tutor's own retriever).
6. **3 long-term memory patterns** — episodic (per-student episode log), semantic (mastered topics), procedural (hint-level/pacing preferences), all in SQLite and proven to survive restarts by test.
7. **Human-in-the-loop validation beyond prompts** — lesson drafts persist as pending-approval rows with an edit path (`stage_lesson`/`decide_lesson`), authorization-scoped per student.
8. **Observability + evaluation layer** — the server's LLM steps ride the same Langfuse project as the tutor; `eval_scores` reads pushed RAGAS/DeepEval scores; a curated 25-sample question set and `grade_reply` (registry-criterion LLM judge) close the loop.
9. **Structured outputs + code quality/DevOps** — Pydantic models on every LLM/tool boundary; ruff (lint+format), pre-commit hooks, GitHub Actions CI on Python 3.14, Dockerfile + docker-compose.

## Docker

```sh
cp .env.sample .env   # fill in values
docker compose up --build
```

`docker-compose.yml` runs the server (stdio over `docker run -i`) with a persistent
`data/` volume for student memory; the Dockerfile installs dependencies with uv from the
lockfile (`--frozen`) on a Python 3.14 slim base.

## Architecture note

The server integrates with the tutor strictly over its HTTP contract (cookie login,
`POST /chat`, the `/kb/...` endpoint) plus a file fallback for the knowledge base — so
the course's Python 3.14 requirement never couples with the tutor's pinned runtime, and
every tool degrades with a structured error instead of crashing when the service is
unreachable. Retrieval and guardrail semantics are ported from the service source
(cited in module docstrings) so offline behavior stays comparable. See `mcp_PLAN.md` in
the parent workspace for the full PRD: contracts, milestones, risks.

## Troubleshooting

- **`TutorUnavailable` on `tutor_ask`** — the service is down or `TUTOR_BASE_URL` is wrong; `GET /healthz` is the quickest probe.
- **`KB unavailable`** — neither the service nor `KB_PATH` yielded chunks; point `KB_PATH` at a built `chunks.jsonl`.
- **`no LLM key configured`** — `exercise_hint`/`synth_question`/`grade_reply` need `ZAI_API_KEY`; all other tools work without it.
- **`tutor login failed`** — wrong `TUTOR_USER`/`TUTOR_PASS` for the target service.

## License

MIT — see [LICENSE](LICENSE).
