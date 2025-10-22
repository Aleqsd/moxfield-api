"""Entry point for the Moxfield scraping API server."""

from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool

from .dependencies import get_moxfield_client
from .moxfield import MoxfieldClient, MoxfieldError, MoxfieldNotFoundError
from .schemas import UserDeckSummariesResponse, UserDecksResponse
from .services.moxfield import build_user_deck_summaries_response, build_user_decks_response


def create_app() -> FastAPI:
    """Instantiate and configure the FastAPI application."""
    app = FastAPI(
        title="Moxfield Scraping API",
        version="0.1.0",
        description="Simple proxy API that fetches public Moxfield data.",
    )

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
    ) -> UserDeckSummariesResponse:
        try:
            return await run_in_threadpool(
                build_user_deck_summaries_response,
                client,
                username,
            )
        except MoxfieldNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except MoxfieldError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    @app.get(
        "/users/{username}/decks",
        response_model=UserDecksResponse,
        tags=["users"],
        summary="Fetch a user's decks including full card details.",
    )
    async def get_user_decks(
        username: str,
        client: MoxfieldClient = Depends(get_moxfield_client),
    ) -> UserDecksResponse:
        try:
            return await run_in_threadpool(build_user_decks_response, client, username)
        except MoxfieldNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except MoxfieldError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    return app


app = create_app()
