"""Tests for the user decks endpoint."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_mongo_database, get_moxfield_client
from app.main import create_app
from app.moxfield import MoxfieldError, MoxfieldNotFoundError


class _StubMoxfieldClient:
    """Simple stub that mimics the Moxfield client behaviour."""

    def __init__(
        self,
        payload: Dict[str, Any] | None = None,
        *,
        error: Exception | None = None,
        summary_payload: Dict[str, Any] | None = None,
        deck_summaries: List[Dict[str, Any]] | None = None,
    ) -> None:
        self._payload = payload
        self._error = error
        self._summary_payload = summary_payload or {}
        self._deck_summaries = list(deck_summaries or [])

    def collect_user_decks_with_details(self, username: str, **_: Any) -> Dict[str, Any]:
        if self._error:
            raise self._error
        return self._payload or {}

    def get_user_summary(self, username: str, **_: Any) -> Dict[str, Any]:
        if self._error:
            raise self._error
        if self._summary_payload:
            return self._summary_payload
        return {
            "userName": username,
            "displayName": username,
            "profileImageUrl": None,
            "badges": [],
        }

    def get_user_deck_summaries(self, username: str, **_: Any) -> List[Dict[str, Any]]:
        if self._error:
            raise self._error
        return self._deck_summaries


class _StubCollection:
    """Capture update operations without touching a real database."""

    def __init__(self) -> None:
        self.calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    async def update_one(self, *args: Any, **kwargs: Any) -> None:
        self.calls.append((args, kwargs))


class _StubDatabase:
    """Dictionary-like helper that returns stub collections."""

    def __init__(self) -> None:
        self._collections = {
            "users": _StubCollection(),
            "decks": _StubCollection(),
            "deck_summaries": _StubCollection(),
        }

    def __getitem__(self, name: str) -> _StubCollection:
        if name not in self._collections:
            self._collections[name] = _StubCollection()
        return self._collections[name]


@pytest.fixture()
def api_client() -> TestClient:
    """Provide a FastAPI TestClient with dependency overrides reset after use."""
    app = create_app()
    stub_db = _StubDatabase()
    app.dependency_overrides[get_mongo_database] = lambda: stub_db
    app.state.stub_db = stub_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_get_user_decks_success(api_client: TestClient) -> None:
    """The endpoint should return a normalized response when the client succeeds."""
    stub_payload = {
        "user": {
            "userName": "TestUser",
            "displayName": "Test User",
            "profileImageUrl": "https://example.com/avatar.png",
            "badges": [{"name": "Badge"}],
        },
        "decks": [
            {
                "id": "deck123",
                "publicId": "deck-public",
                "name": "Sample Deck",
                "format": "commander",
                "visibility": "public",
                "description": "Example deck description.",
                "publicUrl": "https://moxfield.com/decks/deck-public",
                "createdAtUtc": "2024-01-01T00:00:00Z",
                "lastUpdatedAtUtc": "2024-01-02T00:00:00Z",
                "likeCount": 10,
                "viewCount": 20,
                "commentCount": 5,
                "bookmarkCount": 3,
                "createdByUser": {
                    "userName": "Author",
                    "displayName": "Deck Author",
                    "profileImageUrl": "https://example.com/author.png",
                },
                "authors": [
                    {
                        "userName": "Author",
                        "displayName": "Deck Author",
                        "profileImageUrl": "https://example.com/author.png",
                    }
                ],
                "authorTags": {"Card A": ["Tag 1", "Tag 2"]},
                "hubs": [{"name": "Hub One"}],
                "colors": ["G"],
                "colorIdentity": ["G"],
                "boards": {
                    "mainboard": {
                        "count": 1,
                        "cards": {
                            "card-1": {
                                "quantity": 1,
                                "finish": "nonFoil",
                                "isFoil": False,
                                "isAlter": False,
                                "isProxy": False,
                                "card": {"name": "Card A"},
                            }
                        },
                    }
                },
                "tokens": [],
            }
        ],
    }

    stub_client = _StubMoxfieldClient(stub_payload)

    app = api_client.app
    app.dependency_overrides[get_moxfield_client] = lambda: stub_client

    response = api_client.get("/users/TestUser/decks")

    assert response.status_code == 200
    body = response.json()
    assert body["user"]["user_name"] == "TestUser"
    assert body["total_decks"] == 1
    assert body["decks"][0]["public_id"] == "deck-public"
    assert body["decks"][0]["boards"][0]["cards"][0]["card"]["name"] == "Card A"
    assert body["decks"][0]["tags"][0]["tags"] == ["Tag 1", "Tag 2"]


def test_get_user_decks_not_found(api_client: TestClient) -> None:
    """The endpoint should convert client not-found errors into HTTP 404."""
    stub_client = _StubMoxfieldClient(error=MoxfieldNotFoundError("missing"))

    app = api_client.app
    app.dependency_overrides[get_moxfield_client] = lambda: stub_client

    response = api_client.get("/users/Unknown/decks")

    assert response.status_code == 404
    assert response.json()["detail"] == "missing"


def test_get_user_decks_generic_error(api_client: TestClient) -> None:
    """Any other client error should surface as a 502."""
    stub_client = _StubMoxfieldClient(error=MoxfieldError("boom"))

    app = api_client.app
    app.dependency_overrides[get_moxfield_client] = lambda: stub_client

    response = api_client.get("/users/Test/decks")

    assert response.status_code == 502
    assert response.json()["detail"] == "boom"


def test_get_user_deck_summaries_success(api_client: TestClient) -> None:
    """Deck summaries endpoint should omit card payloads while returning metadata."""
    stub_summary = {
        "userName": "TestUser",
        "displayName": "Test User",
        "profileImageUrl": "https://example.com/avatar.png",
        "badges": [],
    }
    stub_decks = [
        {
            "id": "deck123",
            "publicId": "deck-public",
            "name": "Sample Deck",
            "format": "commander",
            "visibility": "public",
            "description": "Example deck description.",
            "publicUrl": "https://moxfield.com/decks/deck-public",
            "createdAtUtc": "2024-01-01T00:00:00Z",
            "lastUpdatedAtUtc": "2024-01-02T00:00:00Z",
            "likeCount": 10,
            "viewCount": 20,
            "commentCount": 5,
            "bookmarkCount": 3,
            "colors": ["G"],
            "colorIdentity": ["G"],
            "hubs": [{"name": "Hub One"}],
        }
    ]

    stub_client = _StubMoxfieldClient(summary_payload=stub_summary, deck_summaries=stub_decks)

    app = api_client.app
    app.dependency_overrides[get_moxfield_client] = lambda: stub_client

    response = api_client.get("/users/TestUser/deck-summaries")

    assert response.status_code == 200
    body = response.json()
    assert body["user"]["user_name"] == "TestUser"
    assert body["total_decks"] == 1
    deck = body["decks"][0]
    assert deck["public_id"] == "deck-public"
    assert "boards" not in deck


def test_get_user_deck_summaries_not_found(api_client: TestClient) -> None:
    """Not found errors should surface as HTTP 404 for summaries."""
    stub_client = _StubMoxfieldClient(error=MoxfieldNotFoundError("missing"))

    app = api_client.app
    app.dependency_overrides[get_moxfield_client] = lambda: stub_client

    response = api_client.get("/users/Unknown/deck-summaries")

    assert response.status_code == 404
    assert response.json()["detail"] == "missing"


def test_get_user_deck_summaries_generic_error(api_client: TestClient) -> None:
    """Any other client error should surface as a 502 for summaries."""
    stub_client = _StubMoxfieldClient(error=MoxfieldError("boom"))

    app = api_client.app
    app.dependency_overrides[get_moxfield_client] = lambda: stub_client

    response = api_client.get("/users/Test/deck-summaries")

    assert response.status_code == 502
    assert response.json()["detail"] == "boom"
