"""HTTP client for the live tutor service — the service's real contract
(service/app.py): cookie login (in-memory sessions, 12h TTL server-side),
POST /chat, GET /kb/{ds}/{ver}/chunks, GET /runs/{thread_id}, GET /healthz.
Re-logins transparently when the service drops the session (redirect to
/login). All failures surface as TutorUnavailable — the MCP boundary never
500s on a dead service."""

from __future__ import annotations

from functools import lru_cache

import httpx

from src.config.settings import settings


class TutorUnavailable(RuntimeError):
    """The tutor service is unreachable or refused login."""


class TutorClient:
    """One client per long-running server process; login is lazy."""

    def __init__(self, base_url: str | None = None):
        s = settings()
        self.http = httpx.Client(
            base_url=base_url or s.tutor_base_url,
            timeout=s.tutor_timeout_s,
            follow_redirects=False,
        )

    def login(self) -> None:
        s = settings()
        try:
            r = self.http.post(
                "/login", data={"username": s.tutor_user, "password": s.tutor_pass}
            )
        except httpx.HTTPError as exc:
            raise TutorUnavailable(
                f"tutor service unreachable at {self.http.base_url}: "
                f"{type(exc).__name__}"
            ) from exc
        if r.status_code != 302 or "tutor_session" not in r.headers.get(
            "set-cookie", ""
        ):
            raise TutorUnavailable(
                f"tutor login failed (HTTP {r.status_code}) — check "
                "TUTOR_USER/TUTOR_PASS"
            )

    def _get(self, path: str, **kwargs) -> httpx.Response:
        r = self.http.get(path, **kwargs)
        if r.status_code == 302 and "/login" in r.headers.get("location", ""):
            self.login()  # session expired (12h TTL) — mint a new one
            r = self.http.get(path, **kwargs)
        return r

    def health(self) -> dict:
        try:
            r = self.http.get("/healthz")
            r.raise_for_status()
            return r.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise TutorUnavailable(
                f"tutor service unreachable at {self.http.base_url}: "
                f"{type(exc).__name__}"
            ) from exc

    def chat(self, thread_id: str, message: str, persona: str | None = None) -> dict:
        if "tutor_session" not in self.http.cookies:
            self.login()
        payload = {"thread_id": thread_id, "message": message, "persona": persona}
        try:
            r = self.http.post("/chat", json=payload)
        except httpx.HTTPError as exc:
            raise TutorUnavailable(
                f"tutor service unreachable at {self.http.base_url}: "
                f"{type(exc).__name__}"
            ) from exc
        if r.status_code == 302:  # session dropped mid-flight
            self.login()
            r = self.http.post("/chat", json=payload)
        r.raise_for_status()
        return r.json()

    def runs(self, thread_id: str) -> dict | None:
        if "tutor_session" not in self.http.cookies:
            self.login()
        r = self._get(f"/runs/{thread_id}")
        return r.json() if r.status_code == 200 else None

    def personas(self) -> dict:
        if "tutor_session" not in self.http.cookies:
            self.login()
        r = self._get("/personas")
        r.raise_for_status()
        return r.json()


@lru_cache(maxsize=1)
def shared_client() -> TutorClient:
    """The long-lived client (cookie jar survives across tool calls)."""
    return TutorClient()
