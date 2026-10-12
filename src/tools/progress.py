"""progress_get / progress_record tools + the lesson-approval HITL surface
(stage_lesson / decide_lesson / pending). Memory patterns live in
src/app/store.py; this module is the tool-facing contract."""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.app.store import Store, shared_store

EVENT_KINDS = ("episode", "lesson_done", "topic_mastered", "pref_set")


class Progress(BaseModel):
    student_id: str
    episodes: list[dict] = Field(default_factory=list)
    mastered_topics: list[dict] = Field(default_factory=list)
    preferences: dict = Field(default_factory=dict)
    pending_lessons: list[dict] = Field(default_factory=list)


def _store() -> Store:
    return shared_store()


def progress_get_impl(student_id: str) -> Progress:
    s = _store()
    return Progress(
        student_id=student_id,
        episodes=s.episodes(student_id),
        mastered_topics=s.mastered(student_id),
        preferences=s.preferences(student_id),
        pending_lessons=s.pending_lessons(student_id),
    )


def progress_record_impl(student_id: str, event: dict) -> dict:
    kind = event.get("kind")
    if kind not in EVENT_KINDS:
        raise ValueError(f"kind must be one of {EVENT_KINDS}")
    s = _store()
    if kind == "episode":
        s.add_episode(
            student_id,
            str(event.get("topic", "chat")),
            str(event.get("detail", "")),
            thread_id=event.get("thread_id"),
        )
    elif kind == "lesson_done":
        s.add_episode(
            student_id, "lesson_done", str(event.get("detail", event.get("topic", "")))
        )
        s.mark_mastered(student_id, str(event["topic"]))
    elif kind == "topic_mastered":
        s.mark_mastered(student_id, str(event["topic"]))
    elif kind == "pref_set":
        s.set_preference(student_id, str(event["topic"]), str(event.get("detail", "")))
    return {
        "ok": True,
        "mastered": len(s.mastered(student_id)),
        "episodes": len(s.episodes(student_id, limit=1000)),
    }


def stage_lesson_impl(student_id: str, topic: str, draft: str) -> dict:
    return {
        "approval_id": _store().stage_lesson(student_id, topic, draft),
        "status": "pending",
    }


def decide_lesson_impl(
    approval_id: int, status: str, edited_draft: str | None = None
) -> dict:
    out = _store().decide_lesson(approval_id, status, edited_draft)
    if out is None:
        raise ValueError(f"unknown approval_id: {approval_id}")
    return out
