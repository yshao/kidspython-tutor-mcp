"""Prompts router: the three agentic workflows (course requirement: at
least one prompt ties tools into a workflow with a human-confirmation step;
all three have one). Each prompt returns the workflow script for the client
LLM — the tools do the work, the gates stop for a human."""

from __future__ import annotations

from fastmcp import FastMCP

from src.tools import tutor


def register(app: FastMCP) -> None:
    @app.prompt
    def tutor_lesson(
        topic: str, audience: str = "kids", student_id: str = "demo-student"
    ) -> str:
        """Plan a kid-appropriate lesson on a KB topic. Agentic workflow:
        outline the KB → parallel search of the 2-3 relevant chapters →
        guardrail-check the framing → structured draft → STAGE for approval
        (stage_lesson) → STOP for the human accept/edit/reject decision
        (decide_lesson). Nothing is presented to the student unapproved."""
        outline = tutor.kb_outline_impl()
        chapters = ", ".join(e.doc for e in outline[:12])
        return (
            f"Plan a {audience}-appropriate Python lesson on: {topic}\n"
            f"student_id for the approval record: {student_id}\n\n"
            "Workflow (use the MCP tools):\n"
            f"1. KB outline: {chapters}. Pick the 2-3 most relevant docs.\n"
            "2. kb_search once per picked doc (parallel fan-out), then kb_chunk "
            "the top hit of each for full text.\n"
            "3. guardrail_check the lesson framing — kids scope, no PII. If it "
            "refuses, reframe and re-check; never skip this step.\n"
            "4. Draft the lesson as: hook, 2-4 sections, one exercise, citations "
            "as doc#NNN refs. EVERY fact must come from the retrieved chunks; "
            "if the KB lacks the topic, say so and pick the nearest covered "
            "topic instead of inventing.\n"
            "5. stage_lesson(student_id, topic, draft) to persist it as pending.\n"
            "6. STOP — show me the draft and ask: accept / edit / reject. On my "
            "decision call decide_lesson (with edited_draft if I edited). Only "
            "after an accepted/edited verdict may the lesson be presented."
        )

    @app.prompt
    def exercise_coach(
        thread_id: str, attempt: str, student_id: str = "demo-student"
    ) -> str:
        """Coach a student's exercise attempt: plan-and-execute with hint
        escalation under the guide-don't-solve rule, and a confirm-before-
        escalate gate. Diagnoses against the KB, never gives the solution."""
        prefs = "unknown (default nudge)"
        return (
            f"Coach this attempt on thread {thread_id} (student {student_id}). "
            f"Attempt: {attempt!r}\n"
            f"Known preferences: {prefs} — read the real ones with "
            f"progress_get('{student_id}') first.\n\n"
            "Plan-and-execute:\n"
            "1. PLAN: kb_search the exercise's topic (thread context helps) and "
            "kb_chunk the best hit; diagnose which concept the attempt misses.\n"
            "2. Pick the hint level from the student's stored preference and the "
            "diagnosis: nudge (which part to reconsider) < hint (the concept, "
            "not the code) < path (the next concrete step, still not the code).\n"
            "3. EXECUTE: give the hint — grounded in the chunk, cite doc#NNN. "
            "NEVER output the completed solution; that is the persona's rule.\n"
            "4. If the student is still stuck, STOP and ask them whether they "
            "want the next hint level before escalating. Record the outcome with "
            "progress_record (topic_mastered when they succeed)."
        )

    @app.prompt
    def curate_eval_set(count: int = 10, student_id: str = "demo-student") -> str:
        """Build a synthetic eval dataset from KB chunks — the human selects
        which generated questions are kept (mirrors the production curation
        loop; output format matches questions-50.jsonl)."""
        outline = tutor.kb_outline_impl()
        docs = [e["doc"] for e in outline if e["chunks"] > 1][:8]
        return (
            f"Curate {count} synthetic eval questions from the KB.\n\n"
            f"1. Pick {min(count, len(docs))} docs from: {docs} (round-robin for "
            "diversity).\n"
            "2. For each doc: kb_search a core concept, kb_chunk the top hit, "
            "then synth_question(chunk_id) to generate ONE kid-style question.\n"
            "3. Show me the batch as a numbered list with {question, "
            "source_chunk_id, kind} each and STOP.\n"
            "4. Keep ONLY the questions I approve; output the kept set as JSONL "
            "(one JSON object per line) ready for the kidspython-eval dataset. "
            "Discard the rest without comment."
        )
