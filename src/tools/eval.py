"""Eval-surface tools: Langfuse score reads, synthetic question generation,
and the registry-criterion LLM judge. Langfuse + LLM degrade independently
(eval_scores needs LANGFUSE_*; synth/grade need ZAI_API_KEY)."""

from __future__ import annotations

import base64
import json
import pathlib
import urllib.request

from src.app import llm
from src.app.models import EvalScore, SynthQuestion
from src.config.settings import settings


class EvalUnavailable(RuntimeError):
    """Langfuse keys missing or the API is unreachable."""


def _registry() -> dict:
    path = (
        pathlib.Path(__file__).resolve().parents[1]
        / "app"
        / "data_metrics_registry.json"
    )
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _lf_get(path: str) -> dict:
    s = settings()
    if not (s.langfuse_public_key and s.langfuse_secret_key):
        raise EvalUnavailable(
            "Langfuse not configured — set LANGFUSE_PUBLIC_KEY/SECRET_KEY"
        )
    auth = base64.b64encode(
        f"{s.langfuse_public_key}:{s.langfuse_secret_key}".encode()
    ).decode()
    req = urllib.request.Request(
        f"{s.langfuse_host.rstrip('/')}{path}",
        headers={"Authorization": "Basic " + auth},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except Exception as exc:
        raise EvalUnavailable(f"Langfuse unreachable: {type(exc).__name__}") from exc


def eval_scores_impl(trace_id: str) -> list[EvalScore]:
    thresholds = {m["name"]: m["pass_threshold"] for m in _registry()["metrics"]}
    trace = _lf_get(f"/api/public/traces/{trace_id}")
    out = []
    for s in trace.get("scores") or []:
        name = s.get("name") or ""
        out.append(
            EvalScore(
                name=name,
                value=float(s.get("value") or 0),
                pass_threshold=thresholds.get(name),
                passed=(
                    float(s.get("value") or 0) >= thresholds[name]
                    if name in thresholds
                    else None
                ),
                comment=(s.get("comment") or "")[:300],
            )
        )
    return out


def registry_metrics() -> dict:
    return _registry()


def synth_question_impl(chunk_id: str) -> SynthQuestion:
    from src.tools.tutor import kb_chunk_impl

    chunk = kb_chunk_impl(chunk_id)
    raw = llm.complete(
        "You write practice questions for kids learning Python. Read this "
        "course snippet and write ONE question a kid student could answer "
        "from it. Vary the style (what / why / how / exercise).\n\n"
        f"Snippet:\n{chunk.text}\n\n"
        'Answer with JSON only: {"question": str, "kind": "what"|"why"|'
        '"how"|"exercise"}'
    )
    data = llm.parse_json(raw)
    return SynthQuestion(
        question=data["question"], source_chunk_id=chunk.chunk_id, kind=data["kind"]
    )


def grade_reply_impl(
    question: str, reply: str, metric: str = "deepeval_directness"
) -> EvalScore:
    reg = {m["name"]: m for m in _registry()["metrics"]}
    if metric not in reg or "criteria" not in reg[metric]:
        raise ValueError(
            f"unknown judge metric: {metric!r} — pick a GEval "
            f"metric from tutor://eval/metrics"
        )
    m = reg[metric]
    raw = llm.complete(
        f"Evaluate the reply against ONE criterion. Score 0.0-1.0 "
        f"(1 = fully meets it). Reply with JSON only: "
        f'{{"score": float, "reason": str}}\n\n'
        f"Criterion ({m['name']}): {m['criteria']}\n\n"
        f"Question: {question}\n\nReply: {reply}"
    )
    data = llm.parse_json(raw)
    score = float(data["score"])
    return EvalScore(
        name=metric,
        value=score,
        pass_threshold=m["pass_threshold"],
        passed=score >= m["pass_threshold"],
        comment=(data.get("reason") or "")[:300],
    )
