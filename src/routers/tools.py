"""Tools router: registers every tool with the FastMCP app using decorators
(the course-prescribed pattern — implementations live in src/tools/, this
module is the registration surface)."""

from __future__ import annotations

from fastmcp import FastMCP

from src.tools import tutor


def register(app: FastMCP) -> None:
    @app.tool
    def tutor_ask(
        message: str, thread_id: str | None = None, persona: str | None = None
    ) -> dict:
        """Ask the kidspython-tutor a question (live service). Returns the
        tutor's reply plus flow state: awaiting (scripted next step),
        low_confidence, refusal (guardrail), and the tools trace. Requires
        the tutor service; raises TutorUnavailable when it is down.
        thread_id pins the persona per thread — omit for a new thread."""
        return tutor.tutor_ask_impl(message, thread_id, persona).model_dump()

    @app.tool
    def kb_search(query: str, doc: str | None = None, limit: int = 5) -> list[dict]:
        """Search the kidspython course knowledge base (580 chunks over 12
        chapters). Works offline (built chunks.jsonl) and via the live
        service when available. doc narrows to one chapter route
        (e.g. '/courses/chapter-3-variables')."""
        return [h.model_dump() for h in tutor.kb_search_impl(query, doc, limit)]

    @app.tool
    def kb_chunk(chunk_id: str) -> dict:
        """Fetch one knowledge-base chunk in full by its id
        (e.g. '/courses/chapter-3-variables#004'). chunk_ids come from
        kb_search or the tutor://kb/outline resource."""
        return tutor.kb_chunk_impl(chunk_id).model_dump()

    @app.tool
    def kb_outline() -> list[dict]:
        """Outline of the knowledge base: every doc/chapter with chunk and
        exercise counts — the map to plan lessons against."""
        return [e.model_dump() for e in tutor.kb_outline_impl()]
