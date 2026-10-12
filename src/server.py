"""kidspython-tutor MCP server — FastMCP entry point (course PROJECT.md
layout). Registers the routers; runs on stdio by default."""

from __future__ import annotations

from fastmcp import FastMCP

from src.config.settings import settings
from src.routers import prompts, resources, tools


def create_server() -> FastMCP:
    s = settings()
    app: FastMCP = FastMCP(name=s.server_name, version=s.server_version)
    tools.register(app)
    resources.register(app)
    prompts.register(app)
    return app


def main() -> None:
    create_server().run()


if __name__ == "__main__":
    main()
