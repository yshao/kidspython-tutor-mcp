"""guardrail_check tool: scope screening using the ported guard. Persona
data comes live from /personas when the tutor is up, else the bundled
kidspython default (guardrail_check stays offline-capable)."""

from __future__ import annotations

from src.app.guardrail import DEFAULT_PERSONA, screen
from src.app.models import ScreeningOut
from src.app.tutor_client import TutorUnavailable, shared_client


def guardrail_check_impl(question: str, persona_id: str | None = None) -> ScreeningOut:
    persona: dict | None = None
    if persona_id is not None:
        try:  # live persona config wins; offline default otherwise
            payload = shared_client().personas()
            match = next(
                (p for p in payload.get("personas", []) if p.get("id") == persona_id),
                None,
            )
            persona = match or None
        except TutorUnavailable:
            persona = None
    s = screen(
        question,
        persona=persona
        or (DEFAULT_PERSONA if persona_id in (None, DEFAULT_PERSONA["id"]) else None),
    )
    return ScreeningOut(
        allowed=s.allowed,
        refusal=s.refusal,
        notice=s.notice,
        scrubbed=s.scrubbed,
        text=s.text,
    )
