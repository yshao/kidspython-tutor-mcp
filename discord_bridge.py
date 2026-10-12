#!/usr/bin/env python3
"""Discord bridge: #chat-kidspython <-> the kidspython-tutor chatbot.

One tutor thread per Discord channel (discord-<channel_id>); the tutor's
flow pins the persona and carries conversation state, so the channel holds
a continuous tutoring conversation. Runs beside the tutor service on the
droplet (Discord's gateway is an outbound websocket — no inbound ports).
Env (see discord-bridge.env): DISCORD_BOT_TOKEN, DISCORD_CHANNEL_ID,
TUTOR_BASE_URL, TUTOR_USER, TUTOR_PASS.
"""

from __future__ import annotations

import asyncio
import logging
import os

import discord
import httpx

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("discord-bridge")

DISCORD_LIMIT = 2000


def chunk_reply(text: str, limit: int = DISCORD_LIMIT) -> list[str]:
    """Split a tutor reply into Discord-sized messages on sentence
    boundaries; hard-split only as the last resort."""
    text = text.strip()
    if len(text) <= limit:
        return [text] if text else []
    parts: list[str] = []
    while len(text) > limit:
        window = text[:limit]
        cut = max(window.rfind(". "), window.rfind("! "), window.rfind("? "),
                  window.rfind("\n"))
        if cut < limit // 2:  # no sane boundary in the window: hard split
            cut = limit - 1
        parts.append(text[: cut + 1].strip())
        text = text[cut + 1:].strip()
    if text:
        parts.append(text)
    return parts


def thread_id_for(channel_id: int) -> str:
    return f"discord-{channel_id}"


class TutorClient:
    """Portal cookie flow: login once, re-login when the session drops
    (the service holds sessions in memory, 12h TTL)."""

    def __init__(self):
        self.base = os.environ.get("TUTOR_BASE_URL", "http://127.0.0.1:8100")
        self.user = os.environ.get("TUTOR_USER", "demo")
        self.password = os.environ.get("TUTOR_PASS", "12345")
        self.http = httpx.Client(base_url=self.base, timeout=120.0,
                                 follow_redirects=False)

    def login(self) -> None:
        r = self.http.post("/login", data={"username": self.user,
                                           "password": self.password})
        if r.status_code != 302 or "tutor_session" not in r.headers.get(
                "set-cookie", ""):
            raise RuntimeError(f"tutor login failed (HTTP {r.status_code})")

    def ask(self, thread_id: str, message: str) -> str:
        if "tutor_session" not in self.http.cookies:
            self.login()
        payload = {"thread_id": thread_id, "message": message,
                   "persona": "kidspython-tutor"}
        r = self.http.post("/chat", json=payload)
        if r.status_code == 302:  # session dropped mid-flight
            self.login()
            r = self.http.post("/chat", json=payload)
        r.raise_for_status()
        data = r.json()
        if data.get("error"):
            return ("Hmm — I hit a backend problem. "
                    "Ask me again in a moment!")
        return str(data.get("reply") or "…")


class Bridge(discord.Client):
    def __init__(self, tutor: TutorClient):
        intents = discord.Intents.default()
        intents.message_content = True  # privileged: enable in the dev portal
        super().__init__(intents=intents)
        self.tutor = tutor
        self.channel_id = int(os.environ["DISCORD_CHANNEL_ID"])

    async def on_ready(self):
        log.info("gateway READY as %s — watching channel %s",
                 self.user, self.channel_id)

    def _allowed(self, message: discord.Message) -> bool:
        return (message.channel.id == self.channel_id
                and not message.author.bot)

    async def on_message(self, message: discord.Message):
        if not self._allowed(message):
            return
        log.info("msg from %s: %.80s", message.author, message.content)
        async with message.channel.typing():
            try:
                reply = await asyncio.to_thread(
                    self.tutor.ask, thread_id_for(self.channel_id),
                    message.content)
            except Exception as exc:  # noqa: BLE001 — the bridge answers
                # the channel even when a turn fails; never crash the gateway
                log.error("tutor turn failed: %s: %.120s",
                          type(exc).__name__, exc)
                reply = ("Hmm — I hit a backend problem. "
                         "Ask me again in a moment!")
            for part in chunk_reply(reply):
                await message.channel.send(part)


def main() -> None:
    token = os.environ.get("DISCORD_BOT_TOKEN")
    if not token:
        raise SystemExit("DISCORD_BOT_TOKEN not set — see discord-bridge.env")
    Bridge(TutorClient()).run(token)


if __name__ == "__main__":
    main()
