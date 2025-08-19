"""Service for handling deck operations."""

import logging
from typing import List, Dict, Any
from app.services.anki import AnkiConnectClient

logger = logging.getLogger(__name__)


class DeckServiceError(Exception):
    """Custom exception for deck service errors."""
    pass


class DeckService:
    """Service for handling deck operations."""

    def __init__(self):
        """Initialize the deck service."""
        self.anki_client = AnkiConnectClient()

    async def list_decks(self) -> List[Dict[str, Any]]:
        """List all available decks with statistics."""
        try:
            return await self.anki_client.get_deck_stats()
        except Exception as e:
            logger.error(f"Failed to list decks: {e}")
            raise DeckServiceError(f"Failed to list decks: {e}")

    async def get_deck_names(self) -> List[str]:
        """Get list of deck names."""
        try:
            return await self.anki_client.get_deck_names()
        except Exception as e:
            logger.error(f"Failed to get deck names: {e}")
            raise DeckServiceError(f"Failed to get deck names: {e}")

    async def find_best_matching_deck(self, partial_name: str) -> str | None:
        """Find the best matching deck name using fuzzy matching."""
        try:
            return await self.anki_client.find_best_matching_deck(partial_name)
        except Exception as e:
            logger.error(f"Failed to find matching deck for '{partial_name}': {e}")
            raise DeckServiceError(f"Failed to find matching deck: {e}")
