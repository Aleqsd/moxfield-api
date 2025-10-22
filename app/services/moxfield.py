"""Service helpers that orchestrate calls to Moxfield and format responses."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from ..moxfield import MoxfieldClient
from ..schemas import (
    Author,
    DeckBoard,
    DeckCard,
    DeckDetail,
    DeckStats,
    DeckSummary,
    DeckTag,
    UserDeckSummariesResponse,
    UserDecksResponse,
    UserSummary,
)


def build_user_decks_response(client: MoxfieldClient, username: str) -> UserDecksResponse:
    """Fetch and normalize the payload returned by the API endpoint."""
    raw_payload = client.collect_user_decks_with_details(username)
    user_summary = _transform_user_summary(raw_payload["user"])
    decks = [_transform_deck(detail) for detail in raw_payload["decks"]]
    return UserDecksResponse(user=user_summary, total_decks=len(decks), decks=decks)


def build_user_deck_summaries_response(
    client: MoxfieldClient, username: str
) -> UserDeckSummariesResponse:
    """Fetch deck summaries for a user without fetching card data."""
    raw_user = client.get_user_summary(username)
    raw_decks = client.get_user_deck_summaries(raw_user["userName"])
    user_summary = _transform_user_summary(raw_user)
    decks = [_transform_deck_summary(deck) for deck in raw_decks]
    return UserDeckSummariesResponse(user=user_summary, total_decks=len(decks), decks=decks)


def _transform_user_summary(raw: Dict[str, Any]) -> UserSummary:
    return UserSummary(
        user_name=raw.get("userName"),
        display_name=raw.get("displayName"),
        profile_image_url=raw.get("profileImageUrl"),
        profile_url=f"https://www.moxfield.com/users/{raw.get('userName')}",
        badges=raw.get("badges", []),
    )


def _transform_deck(raw: Dict[str, Any]) -> DeckDetail:
    stats = DeckStats(
        like_count=raw.get("likeCount", 0),
        view_count=raw.get("viewCount", 0),
        comment_count=raw.get("commentCount", 0),
        bookmark_count=raw.get("bookmarkCount", 0),
    )
    boards = _transform_boards(raw.get("boards", {}))

    return DeckDetail(
        id=raw.get("id"),
        public_id=raw.get("publicId"),
        name=raw.get("name"),
        format=raw.get("format"),
        visibility=raw.get("visibility"),
        description=raw.get("description") or "",
        public_url=raw.get("publicUrl"),
        created_at=_parse_timestamp(raw.get("createdAtUtc")),
        last_updated_at=_parse_timestamp(raw.get("lastUpdatedAtUtc")),
        stats=stats,
        created_by=_transform_author(raw.get("createdByUser")),
        authors=[author for author in (_transform_author(a) for a in raw.get("authors", [])) if author],
        tags=_transform_tags(raw.get("authorTags")),
        hubs=[hub.get("name") for hub in raw.get("hubs", []) if isinstance(hub, dict)],
        colors=raw.get("colors", []),
        color_identity=raw.get("colorIdentity", []),
        boards=boards,
        tokens=raw.get("tokens", []),
    )


def _transform_deck_summary(raw: Dict[str, Any]) -> DeckSummary:
    stats = DeckStats(
        like_count=raw.get("likeCount", 0),
        view_count=raw.get("viewCount", 0),
        comment_count=raw.get("commentCount", 0),
        bookmark_count=raw.get("bookmarkCount", 0),
    )
    return DeckSummary(
        id=raw.get("id"),
        public_id=raw.get("publicId"),
        name=raw.get("name"),
        format=raw.get("format"),
        visibility=raw.get("visibility"),
        description=raw.get("description") or "",
        public_url=raw.get("publicUrl"),
        created_at=_parse_timestamp(raw.get("createdAtUtc")),
        last_updated_at=_parse_timestamp(raw.get("lastUpdatedAtUtc")),
        stats=stats,
        created_by=_transform_author(raw.get("createdByUser")),
        authors=[author for author in (_transform_author(a) for a in raw.get("authors", [])) if author],
        tags=_transform_tags(raw.get("authorTags")),
        hubs=[hub.get("name") for hub in raw.get("hubs", []) if isinstance(hub, dict)],
        colors=raw.get("colors", []),
        color_identity=raw.get("colorIdentity", []),
    )


def _transform_boards(raw_boards: Dict[str, Any]) -> List[DeckBoard]:
    boards: List[DeckBoard] = []
    for board_name, board_data in raw_boards.items():
        cards = _transform_board_cards(board_data.get("cards", {}))
        boards.append(
            DeckBoard(
                name=board_name,
                count=board_data.get("count"),
                cards=cards,
            )
        )
    return boards


def _transform_board_cards(raw_cards: Dict[str, Any]) -> List[DeckCard]:
    cards: List[DeckCard] = []
    for card_data in raw_cards.values():
        cards.append(
            DeckCard(
                quantity=card_data.get("quantity", 0),
                finish=card_data.get("finish"),
                is_foil=card_data.get("isFoil"),
                is_alter=card_data.get("isAlter"),
                is_proxy=card_data.get("isProxy"),
                card=card_data.get("card", {}),
            )
        )
    return cards


def _transform_author(raw_author: Optional[Dict[str, Any]]) -> Optional[Author]:
    if not raw_author:
        return None
    return Author(
        user_name=raw_author.get("userName"),
        display_name=raw_author.get("displayName"),
        profile_image_url=raw_author.get("profileImageUrl"),
    )


def _transform_tags(raw_tags: Any) -> List[DeckTag]:
    tags: List[DeckTag] = []
    if isinstance(raw_tags, dict):
        for card_name, tag_list in raw_tags.items():
            tags.append(
                DeckTag(card_name=str(card_name), tags=list(tag_list) if isinstance(tag_list, list) else [])
            )
    elif isinstance(raw_tags, list):
        for entry in raw_tags:
            if isinstance(entry, dict) and "card_name" in entry:
                tags.append(
                    DeckTag(
                        card_name=str(entry["card_name"]),
                        tags=list(entry.get("tags", [])) if isinstance(entry.get("tags"), list) else [],
                    )
                )
    return tags


def _parse_timestamp(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = f"{value[:-1]}+00:00"
        return datetime.fromisoformat(value)
    except ValueError:
        return None
