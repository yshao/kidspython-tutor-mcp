"""Resources router: MCP resources give clients context without a tool call
(course custom feature #2). Implementations live in src/resources/."""

from __future__ import annotations

import json

from fastmcp import FastMCP

from src.tools import tutor


def register(app: FastMCP) -> None:
    @app.resource("tutor://kb/outline")
    def kb_outline_uri() -> str:
        """Knowledge-base outline as context (docs, chapters, exercises)."""
        return json.dumps([e.model_dump() for e in tutor.kb_outline_impl()], indent=1)

    @app.resource("tutor://kb/chunks/{chunk_id}")
    def kb_chunk_uri(chunk_id: str) -> str:
        """One full knowledge-base chunk as context."""
        return tutor.kb_chunk_impl(chunk_id).model_dump_json(indent=1)
