"""Prompts router: agentic workflows that tie tools together (course
requirement: at least one prompt with a human-confirmation step). The three
flagship workflows land in milestone 4 (mcp_PLAN.md §9); the router and its
registration exist from day one so the server surface is complete."""

from __future__ import annotations

from fastmcp import FastMCP

from src.tools import tutor


def register(app: FastMCP) -> None:
    @app.prompt
    def tutor_lesson(topic: str, audience: str = "kids") -> str:
        """Plan a kid-appropriate lesson on a KB topic. Workflow: outline the
        KB, search the relevant chapters, guardrail-check the framing, then
        draft the lesson — and STOP for human approval before the lesson is
        presented to any student (accept / edit / reject)."""
        outline = tutor.kb_outline_impl()
        chapters = ", ".join(e.doc for e in outline[:12])
        return (
            f"Plan a {audience}-appropriate Python lesson on: {topic}\n\n"
            "Steps:\n"
            f"1. The KB outline is: {chapters}. Pick the 2-3 most relevant docs.\n"
            "2. kb_search within each picked doc; kb_chunk the top hits for full text.\n"
            "3. guardrail_check your lesson framing (kids scope: no PII, allowlist topics).\n"
            "4. Draft the lesson: hook, 2-4 sections, one exercise, citations as "
            "doc#chunk refs. Every fact must come from the retrieved chunks.\n"
            "5. STOP: show the draft and ask me to accept, edit, or reject it. "
            "Do not present the lesson until I approve."
        )
