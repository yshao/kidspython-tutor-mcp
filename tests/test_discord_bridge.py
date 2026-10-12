"""Discord bridge offline parts: reply chunking, thread mapping, and the
channel gate. The gateway itself is exercised only in deployment."""

import discord_bridge as bridge


def test_short_reply_passes_through():
    assert bridge.chunk_reply("A variable is a box with a name!") == [
        "A variable is a box with a name!"
    ]


def test_long_reply_splits_on_sentence_boundaries():
    reply = "First sentence stays whole. " * 60  # ~1600 chars
    reply += "Second long sentence also stays whole. " * 60
    parts = bridge.chunk_reply(reply)
    assert len(parts) >= 2
    assert all(len(p) <= bridge.DISCORD_LIMIT for p in parts)
    assert " ".join(parts).startswith("First sentence")


def test_pathological_text_hard_splits():
    parts = bridge.chunk_reply("a" * 4500)
    assert all(len(p) <= bridge.DISCORD_LIMIT for p in parts)
    assert "".join(parts) == "a" * 4500  # no content lost


def test_empty_reply_yields_no_messages():
    assert bridge.chunk_reply("   ") == []


def test_thread_id_maps_channel():
    assert bridge.thread_id_for(123456789) == "discord-123456789"


class _Msg:
    """duck-typed discord.Message for the gate test"""

    def __init__(self, channel_id, author_bot=False):
        self.channel = type("C", (), {"id": channel_id})()
        self.author = type("A", (), {"bot": author_bot})()


def _bridge(channel_id=42):
    import os

    os.environ["DISCORD_CHANNEL_ID"] = str(channel_id)
    b = bridge.Bridge.__new__(bridge.Bridge)  # no gateway login
    b.tutor = None
    b.channel_id = channel_id
    return b


def test_gate_allows_only_watched_channel_from_humans():
    b = _bridge(42)
    assert b._allowed(_Msg(42)) is True
    assert b._allowed(_Msg(43)) is False  # other channel
    assert b._allowed(_Msg(42, author_bot=True)) is False  # bots ignored
