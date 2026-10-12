"""Tool implementations: tutor turn + KB family. Thin — business logic in
src/app/. Docstrings are the MCP tool descriptions; write them for Cursor
users debugging from the client side."""

from __future__ import annotations

import uuid

from src.app import kb as kb_app
from src.app.models import KbChunk, KbHit, OutlineEntry, TutorTurn
from src.app.tutor_client import TutorUnavailable, shared_client


def tutor_ask_impl(
    message: str, thread_id: str | None = None, persona: str | None = None
) -> TutorTurn:
    """One live tutor turn. thread_id pins a persona per thread (service
    rule); omit it for a fresh conversation. Raises TutorUnavailable when
    the service is down — handle or surface, never retry blindly."""
    tid = thread_id or f"mcp-{uuid.uuid4().hex[:10]}"
    data = shared_client().chat(tid, message, persona)
    return TutorTurn(
        **{
            k: data.get(k)
            for k in (
                "reply",
                "awaiting",
                "low_confidence",
                "refusal",
                "error",
                "tools",
            )
        }
    )


def _kb() -> kb_app.Kb:
    return kb_app.load_kb()


def kb_search_impl(query: str, doc: str | None = None, limit: int = 5) -> list[KbHit]:
    return [KbHit(**h) for h in _kb().search(query, doc=doc, limit=limit)]


def kb_chunk_impl(chunk_id: str) -> KbChunk:
    c = _kb().chunk(chunk_id)
    if c is None:
        raise ValueError(
            f"unknown chunk_id: {chunk_id!r} — try kb_search "
            "or the tutor://kb/outline resource"
        )
    return KbChunk(**c)


def kb_outline_impl() -> list[OutlineEntry]:
    return [OutlineEntry(**e) for e in _kb().outline()]


__all__ = [
    "TutorUnavailable",
    "kb_chunk_impl",
    "kb_outline_impl",
    "kb_search_impl",
    "tutor_ask_impl",
]
