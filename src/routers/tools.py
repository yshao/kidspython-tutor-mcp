"""Tools router: registers every tool with the FastMCP app using decorators
(the course-prescribed pattern — implementations live in src/tools/, this
module is the registration surface)."""

from __future__ import annotations

from fastmcp import FastMCP

from src.tools import guardrail, progress, tutor


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

    @app.tool
    def guardrail_check(question: str, persona_id: str | None = None) -> dict:
        """Scope-screen a question with the tutor's kid-safety guard:
        allowlist topic check, PII scrub ('I am 9' / emails / phones /
        school names → [removed] + notice), and the refusal template for
        out-of-scope topics. Works offline (bundled kidspython scope);
        persona_id pulls live scope config from the tutor when up."""
        return guardrail.guardrail_check_impl(question, persona_id).model_dump()

    @app.tool
    def progress_get(student_id: str) -> dict:
        """One student's long-term memory: recent episodes (episodic),
        mastered topics (semantic), preferences like hint_level and pacing
        (procedural), and any lesson drafts awaiting approval. Persisted in
        the server's SQLite — survives restarts."""
        return progress.progress_get_impl(student_id).model_dump()

    @app.tool
    def progress_record(student_id: str, event: dict) -> dict:
        """Record a learning event. event = {"kind": "episode"|"lesson_done"|
        "topic_mastered"|"pref_set", "topic": str, "detail"?: str,
        "thread_id"?: str}. lesson_done also marks the topic mastered;
        pref_set stores a procedural preference (e.g. topic=hint_level,
        detail=path)."""
        return progress.progress_record_impl(student_id, event)

    @app.tool
    def stage_lesson(student_id: str, topic: str, draft: str) -> dict:
        """Human-in-the-loop gate: stage a lesson draft as pending approval.
        Nothing is presented to the student until decide_lesson accepts or
        edits it. Returns {approval_id, status: 'pending'}."""
        return progress.stage_lesson_impl(student_id, topic, draft)

    @app.tool
    def decide_lesson(
        approval_id: int, status: str, edited_draft: str | None = None
    ) -> dict:
        """Resolve a staged lesson: status = accepted | edited | rejected
        (edited requires edited_draft). Returns the final decision row."""
        return progress.decide_lesson_impl(approval_id, status, edited_draft)
