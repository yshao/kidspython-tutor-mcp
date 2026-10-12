"""Tutor HTTP client against a mocked service (respx): login cookie flow,
chat pass-through, session re-login, and TutorUnavailable on a dead service.
The 302+Set-Cookie shape mirrors service/app.py's login."""

import httpx
import pytest
import respx

from src.app.tutor_client import TutorClient, TutorUnavailable

LOGIN = {"set-cookie": "tutor_session=abc123; Path=/; HttpOnly"}


def _client() -> TutorClient:
    return TutorClient(base_url="http://tutor.test")


@respx.mock
def test_login_sets_cookie_and_chat_returns_result():
    respx.post("http://tutor.test/login").mock(
        return_value=httpx.Response(302, headers=LOGIN)
    )
    respx.post("http://tutor.test/chat").mock(
        return_value=httpx.Response(
            200,
            json={
                "reply": "A variable is a box with a name!",
                "awaiting": None,
                "low_confidence": False,
                "tools": [{"name": "llm"}],
            },
        )
    )
    tc = _client()
    turn = tc.chat("t-1", "What is a variable?")
    assert turn["reply"].startswith("A variable")
    assert "tutor_session" in tc.http.cookies


@respx.mock
def test_expired_session_relogins_once():
    route = respx.post("http://tutor.test/chat")
    route.side_effect = [
        httpx.Response(302, headers={"location": "/login"}),
        httpx.Response(
            200,
            json={
                "reply": "ok",
                "awaiting": None,
                "low_confidence": False,
                "tools": [],
            },
        ),
    ]
    respx.post("http://tutor.test/login").mock(
        return_value=httpx.Response(302, headers=LOGIN)
    )
    tc = _client()
    tc.login()
    assert tc.chat("t-1", "hi")["reply"] == "ok"


@respx.mock
def test_dead_service_raises_tutor_unavailable():
    respx.post("http://tutor.test/login").mock(
        side_effect=httpx.ConnectError("refused")
    )
    with pytest.raises(TutorUnavailable, match="unreachable"):
        _client().login()


@respx.mock
def test_degrade_path_returns_error_field_not_exception():
    respx.post("http://tutor.test/login").mock(
        return_value=httpx.Response(302, headers=LOGIN)
    )
    respx.post("http://tutor.test/chat").mock(
        return_value=httpx.Response(
            200,
            json={
                "reply": "Setup mode — the tutor runs without its language model.",
                "error": "RuntimeError: no LLM provider",
            },
        )
    )
    turn = _client().chat("t-1", "hi")
    assert turn["error"] and "no LLM provider" in turn["error"]
