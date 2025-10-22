"""Tests for MongoDB storage helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pytest

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.schemas import (
    DeckBoard,
    DeckCard,
    DeckDetail,
    DeckStats,
    DeckSummary,
    UserDeckSummariesResponse,
    UserDecksResponse,
    UserSummary,
)
from app.services.storage import upsert_user_deck_summaries, upsert_user_decks


@pytest.fixture()
def anyio_backend() -> str:
    """Force AnyIO tests to run against asyncio to avoid optional dependencies."""
    return "asyncio"


class _StubCollection:
    """Capture update operations to assert on them."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def update_one(self, *args: Any, **kwargs: Any) -> None:
        self.calls.append({"args": args, "kwargs": kwargs})


class _StubDatabase:
    """Dictionary-like helper that returns stub collections."""

    def __init__(self) -> None:
        self._collections: dict[str, _StubCollection] = {}

    def __getitem__(self, name: str) -> _StubCollection:
        if name not in self._collections:
            self._collections[name] = _StubCollection()
        return self._collections[name]


def _build_user_payload() -> UserSummary:
    return UserSummary(
        user_name="TestUser",
        display_name="Test User",
        profile_image_url="https://example.com/avatar.png",
        profile_url="https://moxfield.com/users/TestUser",
        badges=[],
    )


def _build_deck_detail() -> DeckDetail:
    board = DeckBoard(
        name="mainboard",
        cards=[DeckCard(quantity=1, card={"name": "Card A"})],
    )
    return DeckDetail(
        public_id="deck-public",
        name="Sample Deck",
        format="commander",
        public_url="https://moxfield.com/decks/deck-public",
        boards=[board],
        stats=DeckStats(),
        tokens=[],
    )


def _build_deck_summary() -> DeckSummary:
    return DeckSummary(
        public_id="deck-public",
        name="Sample Deck",
        format="commander",
        public_url="https://moxfield.com/decks/deck-public",
        stats=DeckStats(),
    )


@pytest.mark.anyio("asyncio")
async def test_upsert_user_decks_persists_user_and_decks() -> None:
    """Deck details should be upserted under the configured collections."""
    database = _StubDatabase()
    payload = UserDecksResponse(
        user=_build_user_payload(),
        total_decks=1,
        decks=[_build_deck_detail()],
    )

    await upsert_user_decks(database, payload)

    user_calls = database["users"].calls
    deck_calls = database["decks"].calls
    assert len(user_calls) == 1
    assert len(deck_calls) == 1

    user_filter, user_update = user_calls[0]["args"][:2]
    assert user_filter == {"user_name": "TestUser"}
    assert "$set" in user_update
    assert user_calls[0]["kwargs"]["upsert"] is True

    deck_filter, deck_update = deck_calls[0]["args"][:2]
    assert deck_filter == {"public_id": "deck-public", "user_name": "TestUser"}
    assert deck_calls[0]["kwargs"]["upsert"] is True
    assert isinstance(deck_update["$set"]["synced_at"], datetime)


@pytest.mark.anyio("asyncio")
async def test_upsert_user_deck_summaries_persists_user_and_summaries() -> None:
    """Deck summaries should be stored separately from full deck payloads."""
    database = _StubDatabase()
    payload = UserDeckSummariesResponse(
        user=_build_user_payload(),
        total_decks=1,
        decks=[_build_deck_summary()],
    )

    await upsert_user_deck_summaries(database, payload)

    user_calls = database["users"].calls
    summary_calls = database["deck_summaries"].calls
    assert len(user_calls) == 1
    assert len(summary_calls) == 1

    summary_filter, summary_update = summary_calls[0]["args"][:2]
    assert summary_filter == {"public_id": "deck-public", "user_name": "TestUser"}
    assert summary_calls[0]["kwargs"]["upsert"] is True
    assert isinstance(summary_update["$set"]["synced_at"], datetime)
