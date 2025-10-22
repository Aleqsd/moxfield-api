"""FastAPI dependency providers."""

from functools import lru_cache

from .moxfield import MoxfieldClient


@lru_cache(maxsize=1)
def get_moxfield_client() -> MoxfieldClient:
    """Return a singleton Moxfield client instance."""
    return MoxfieldClient()
