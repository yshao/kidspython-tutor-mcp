"""Knowledge-base access: HTTP-first against the tutor service's own
/kb/{dataset}/{version}/chunks endpoint, file-fallback to chunks.jsonl.

The search/outline logic ports service/services/knowledge.py (idf-weighted
term overlap over [a-z0-9] tokens minus STOPWORDS, anchor indexes by
route/title/exercise) so offline scores stay comparable with the live
service's retrieval. Retrieved chunks are data to cite, never instructions.
"""

from __future__ import annotations

import json
import math
import re
from functools import lru_cache
from pathlib import Path

from src.config.settings import settings

# ported verbatim from service/services/knowledge.py:31
STOPWORDS = frozenset(
    [
        "a",
        "about",
        "am",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "been",
        "being",
        "but",
        "by",
        "can",
        "could",
        "did",
        "do",
        "does",
        "explain",
        "for",
        "from",
        "give",
        "had",
        "has",
        "have",
        "how",
        "i",
        "if",
        "in",
        "is",
        "it",
        "may",
        "me",
        "might",
        "must",
        "my",
        "of",
        "on",
        "or",
        "please",
        "show",
        "shall",
        "should",
        "tell",
        "that",
        "the",
        "their",
        "them",
        "then",
        "these",
        "they",
        "this",
        "those",
        "to",
        "was",
        "we",
        "were",
        "what",
        "when",
        "where",
        "which",
        "who",
        "whom",
        "whose",
        "will",
        "with",
        "would",
        "you",
        "your",
    ]
)


class KbUnavailable(RuntimeError):
    """Neither the HTTP KB endpoint nor KB_PATH yielded chunks."""


def _load_file(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


@lru_cache(maxsize=2)
def _file_chunks(path_str: str) -> tuple[dict, ...]:
    return tuple(_load_file(Path(path_str)))


class Kb:
    """Anchor-primary retrieval ported from KnowledgeService; source is
    transparent to callers ('http' | 'file')."""

    def __init__(self, records: list[dict], source: str):
        self.source = source
        self._chunks = records
        self._by_route: dict[str, list[dict]] = {}
        self._by_title: dict[str, list[dict]] = {}
        self._by_exercise: dict[str, list[dict]] = {}
        for chunk in self._chunks:
            anchors = chunk.get("anchors") or {}
            if anchors.get("route"):
                self._by_route.setdefault(anchors["route"], []).append(chunk)
            title = anchors.get("title") or chunk.get("title")
            if title:
                self._by_title.setdefault(str(title).lower(), []).append(chunk)
            for ex in anchors.get("exercise_ids") or []:
                self._by_exercise.setdefault(ex, []).append(chunk)

    # -- lookup tiers (ported: knowledge.py retrieve/search) ----------------

    def chunk(self, chunk_id: str) -> dict | None:
        return next((c for c in self._chunks if c["chunk_id"] == chunk_id), None)

    def retrieve(
        self,
        route: str | None = None,
        title: str | None = None,
        exercise: str | None = None,
    ) -> list[dict]:
        if route is not None:
            return list(self._by_route.get(route, []))
        if exercise is not None:
            return list(self._by_exercise.get(exercise, []))
        if title is not None:
            return list(self._by_title.get(title.strip().lower(), []))
        return []

    def search(self, query: str, doc: str | None = None, limit: int = 5) -> list[dict]:
        pool = self._by_route.get(doc, []) if doc is not None else self._chunks
        terms = set(re.findall(r"[a-z0-9]+", query.lower())) - STOPWORDS
        df: dict[str, int] = {}
        bags: list[tuple[dict, set[str]]] = []
        for chunk in pool:
            bag = set(re.findall(r"[a-z0-9]+", chunk["text"].lower()))
            bags.append((chunk, bag))
            for term in bag:
                df[term] = df.get(term, 0) + 1
        n = max(len(pool), 1)
        scored = sorted(
            (
                (sum(math.log(n / df[t]) for t in terms & bag), chunk)
                for chunk, bag in bags
            ),
            key=lambda pair: (-pair[0], pair[1]["chunk_id"]),
        )
        hits = [
            {
                "chunk_id": c["chunk_id"],
                "doc": c.get("doc", ""),
                "title": c.get("title", ""),
                "snippet": c["text"][:200],
                "score": round(score, 3),
            }
            for score, c in scored
            if score > 0
        ]
        return hits[:limit]

    def outline(self) -> list[dict]:
        docs: dict[str, dict] = {}
        for c in self._chunks:
            d = docs.setdefault(
                c.get("doc", ""),
                {
                    "doc": c.get("doc", ""),
                    "title": c.get("title", ""),
                    "chunks": 0,
                    "exercise_ids": [],
                },
            )
            d["chunks"] += 1
            for ex in (c.get("anchors") or {}).get("exercise_ids") or []:
                if ex not in d["exercise_ids"]:
                    d["exercise_ids"].append(ex)
        return sorted(docs.values(), key=lambda d: d["doc"])


def load_kb() -> Kb:
    """HTTP-first: fetch chunks from the service; fall back to KB_PATH.
    Raises KbUnavailable only when both paths fail."""
    import httpx  # local import: kb.py stays importable without the service

    s = settings()
    url = f"{s.tutor_base_url}/kb/{s.kb_dataset}/{s.kb_version}/chunks"
    http_error: Exception | None = None
    try:
        with httpx.Client(timeout=10) as client:
            r = client.get(url)
            if r.status_code == 401:  # needs the session: login then retry
                from src.app.tutor_client import TutorClient

                tc = TutorClient()
                tc.login()
                r = tc.http.get(url)
            r.raise_for_status()
            rows = r.json().get("chunks") or []
            if rows:
                return Kb(rows, source="http")
    except Exception as exc:  # noqa: BLE001 — deliberate: ANY http failure
        http_error = exc  # degrades to the KB file (mcp_PLAN.md §2)
    try:
        return Kb(list(_file_chunks(str(s.kb_path))), source="file")
    except OSError as exc:
        why = f"type={type(http_error).__name__}" if http_error else "not attempted"
        raise KbUnavailable(
            f"KB unreachable: service at {s.tutor_base_url} ({why}) AND "
            f"KB_PATH {s.kb_path} unreadable ({exc})"
        ) from exc
