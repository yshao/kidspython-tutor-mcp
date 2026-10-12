"""Server contract: the fastmcp in-memory client lists the registered
surface and kb tools run through the full MCP stack (KB_PATH pointed at the
synthetic fixtures — no service, no licensed data)."""

import pathlib

import pytest
from fastmcp import Client

from src.server import create_server

FIX = pathlib.Path(__file__).parent / "fixtures" / "chunks.jsonl"


@pytest.fixture
def kb_env(monkeypatch):
    monkeypatch.setenv("KB_PATH", str(FIX))
    from src.config.settings import settings as get_settings

    s = get_settings()  # lru_cached singleton — the same one server/tools use
    s.kb_path = FIX
    s.tutor_base_url = "http://127.0.0.1:1"  # nothing there: degradation path
    kb_app = __import__("src.app.kb", fromlist=["_file_chunks"])
    kb_app._file_chunks.cache_clear()
    return s


@pytest.mark.asyncio
async def test_surface_lists_tools_resources_prompts(kb_env):
    app = create_server()
    async with Client(app) as client:
        tools = {t.name for t in (await client.list_tools())}
        assert {"tutor_ask", "kb_search", "kb_chunk", "kb_outline"} <= tools
        resources = [str(r.uri) for r in (await client.list_resources())]
        assert "tutor://kb/outline" in resources
        prompts = [p.name for p in (await client.list_prompts())]
        assert "tutor_lesson" in prompts


@pytest.mark.asyncio
async def test_kb_search_through_mcp(kb_env):
    app = create_server()
    async with Client(app) as client:
        res = await client.call_tool("kb_search", {"query": "for loop range"})
        ids = [h["chunk_id"] for h in res.data]
        assert any("chapter-5-loops" in i for i in ids)


@pytest.mark.asyncio
async def test_tutor_ask_down_service_is_structured_not_crash(kb_env):
    from fastmcp.exceptions import ToolError

    app = create_server()
    async with Client(app) as client:
        # dead service → ToolError carrying TutorUnavailable's message;
        # the contract is: structured error, never a hang or hard crash
        with pytest.raises(ToolError, match="unreachable"):
            await client.call_tool(
                "tutor_ask", {"message": "hi", "thread_id": "dead-thread"}
            )
