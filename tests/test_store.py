"""Store: the 3 memory patterns persist ACROSS Store instances (the
restart-persistence acceptance) and the HITL approval lifecycle works."""

import pytest

from src.app.store import Store

EVENT_KINDS_ERROR = "kind must be one of"


@pytest.fixture
def store(tmp_path):
    path = tmp_path / "mem.sqlite"
    first = Store(path)  # one process "session"
    first.add_episode("s1", "lesson_done", "finished chapter 3")
    first.mark_mastered("s1", "variables")
    first.set_preference("s1", "hint_level", "nudge")
    first.stage_lesson("s1", "loops", "draft text")
    return path  # "restart": a brand-new Store over the same file


def test_memory_survives_restart(store):
    second = Store(store)
    assert second.episodes("s1")[0]["kind"] == "lesson_done"
    assert second.mastered("s1")[0]["topic"] == "variables"
    assert second.preferences("s1")["hint_level"] == "nudge"
    assert len(second.pending_lessons("s1")) == 1


def test_mastered_upsert_keeps_first_seen(store):
    s = Store(store)
    first_seen = s.mastered("s1")[0]["first_seen"]
    s.mark_mastered("s1", "variables")  # re-master: bump last_seen only
    row = s.mastered("s1")[0]
    assert row["first_seen"] == first_seen and row["last_seen"] >= first_seen


def test_decide_lesson_lifecycle(store):
    s = Store(store)
    approval_id = s.pending_lessons("s1")[0]["id"]
    out = s.decide_lesson(approval_id, "s1", "edited", "better draft")
    assert out["status"] == "edited" and out["edited_draft"] == "better draft"
    assert s.pending_lessons("s1") == []


def test_decide_rejects_bad_status(store):
    s = Store(store)
    with pytest.raises(ValueError, match="bad status"):
        s.decide_lesson(1, "s1", "maybe")


def test_decide_cannot_bypass_ownership(store):
    # security review finding: one student must not decide another's approval
    s = Store(store)
    approval_id = s.pending_lessons("s1")[0]["id"]
    assert s.decide_lesson(approval_id, "s2", "accepted") is None
    assert len(s.pending_lessons("s1")) == 1  # untouched


def test_stage_rejects_oversized_draft(store):
    s = Store(store)
    with pytest.raises(ValueError, match="draft too large"):
        s.stage_lesson("s1", "loops", "x" * 20_001)


def test_progress_record_validates_kind(store):
    from src.tools.progress import progress_record_impl

    with pytest.raises(ValueError, match=EVENT_KINDS_ERROR):
        progress_record_impl("s1", {"kind": "nonsense"})
