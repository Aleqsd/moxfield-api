"""Runtime configuration helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    """Application settings sourced from environment variables."""

    mongo_uri: str
    mongo_db: str
    mongo_users_collection: str
    mongo_decks_collection: str
    mongo_deck_summaries_collection: str

    @classmethod
    def from_env(cls) -> "Settings":
        """Construct settings using environment variables with sane defaults."""
        return cls(
            mongo_uri=os.getenv("MONGO_URI", "mongodb://localhost:27017"),
            mongo_db=os.getenv("MONGO_DB_NAME", "moxfield"),
            mongo_users_collection=os.getenv("MONGO_USERS_COLLECTION", "users"),
            mongo_decks_collection=os.getenv("MONGO_DECKS_COLLECTION", "decks"),
            mongo_deck_summaries_collection=os.getenv(
                "MONGO_DECK_SUMMARIES_COLLECTION", "deck_summaries"
            ),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings.from_env()

