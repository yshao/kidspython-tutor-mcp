"""Eval plumbing that runs without keys/network: the fence-tolerant JSON
parser (ported from the chatbot's eval runner) and the registry loader."""

import pytest

from src.app import llm
from src.tools.eval import _registry, grade_reply_impl


def test_parse_json_plain_fenced_and_pythonic():
    assert llm.parse_json('{"a": 1}') == {"a": 1}
    assert llm.parse_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert llm.parse_json("{'a': 1,}") == {"a": 1}  # single quotes + comma
    assert llm.parse_json('sure! {"a": 1} hope that helps') == {"a": 1}


def test_registry_loads_with_thresholds():
    reg = _registry()
    names = {m["name"] for m in reg["metrics"]}
    assert "ragas_faithfulness" in names and "deepeval_directness" in names
    assert reg["dataset"] == "kidspython-eval"


def test_grade_reply_rejects_unknown_metric():
    with pytest.raises(ValueError, match="unknown judge metric"):
        grade_reply_impl("q", "a", metric="not_a_metric")


def test_grade_reply_without_key_degrades():
    from src.app.llm import LlmUnavailable
    from src.config.settings import llm_settings

    if llm_settings().zai_api_key:
        pytest.skip("key configured — degradation path not exercised")
    with pytest.raises(LlmUnavailable, match="ZAI_API_KEY"):
        grade_reply_impl("q", "a")
