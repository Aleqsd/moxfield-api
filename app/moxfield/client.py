"""HTTP client for interacting with the public Moxfield API endpoints."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import cloudscraper
from requests import Response

from .errors import MoxfieldError, MoxfieldNotFoundError

DEFAULT_BASE_URL = "https://api2.moxfield.com"


class MoxfieldClient:
    """Minimal client wrapper around the Moxfield API."""

    def __init__(
        self,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 15.0,
        scraper: Optional[cloudscraper.CloudScraper] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._scraper = scraper or cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "mobile": False}
        )
        # Moxfield is more stable if a referer/user-agent is provided.
        self._scraper.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/118.0.0.0 Safari/537.36"
                ),
                "Referer": "https://www.moxfield.com/",
            }
        )

    # --------------------------------------------------------------------- #
    # Public API methods                                                    #
    # --------------------------------------------------------------------- #

    def get_user_summary(self, username: str) -> Dict[str, Any]:
        """Lookup a user and return the summary metadata published in search."""
        params = {
            "filter": username,
            "pageNumber": 1,
            "pageSize": 10,
        }
        payload = self._request_json("GET", "/v2/users/search-sfw", params=params)
        data = payload.get("data", [])
        for entry in data:
            if entry.get("userName", "").lower() == username.lower():
                return entry
        raise MoxfieldNotFoundError(f"Moxfield user '{username}' was not found.")

    def get_user_deck_summaries(
        self,
        username: str,
        *,
        page_size: int = 100,
        include_pinned: bool = True,
    ) -> List[Dict[str, Any]]:
        """Return all public deck summaries for the given username."""
        page = 1
        decks: List[Dict[str, Any]] = []
        while True:
            params = {
                "authorUserNames": username,
                "pageNumber": page,
                "pageSize": page_size,
                "sortType": "Updated",
                "sortDirection": "Descending",
                "filter": "",
                "fmt": "",
                "includePinned": include_pinned,
                "showIllegal": True,
            }
            payload = self._request_json("GET", "/v2/decks/search-sfw", params=params)
            data = payload.get("data", [])
            decks.extend(data)
            total_pages = int(payload.get("totalPages", page))
            if page >= total_pages or not data:
                break
            page += 1
        return decks

    def get_deck_details(self, public_id: str) -> Dict[str, Any]:
        """Fetch full deck details (including board data) by public identifier."""
        return self._request_json("GET", f"/v3/decks/all/{public_id}")

    def collect_user_decks_with_details(
        self,
        username: str,
        *,
        page_size: int = 100,
        include_pinned: bool = True,
    ) -> Dict[str, Any]:
        """Gather the summary user data alongside full deck details."""
        user_summary = self.get_user_summary(username)
        deck_summaries = self.get_user_deck_summaries(
            user_summary["userName"],
            page_size=page_size,
            include_pinned=include_pinned,
        )
        decks: List[Dict[str, Any]] = []
        for deck in deck_summaries:
            public_id = deck.get("publicId")
            if not public_id:
                # Skip malformed deck objects.
                continue
            detail = self.get_deck_details(public_id)
            decks.append(detail)
        return {
            "user": user_summary,
            "decks": decks,
        }

    # --------------------------------------------------------------------- #
    # Internal helpers                                                      #
    # --------------------------------------------------------------------- #

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        response = self._request(method, path, params=params)
        try:
            return response.json()
        except ValueError as exc:  # pragma: no cover - defensive
            raise MoxfieldError(
                f"Failed to parse JSON response from '{path}'."
            ) from exc

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
    ) -> Response:
        url = path if path.startswith("http") else f"{self.base_url}{path}"
        try:
            response = self._scraper.request(
                method,
                url,
                params=params,
                timeout=self.timeout,
            )
        except Exception as exc:  # pragma: no cover - network failure
            raise MoxfieldError(f"Failed to contact Moxfield: {exc}") from exc

        if response.status_code == 404:
            raise MoxfieldNotFoundError(
                f"Moxfield resource '{url}' returned HTTP 404."
            )

        if not 200 <= response.status_code < 300:
            raise MoxfieldError(
                f"Moxfield request to '{url}' failed with "
                f"status {response.status_code}: {response.text}"
            )
        return response
