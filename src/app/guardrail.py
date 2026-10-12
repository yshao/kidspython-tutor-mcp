"""Port of the chatbot's scope guard — service/services/guarding.py
(verbatim semantics, 2026-10-12): deterministic allowlist gate + PII scrub +
audience profiles. Pure stdlib so the MCP server needs no service to screen
text. The ONE change vs the source: the persona inputs (scope_terms,
escalation, audience_class) arrive as plain data — from the live /personas
endpoint when the tutor is up, else DEFAULT below (kidspython-tutor's
published config). Parity tests: tests/test_guardrail.py."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field

ESCALATION = "ask your teacher or a parent"
PII_NOTICE = "you don't need to tell me that — let's stick to Python"

# ponytail: regex heuristics for kid PII; extend as real traffic shows gaps.
PII_PATTERNS = [
    re.compile(
        r"\b(?:i'?m|i am|age(?:\s+is)?|aged)\s*\d{1,2}\b"
        r"|\b\d{1,2}\s*(?:years?\s+old|yo)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),
    re.compile(r"\b(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b"),
    re.compile(
        r"\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?\s+(?:Elementary|Middle|High)(?:\s+School)?\b"
    ),
]


@dataclass
class Screening:
    """Result of screening one inbound student message."""

    allowed: bool
    text: str  # PII-scrubbed text, what downstream layers see
    refusal: str | None = None
    notice: str | None = None
    scrubbed: list[str] = field(default_factory=list)


def scrub_pii(text: str) -> tuple[str, list[str]]:
    """Replace deterministic PII matches with [removed]; never persisted."""
    scrubbed: list[str] = []
    for pattern in PII_PATTERNS:
        scrubbed.extend(pattern.findall(text))  # no capture groups: full matches
        text = pattern.sub("[removed]", text)
    return text, scrubbed


@dataclass(frozen=True)
class AudienceProfile:
    """Guard profile keyed by persona audience_class (ingestion_PLAN §6).

    Templates and scope_terms come from persona DATA; the profile supplies
    only the audience phrasing — kids vs professional refusal text, whether
    the PII scrub applies, and the respond-time style directives the
    persona's tone must satisfy.
    """

    audience_class: str
    scrub_pii: bool
    refusal: str  # template over {escalation} and {lesson}
    style: tuple[str, ...]  # respond-time directives (persona tone rules)


# §6: exactly two guard profiles — code, not data.
KIDS_PROFILE = AudienceProfile(
    audience_class="kids",
    scrub_pii=True,
    refusal=(
        "That's outside what we're learning right now — {escalation}. "
        "Want to keep going with {lesson}?"
    ),
    style=(
        "simple words",
        "guide-don't-solve: give the next hint, never the completed solution",
    ),
)
PROFESSIONAL_PROFILE = AudienceProfile(
    audience_class="professional",
    scrub_pii=False,  # adults may identify themselves; the kid scrub is kid-only
    refusal=(
        "That request falls outside this navigator's guideline scope — "
        "no dosing or diagnostic output; {escalation}."
    ),
    style=("citation-first terseness", "no-dosing, no-diagnostic framing"),
)
AUDIENCE_PROFILES = {"kids": KIDS_PROFILE, "professional": PROFESSIONAL_PROFILE}


def guard_for(persona, current_lesson: str) -> ScopeGuard:
    """ScopeGuard from persona data: scope_terms + escalation + the
    audience_class profile (§6 — personas are data, the guard is code)."""
    return ScopeGuard(
        persona.scope_terms,
        current_lesson,
        escalation=persona.escalation,
        profile=AUDIENCE_PROFILES[persona.audience_class],
    )


class ScopeGuard:
    """Keyword allowlist gate over the current lesson's scope."""

    def __init__(
        self,
        allowlist: Iterable[str],
        current_lesson: str,
        escalation: str = ESCALATION,
        profile: AudienceProfile = KIDS_PROFILE,
    ):
        self._keywords = [kw.lower() for kw in allowlist]
        self._current_lesson = current_lesson
        self._escalation = escalation
        self._profile = profile

    def screen(self, text: str, enforce_scope: bool = True) -> Screening:
        if self._profile.scrub_pii:
            cleaned, scrubbed = scrub_pii(text)
        else:
            cleaned, scrubbed = text, []
        if enforce_scope and not self._in_scope(cleaned):
            return Screening(
                allowed=False,
                text=cleaned,
                refusal=self._profile.refusal.format(
                    escalation=self._escalation, lesson=self._current_lesson
                ),
                scrubbed=scrubbed,
            )
        return Screening(
            allowed=True,
            text=cleaned,
            notice=PII_NOTICE if scrubbed else None,
            scrubbed=scrubbed,
        )

    def _in_scope(self, text: str) -> bool:
        # prefix-bound only: "token" must match "tokens"/"tokenizer" — an
        # allowlist gate should over-accept derivatives, never reject plurals
        def _hit(kw):
            if re.search(rf"\b{re.escape(kw)}", text, re.IGNORECASE):
                return True
            # text-side plural tolerance: keyword "lists" must match "list"
            return bool(
                kw.endswith("s")
                and re.search(rf"\b{re.escape(kw[:-1])}(?:s\b|$)", text, re.IGNORECASE)
            )

        return any(_hit(kw) for kw in self._keywords)


# ---------------------------------------------------------------------------
# MCP adapter: persona-as-data + offline default (kidspython-tutor's public
# config — personas/kidspython-tutor.json). The live /personas endpoint
# overrides these when the tutor service is reachable.

DEFAULT_PERSONA = {
    "id": "kidspython-tutor",
    "audience_class": "kids",
    "scope_terms": [
        "print",
        "variable",
        "string",
        "number",
        "integer",
        "boolean",
        "condition",
        "logical operator",
        "loop",
        "for loop",
        "while loop",
        "function",
        "list",
        "dictionary",
        "index",
        "slice",
        "input",
        "output",
        "operator",
        "method",
        "concatenation",
        "data type",
        "comment",
        "error",
        "syntax",
        "exercise",
        "playground",
        "chapter",
        "code",
        "python",
    ],
    "escalation": "ask your teacher or a parent",
}


def guard_from_dict(persona: dict, current_lesson: str = "Python") -> ScopeGuard:
    """ScopeGuard from a persona dict (/personas payload or DEFAULT_PERSONA)."""
    return ScopeGuard(
        persona.get("scope_terms") or DEFAULT_PERSONA["scope_terms"],
        current_lesson,
        escalation=persona.get("escalation") or DEFAULT_PERSONA["escalation"],
        profile=AUDIENCE_PROFILES[
            persona.get("audience_class") or DEFAULT_PERSONA["audience_class"]
        ],
    )


def screen(
    text: str, persona: dict | None = None, current_lesson: str = "Python"
) -> Screening:
    """Screen one message with the ported guard (offline-capable)."""
    return guard_from_dict(persona or DEFAULT_PERSONA, current_lesson).screen(text)
