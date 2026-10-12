"""Structured outputs for every tool boundary (course custom feature:
Pydantic models, structured LLM/tool returns)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class KbHit(BaseModel):
    chunk_id: str
    doc: str
    title: str
    snippet: str
    score: float


class KbChunk(BaseModel):
    chunk_id: str
    doc: str
    title: str
    text: str
    anchors: dict[str, Any] = Field(default_factory=dict)


class OutlineEntry(BaseModel):
    doc: str
    title: str
    chunks: int
    exercise_ids: list[str] = Field(default_factory=list)


class TutorTurn(BaseModel):
    reply: str
    awaiting: str | None = None
    low_confidence: bool | None = None  # service sends null on flow turns
    refusal: str | None = None
    error: str | None = None
    tools: list[dict[str, Any]] = Field(default_factory=list)


class Hint(BaseModel):
    level: Literal["nudge", "hint", "path"]
    text: str = Field(description="guide-don't-solve: never the completed solution")
    grounded_in: list[str] = Field(
        default_factory=list, description="chunk_ids the hint draws on"
    )


class EvalScore(BaseModel):
    name: str
    value: float
    pass_threshold: float | None = None
    passed: bool | None = None
    comment: str | None = None


class SynthQuestion(BaseModel):
    question: str
    source_chunk_id: str
    kind: Literal["what", "why", "how", "exercise"]


class ScreeningOut(BaseModel):
    allowed: bool
    refusal: str | None = None
    notice: str | None = None
    scrubbed: list[str] = Field(default_factory=list)
    text: str = ""
