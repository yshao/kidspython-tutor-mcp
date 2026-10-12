"""Guardrail port parity: the MCP copy must behave exactly like the service
guard on the inputs that matter — allowlist pass, out-of-scope refusal with
the escalation template, PII scrub + notice, plural tolerance."""

from src.app.guardrail import DEFAULT_PERSONA, screen
from src.tools.guardrail import guardrail_check_impl


def test_in_scope_question_allowed():
    s = screen("What is a variable?")
    assert s.allowed and s.refusal is None


def test_out_of_scope_refused_with_template():
    s = screen("What is the capital of France?")
    assert not s.allowed
    assert "outside what we're learning" in s.refusal
    assert DEFAULT_PERSONA["escalation"] in s.refusal


def test_pii_scrubbed_with_notice():
    s = screen("I am 9 years old and my email is kid@example.com. What is a list?")
    assert s.allowed  # 'list' is in scope
    assert "[removed]" in s.text
    assert any("@" in x or "9" in x for x in s.scrubbed)
    assert s.notice and "stick to Python" in s.notice


def test_plural_tolerance():
    assert screen("How do variables work in Python?").allowed
    assert screen("Tell me about loops").allowed


def test_out_of_scope_beyond_python_refused():
    assert not screen("How do I hack a game?").allowed


def test_guard_from_dict_overrides():
    pro = {
        "audience_class": "professional",
        "scope_terms": ["guideline"],
        "escalation": "see your care team",
    }
    s = screen("What is the dose?", persona=pro)
    assert not s.allowed and "guideline scope" in s.refusal


def test_tool_impl_offline_default():
    out = guardrail_check_impl("What is a for loop?")
    assert out.allowed
    out = guardrail_check_impl("Who is the president?")
    assert not out.allowed and out.refusal
