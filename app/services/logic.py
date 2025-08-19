"""Orchestration service for coordinating Anki and LLM operations."""

import logging
from typing import List, Dict, Any
from app.services.compaction import CompactionService
from app.services.cards import CardService
from app.services.decks import DeckService
from app.models.schemas import (
    CompactPreviewResponse, ApplySummary, RollbackResponse, ListCardsResponse
)

logger = logging.getLogger(__name__)


class LogicServiceError(Exception):
    """Custom exception for logic service errors."""
    pass


class LogicService:
    """Orchestration service that coordinates specialized services."""

    def __init__(self):
        """Initialize the logic service with specialized services."""
        self.compaction_service = CompactionService()
        self.card_service = CardService()
        self.deck_service = DeckService()

    async def compact_examples(
        self, 
        deck: str, 
        field: str = "Example", 
        preview_count: int = 5, 
        limit: int = 30, 
        dry_run: bool = True
    ) -> CompactPreviewResponse:
        """Compact examples in a deck with preview and confirmation."""
        try:
            return await self.compaction_service.compact_examples(
                deck, field, preview_count, limit, dry_run
            )
        except Exception as e:
            logger.error(f"Failed to compact examples: {e}")
            raise LogicServiceError(f"Compaction failed: {e}")

    async def apply_compaction(self, confirm_token: str) -> ApplySummary:
        """Apply compaction changes using a confirmation token."""
        try:
            return await self.compaction_service.apply_compaction(confirm_token)
        except Exception as e:
            logger.error(f"Failed to apply compaction: {e}")
            raise LogicServiceError(f"Application failed: {e}")

    async def rollback_compacted(self, deck: str, field: str = "Example") -> RollbackResponse:
        """Rollback compacted examples to their original versions."""
        try:
            return await self.compaction_service.rollback_compacted(deck, field)
        except Exception as e:
            logger.error(f"Failed to rollback: {e}")
            raise LogicServiceError(f"Rollback failed: {e}")

    async def list_cards(
        self, 
        deck: str, 
        field: str = "Example", 
        filter_description: str = "",
        limit: int = 10,
        position: str = "top"
    ) -> ListCardsResponse:
        """List cards based on LLM filtering or natural deck order."""
        try:
            return await self.card_service.list_cards(
                deck, field, filter_description, limit, position
            )
        except Exception as e:
            logger.error(f"Failed to list cards: {e}")
            raise LogicServiceError(f"Listing cards failed: {e}")

    async def list_decks(self) -> List[Dict[str, Any]]:
        """List all available decks with statistics."""
        try:
            return await self.deck_service.list_decks()
        except Exception as e:
            logger.error(f"Failed to list decks: {e}")
            raise LogicServiceError(f"Failed to list decks: {e}")
