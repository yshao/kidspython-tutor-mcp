"""The server's own LLM path: the z.ai gateway (Anthropic protocol) via the
anthropic SDK — the same provider the tutor service uses, without importing
it. Blank key = LlmUnavailable (LLM tools degrade; the rest of the server
works). JSON answers parsed fence-tolerantly (ported from
chatbot scripts/eval/run_evals.parse_json)."""

from __future__ import annotations

import ast
import json
import re

from src.config.settings import llm_settings


class LlmUnavailable(RuntimeError):
    """No LLM key configured — synth/hint/judge tools are down."""


def complete(
    prompt: str, system: str | None = None, max_tokens: int | None = None
) -> str:
    s = llm_settings()
    if not s.zai_api_key:
        raise LlmUnavailable(
            "no LLM key configured — set ZAI_API_KEY in .env to enable "
            "synth_question / exercise_hint / grade_reply"
        )
    from anthropic import Anthropic

    client = Anthropic(api_key=s.zai_api_key, base_url=s.zai_base_url, max_retries=2)
    resp = client.messages.create(
        model=s.llm_model,
        max_tokens=max_tokens or s.llm_max_tokens,
        messages=[{"role": "user", "content": prompt}],
        **({"system": system} if system else {}),
    )
    blocks = [b.text for b in resp.content if getattr(b, "type", "") == "text"]
    return "".join(blocks).strip()


def parse_json(raw: str) -> dict:
    """LLM -> JSON, fence- and quote-tolerant (ported from the chatbot's
    eval runner: models wrap JSON in ``` fences or single-quoted dicts)."""
    txt = (raw or "").strip()
    if txt.startswith("```"):
        txt = re.sub(r"^```[a-zA-Z]*\n?", "", txt)
        txt = re.sub(r"\n?```$", "", txt).strip()
    m = re.search(r"\{.*\}", txt, re.DOTALL)
    if m:
        txt = m.group(0)
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        return ast.literal_eval(txt)  # single quotes / trailing commas
