"""Pydantic schemas that describe the API responses."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class Author(BaseModel):
    """Basic information about a Moxfield user."""

    model_config = ConfigDict(extra="forbid")

    user_name: str
    display_name: Optional[str] = None
    profile_image_url: Optional[str] = None


class DeckStats(BaseModel):
    """Aggregate deck statistics."""

    model_config = ConfigDict(extra="forbid")

    like_count: int = 0
    view_count: int = 0
    comment_count: int = 0
    bookmark_count: int = 0


class DeckCard(BaseModel):
    """A single card entry within a board."""

    model_config = ConfigDict(extra="forbid")

    quantity: int
    finish: Optional[str] = None
    is_foil: Optional[bool] = None
    is_alter: Optional[bool] = None
    is_proxy: Optional[bool] = None
    card: Dict[str, Any] = Field(default_factory=dict)


class DeckBoard(BaseModel):
    """A board (mainboard, sideboard, commanders, etc.) within a deck."""

    model_config = ConfigDict(extra="forbid")

    name: str
    count: Optional[int] = None
    cards: List[DeckCard] = Field(default_factory=list)


class DeckTag(BaseModel):
    """Tags assigned by the deck author to individual cards."""

    model_config = ConfigDict(extra="forbid")

    card_name: str
    tags: List[str] = Field(default_factory=list)


class UserSummary(BaseModel):
    """Top-level user descriptor returned by the API."""

    model_config = ConfigDict(extra="forbid")

    user_name: str
    display_name: Optional[str] = None
    profile_image_url: Optional[str] = None
    profile_url: Optional[str] = None
    badges: List[Dict[str, Any]] = Field(default_factory=list)


class DeckSummary(BaseModel):
    """Lightweight deck metadata that excludes card lists."""

    model_config = ConfigDict(extra="forbid")

    id: Optional[str] = None
    public_id: str
    name: str
    format: str
    public_url: Optional[str] = None
    visibility: Optional[str] = None
    description: Optional[str] = ""
    created_at: Optional[datetime] = None
    last_updated_at: Optional[datetime] = None
    stats: DeckStats = Field(default_factory=DeckStats)
    created_by: Optional[Author] = None
    authors: List[Author] = Field(default_factory=list)
    tags: List[DeckTag] = Field(default_factory=list)
    hubs: List[str] = Field(default_factory=list)
    colors: List[str] = Field(default_factory=list)
    color_identity: List[str] = Field(default_factory=list)


class DeckDetail(BaseModel):
    """Full deck details including card breakdown."""

    model_config = ConfigDict(extra="forbid")

    id: Optional[str] = None
    public_id: str
    name: str
    format: str
    public_url: str
    visibility: Optional[str] = None
    description: Optional[str] = ""
    created_at: Optional[datetime] = None
    last_updated_at: Optional[datetime] = None
    stats: DeckStats = Field(default_factory=DeckStats)
    created_by: Optional[Author] = None
    authors: List[Author] = Field(default_factory=list)
    tags: List[DeckTag] = Field(default_factory=list)
    hubs: List[str] = Field(default_factory=list)
    colors: List[str] = Field(default_factory=list)
    color_identity: List[str] = Field(default_factory=list)
    boards: List[DeckBoard] = Field(default_factory=list)
    tokens: List[Dict[str, Any]] = Field(default_factory=list)


class UserDecksResponse(BaseModel):
    """Main response payload for the /users/{username}/decks route."""

    model_config = ConfigDict(extra="forbid")

    user: UserSummary
    total_decks: int
    decks: List[DeckDetail] = Field(default_factory=list)


class UserDeckSummariesResponse(BaseModel):
    """Response for routes returning decks without card details."""

    model_config = ConfigDict(extra="forbid")

    user: UserSummary
    total_decks: int
    decks: List[DeckSummary] = Field(default_factory=list)
