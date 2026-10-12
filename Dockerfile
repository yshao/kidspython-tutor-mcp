# kidspython-tutor MCP server — stdio MCP over a uv-managed py3.14 env.
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# deps first: the lockfile layer caches independently of source changes
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src
COPY client_demo.py README.md ./
RUN uv sync --frozen --no-dev

RUN useradd -m tutor && chown -R tutor /app
USER tutor

# MCP stdio: docker run -i (compose wires it); data/ volume holds student memory
ENTRYPOINT ["uv", "run", "--no-dev", "kidspython-tutor-mcp"]
