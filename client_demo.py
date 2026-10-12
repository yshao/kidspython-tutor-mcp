#!/usr/bin/env python3
"""MCP client demo (course custom feature: programmatic client with custom
orchestration). Plans and delivers a micro-lesson end-to-end against the
kidspython-tutor MCP server — no Cursor, no human in the loop here (the
approval step is simulated; the interactive path is the tutor_lesson prompt):

  outline → pick chapter → search + chunk → guardrail → draft → stage →
  approve → present → comprehension check (tutor_ask) → grade → progress

Run: uv run python client_demo.py [topic]
"""

from __future__ import annotations

import asyncio
import sys
import uuid

from fastmcp import Client

from src.server import create_server


def line(step: str, msg: str) -> None:
    print(f"[{step:>9}] {msg}")


async def main() -> int:
    topic = sys.argv[1] if len(sys.argv) > 1 else "for loops"
    student = "demo-student"
    app = create_server()
    async with Client(app) as c:
        line(
            "surface",
            f"{len(await c.list_tools())} tools, "
            f"{len(await c.list_resources())} resources, "
            f"{len(await c.list_prompts())} prompts",
        )

        outline = await c.call_tool("kb_outline", {})
        chapters = [e["doc"] for e in outline.data if e["chunks"] > 2]
        pick = next((d for d in chapters if topic.split()[0] in d), chapters[0])
        line("plan", f"topic={topic!r} → chapter {pick}")

        search = await c.call_tool(
            "kb_search", {"query": topic, "doc": pick, "limit": 2}
        )
        hits = search.data
        if not hits:
            print(f"no KB hits for {topic!r} in {pick} — try another topic")
            return 1
        chunk = (await c.call_tool("kb_chunk", {"chunk_id": hits[0]["chunk_id"]})).data
        line("retrieve", f"{len(hits)} hits; grounding on {chunk['chunk_id']}")

        guard = (await c.call_tool("guardrail_check", {"question": topic})).data
        if not guard["allowed"]:
            print(f"guardrail refused the framing: {guard['refusal']}")
            return 1
        line(
            "guard",
            "framing in scope"
            + (f" (notice: {guard['notice']})" if guard["notice"] else ""),
        )

        draft = (
            f"Lesson: {chunk['title']}\n"
            f"Hook: ever wondered how {topic} work?\n"
            f"Body: {chunk['text']}\n"
            f"Citation: {chunk['chunk_id']}"
        )
        staged = (
            await c.call_tool(
                "stage_lesson", {"student_id": student, "topic": topic, "draft": draft}
            )
        ).data
        line("hitl", f"staged approval #{staged['approval_id']} ({staged['status']})")
        # the human decision — interactive flows stop here; the demo accepts
        decided = (
            await c.call_tool(
                "decide_lesson",
                {
                    "approval_id": staged["approval_id"],
                    "student_id": student,
                    "status": "accepted",
                },
            )
        ).data
        line("hitl", f"decision: {decided['status']} → lesson presented")

        check_q = (
            "What is a variable?"  # composes; exercise-y phrasings bind to the flow
        )
        turn = (
            await c.call_tool(
                "tutor_ask",
                {
                    "message": check_q,
                    "thread_id": f"client-demo-{uuid.uuid4().hex[:8]}",
                },
            )
        ).data
        line("tutor", turn["reply"][:120] + ("…" if len(turn["reply"]) > 120 else ""))

        try:
            grade = (
                await c.call_tool(
                    "grade_reply", {"question": check_q, "reply": turn["reply"]}
                )
            ).data
            line(
                "grade",
                f"{grade['name']}={grade['value']} "
                f"(threshold {grade['pass_threshold']}, "
                f"passed={grade['passed']})",
            )
        except Exception as exc:  # noqa: BLE001 — the demo tolerates any
            # single-step failure (LLM key missing, service down) and reports it
            line("grade", f"skipped ({type(exc).__name__})")

        rec = (
            await c.call_tool(
                "progress_record",
                {
                    "student_id": student,
                    "event": {
                        "kind": "lesson_done",
                        "topic": topic,
                        "detail": chunk["chunk_id"],
                    },
                },
            )
        ).data
        line(
            "memory",
            f"recorded: {rec['mastered']} topics mastered, {rec['episodes']} episodes",
        )
    print("demo complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
