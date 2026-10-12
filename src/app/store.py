"""MCP-side long-term memory (course custom feature: 3 patterns) + lesson
approval rows (human-in-the-loop). SQLite via stdlib; one Store instance per
process, schema created idempotently on open — progress survives restarts.

Patterns:
  episodic   episodes(student_id, ts, thread_id, kind, summary)
  semantic   mastered(student_id, topic, first_seen, last_seen)
  procedural preferences(student_id, key, value)   e.g. hint_level, pacing
  hitl       lesson_approvals(draft, status pending→accepted/edited/rejected)
"""

from __future__ import annotations

import sqlite3
import time
from functools import lru_cache
from pathlib import Path

from src.config.settings import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS episodes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  student_id TEXT NOT NULL, ts REAL NOT NULL,
  thread_id TEXT, kind TEXT NOT NULL, summary TEXT);
CREATE INDEX IF NOT EXISTS idx_ep_student ON episodes(student_id, ts);
CREATE TABLE IF NOT EXISTS mastered (
  student_id TEXT NOT NULL, topic TEXT NOT NULL,
  first_seen REAL NOT NULL, last_seen REAL NOT NULL,
  PRIMARY KEY (student_id, topic));
CREATE TABLE IF NOT EXISTS preferences (
  student_id TEXT NOT NULL, key TEXT NOT NULL, value TEXT NOT NULL,
  updated_at REAL NOT NULL,
  PRIMARY KEY (student_id, key));
CREATE TABLE IF NOT EXISTS lesson_approvals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  student_id TEXT NOT NULL, topic TEXT NOT NULL,
  draft TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending',
  edited_draft TEXT, ts REAL NOT NULL);
"""


class Store:
    def __init__(self, path: Path | None = None):
        p = Path(path or settings().store_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(p, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)

    # -- episodic -----------------------------------------------------------

    def add_episode(
        self, student_id: str, kind: str, summary: str, thread_id: str | None = None
    ) -> None:
        self.db.execute(
            "INSERT INTO episodes (student_id, ts, thread_id, kind, summary) "
            "VALUES (?, ?, ?, ?, ?)",
            (student_id, time.time(), thread_id, kind, summary),
        )
        self.db.commit()

    def episodes(self, student_id: str, limit: int = 20) -> list[dict]:
        rows = self.db.execute(
            "SELECT ts, thread_id, kind, summary FROM episodes "
            "WHERE student_id = ? ORDER BY ts DESC LIMIT ?",
            (student_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    # -- semantic -----------------------------------------------------------

    def mark_mastered(self, student_id: str, topic: str) -> None:
        now = time.time()
        self.db.execute(
            "INSERT INTO mastered (student_id, topic, first_seen, last_seen) "
            "VALUES (?, ?, ?, ?) ON CONFLICT(student_id, topic) "
            "DO UPDATE SET last_seen = excluded.last_seen",
            (student_id, topic, now, now),
        )
        self.db.commit()

    def mastered(self, student_id: str) -> list[dict]:
        rows = self.db.execute(
            "SELECT topic, first_seen, last_seen FROM mastered "
            "WHERE student_id = ? ORDER BY last_seen DESC",
            (student_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    # -- procedural ---------------------------------------------------------

    def set_preference(self, student_id: str, key: str, value: str) -> None:
        self.db.execute(
            "INSERT INTO preferences (student_id, key, value, updated_at) "
            "VALUES (?, ?, ?, ?) ON CONFLICT(student_id, key) "
            "DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at",
            (student_id, key, value, time.time()),
        )
        self.db.commit()

    def preferences(self, student_id: str) -> dict:
        rows = self.db.execute(
            "SELECT key, value FROM preferences WHERE student_id = ?", (student_id,)
        ).fetchall()
        return {r["key"]: r["value"] for r in rows}

    # -- human-in-the-loop lesson approvals ---------------------------------

    def stage_lesson(self, student_id: str, topic: str, draft: str) -> int:
        cur = self.db.execute(
            "INSERT INTO lesson_approvals (student_id, topic, draft, ts) "
            "VALUES (?, ?, ?, ?)",
            (student_id, topic, draft, time.time()),
        )
        self.db.commit()
        return cur.lastrowid

    def decide_lesson(
        self, approval_id: int, status: str, edited_draft: str | None = None
    ) -> dict | None:
        if status not in ("accepted", "edited", "rejected"):
            raise ValueError(f"bad status: {status!r}")
        cur = self.db.execute(
            "UPDATE lesson_approvals SET status = ?, edited_draft = ? "
            "WHERE id = ? RETURNING student_id, topic, draft, edited_draft, status",
            (status, edited_draft, approval_id),
        )
        rows = cur.fetchall()  # consume: RETURNING holds the txn open otherwise
        self.db.commit()
        return dict(rows[0]) if rows else None

    def pending_lessons(self, student_id: str) -> list[dict]:
        rows = self.db.execute(
            "SELECT id, topic, draft, ts FROM lesson_approvals "
            "WHERE student_id = ? AND status = 'pending' ORDER BY ts DESC",
            (student_id,),
        ).fetchall()
        return [dict(r) for r in rows]


@lru_cache(maxsize=1)
def shared_store() -> Store:
    return Store()
