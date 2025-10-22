"""Entry point for the Moxfield scraping API server."""

from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from fastapi import Depends, FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from motor.motor_asyncio import AsyncIOMotorDatabase

from .dependencies import close_mongo_client, get_mongo_database, get_moxfield_client
from .moxfield import MoxfieldClient, MoxfieldError, MoxfieldNotFoundError
from .schemas import UserDeckSummariesResponse, UserDecksResponse
from .services.moxfield import build_user_deck_summaries_response, build_user_decks_response
from .services.storage import upsert_user_deck_summaries, upsert_user_decks

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Instantiate and configure the FastAPI application."""
    app = FastAPI(
        title="Moxfield Scraping API",
        version="0.1.0",
        description="Simple proxy API that fetches public Moxfield data.",
    )

    @app.on_event("shutdown")
    async def shutdown_event() -> None:
        """Ensure connections are closed cleanly."""
        close_mongo_client()

    @app.get("/health", tags=["meta"])
    async def health_check() -> dict[str, str]:
        """Useful for uptime checks."""
        return {"status": "ok"}

    @app.get(
        "/users/{username}/deck-summaries",
        response_model=UserDeckSummariesResponse,
        tags=["users"],
        summary="Fetch a user's decks without card details.",
    )
    async def get_user_deck_summaries(
        username: str,
        client: MoxfieldClient = Depends(get_moxfield_client),
        database: AsyncIOMotorDatabase = Depends(get_mongo_database),
    ) -> UserDeckSummariesResponse:
        try:
            response = await run_in_threadpool(
                build_user_deck_summaries_response,
                client,
                username,
            )
        except MoxfieldNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except MoxfieldError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        await _try_upsert(upsert_user_deck_summaries, database, response)
        return response

    @app.get(
        "/users/{username}/decks",
        response_model=UserDecksResponse,
        tags=["users"],
        summary="Fetch a user's decks including full card details.",
    )
    async def get_user_decks(
        username: str,
        client: MoxfieldClient = Depends(get_moxfield_client),
        database: AsyncIOMotorDatabase = Depends(get_mongo_database),
    ) -> UserDecksResponse:
        try:
            response = await run_in_threadpool(build_user_decks_response, client, username)
        except MoxfieldNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except MoxfieldError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        await _try_upsert(upsert_user_decks, database, response)
        return response

    return app


app = create_app()


async def _try_upsert(
    func: Callable[[AsyncIOMotorDatabase, Any], Awaitable[None]],
    database: AsyncIOMotorDatabase,
    payload: UserDeckSummariesResponse | UserDecksResponse,
) -> None:
    """Persist payloads to MongoDB without disrupting the response path."""
    try:
        await func(database, payload)
    except Exception:  # pragma: no cover - defensive logging
        logger.exception("Failed to persist payload to MongoDB.")
