"""Offline KB engine: search/outline/chunk on the synthetic fixture KB —
no service, no real licensed data (fixtures only, mirroring the chatbot's
fixture pattern)."""

import pathlib

import pytest

from src.app import kb as kb_app
from src.config.settings import Settings

FIX = pathlib.Path(__file__).parent / "fixtures" / "chunks.jsonl"


@pytest.fixture
def kb() -> kb_app.Kb:
    return kb_app.Kb(kb_app._load_file(FIX), source="file")


def test_search_ranks_loop_query_to_loop_chunks(kb):
    hits = kb.search("for loop range", limit=5)
    assert hits, "loop query must hit"
    assert all(
        "loop" in h["chunk_id"]
        or "range" in h["text"].lower()
        or "loop" in h["text"].lower()
        for h in hits[:2]
    )
    assert hits[0]["score"] >= hits[-1]["score"]


def test_search_stopwords_do_not_match_everything(kb):
    # 'what is a' is all stopwords — zero terms → zero hits, not rank-noise
    assert kb.search("what is a") == []


def test_doc_narrows_the_pool(kb):
    # 'assignment' appears in exactly one variables chunk — idf > 0 there
    hits = kb.search("assignment operator", doc="/courses/chapter-3-variables")
    assert [h["chunk_id"] for h in hits] == ["/courses/chapter-3-variables#001"]
    # a term in EVERY pool chunk has idf 0 → correctly no hits (ported
    # service semantics, knowledge.py search())
    assert kb.search("variable", doc="/courses/chapter-3-variables") == []


def test_search_across_pool_ignores_universal_terms(kb):
    hits = kb.search("numbers", limit=5)
    assert "/courses/chapter-3-variables#001" in {h["chunk_id"] for h in hits}


def test_chunk_and_outline(kb):
    c = kb.chunk("/courses/chapter-5-loops#002")
    assert c["title"] == "For loops" and "range(5)" in c["text"]
    assert kb.chunk("/nope#999") is None
    outline = kb.outline()
    by_doc = {e["doc"]: e for e in outline}
    assert by_doc["/courses/chapter-5-loops"]["chunks"] == 2
    assert by_doc["/courses/chapter-3-variables"]["exercise_ids"] == ["variables-quiz"]


def test_load_file_parses_all_lines():
    rows = kb_app._load_file(FIX)
    assert len(rows) == 6 and rows[0]["chunk_id"] == "/courses#001"


def test_settings_defaults_are_offline_safe(tmp_path, monkeypatch):
    monkeypatch.setenv("KB_PATH", str(FIX))
    Settings.model_rebuild()
    s = Settings(kb_path=FIX, store_path=tmp_path / "s.sqlite")
    rows = kb_app._load_file(s.kb_path)
    assert rows and s.tutor_base_url.startswith("http")
