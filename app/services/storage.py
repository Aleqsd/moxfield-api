"""MongoDB persistence helpers."""

from __future__ import annotations

from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase

from ..config import get_settings
from ..schemas import UserDeckSummariesResponse, UserDecksResponse


async def upsert_user_decks(
    database: AsyncIOMotorDatabase, payload: UserDecksResponse
) -> None:
    """Persist the latest deck snapshot for a user."""
    settings = get_settings()
    users = database[settings.mongo_users_collection]
    decks = database[settings.mongo_decks_collection]

    synced_at = datetime.now(timezone.utc)
    user_doc = payload.user.model_dump(mode="python")
    user_doc["synced_at"] = synced_at
    user_doc["total_decks"] = payload.total_decks

    await users.update_one(
        {"user_name": payload.user.user_name},
        {"$set": user_doc},
        upsert=True,
    )

    for deck in payload.decks:
        deck_doc = deck.model_dump(mode="python")
        deck_doc["user_name"] = payload.user.user_name
        deck_doc["synced_at"] = synced_at

        await decks.update_one(
            {"public_id": deck.public_id, "user_name": payload.user.user_name},
            {"$set": deck_doc},
            upsert=True,
        )


async def upsert_user_deck_summaries(
    database: AsyncIOMotorDatabase, payload: UserDeckSummariesResponse
) -> None:
    """Persist the lighter deck summary snapshot for a user."""
    settings = get_settings()
    users = database[settings.mongo_users_collection]
    deck_summaries = database[settings.mongo_deck_summaries_collection]

    synced_at = datetime.now(timezone.utc)
    user_doc = payload.user.model_dump(mode="python")
    user_doc["synced_at"] = synced_at
    user_doc["total_decks"] = payload.total_decks

    await users.update_one(
        {"user_name": payload.user.user_name},
        {"$set": user_doc},
        upsert=True,
    )

    for deck in payload.decks:
        deck_doc = deck.model_dump(mode="python")
        deck_doc["user_name"] = payload.user.user_name
        deck_doc["synced_at"] = synced_at

        await deck_summaries.update_one(
            {"public_id": deck.public_id, "user_name": payload.user.user_name},
            {"$set": deck_doc},
            upsert=True,
        )
