"""Service for handling card listing and filtering operations."""

import logging
from typing import List, Dict, Any
from app.services.anki import AnkiConnectClient
from app.services.llm import LLMService
from app.models.schemas import ListCardsResponse, ListCardsItem

logger = logging.getLogger(__name__)


class CardServiceError(Exception):
    """Custom exception for card service errors."""
    pass


class CardService:
    """Service for handling card listing and filtering operations."""

    def __init__(self):
        """Initialize the card service."""
        self.anki_client = AnkiConnectClient()
        self.llm_service = LLMService()

    async def list_cards(
        self, 
        deck: str, 
        field: str = "Example", 
        filter_description: str = "",
        limit: int = 10,
        position: str = "top"
    ) -> ListCardsResponse:
        """List cards based on LLM filtering or natural deck order."""
        original_deck = deck  # Track original deck name for resolution info
        try:
            # Try to resolve deck name and find notes
            deck, note_ids, field = await self._resolve_deck_and_find_notes(deck, field)
            
            if not note_ids:
                return ListCardsResponse(
                    items=[],
                    total_found=0,
                    filter_applied=filter_description or "No filter applied",
                    deck_resolved=original_deck if original_deck != deck else None
                )
            
            # Get note information and prepare card data
            cards_data = await self._prepare_card_data(note_ids, field)
            
            if not cards_data:
                return ListCardsResponse(
                    items=[],
                    total_found=0,
                    filter_applied=filter_description or "No filter applied",
                    deck_resolved=original_deck if original_deck != deck else None
                )
            
            # Apply filtering or natural ordering
            if filter_description.strip():
                items = await self._apply_llm_filtering(filter_description, cards_data, limit)
                filter_applied = filter_description
            else:
                items = self._apply_natural_ordering(cards_data, position, limit)
                filter_applied = f"No filter applied - natural deck order ({position})"
            
            return ListCardsResponse(
                items=items,
                total_found=len(cards_data),
                filter_applied=filter_applied,
                deck_resolved=original_deck if original_deck != deck else None
            )
            
        except Exception as e:
            logger.error(f"Failed to list cards: {e}")
            raise CardServiceError(f"Listing cards failed: {e}")

    async def _resolve_deck_and_find_notes(self, deck: str, field: str) -> tuple[str, List[int], str]:
        """Resolve deck name and find notes, with intelligent deck name resolution."""
        # First try with the specified field
        query = self.anki_client.build_query(deck, field)
        note_ids = await self.anki_client.find_notes(query)
        
        # If no notes found, try to resolve the deck name intelligently
        if not note_ids:
            logger.info(f"No notes found with deck '{deck}', attempting deck name resolution")
            available_decks = await self.anki_client.get_deck_names()
            resolved_deck = await self.anki_client.find_best_matching_deck(deck)
            
            if resolved_deck and resolved_deck != deck:
                logger.info(f"Resolved deck '{deck}' to '{resolved_deck}'")
                deck = resolved_deck
                query = self.anki_client.build_query(deck, field)
                note_ids = await self.anki_client.find_notes(query)
                
                if note_ids:
                    logger.info(f"Found {len(note_ids)} notes with resolved deck '{deck}'")
                else:
                    # Try LLM-based resolution as fallback
                    logger.info(f"Fuzzy matching failed, trying LLM-based resolution")
                    llm_resolved_deck = await self.llm_service.resolve_deck_name(deck, available_decks)
                    if llm_resolved_deck and llm_resolved_deck != deck:
                        logger.info(f"LLM resolved deck '{deck}' to '{llm_resolved_deck}'")
                        deck = llm_resolved_deck
                        query = self.anki_client.build_query(deck, field)
                        note_ids = await self.anki_client.find_notes(query)
                        if note_ids:
                            logger.info(f"Found {len(note_ids)} notes with LLM-resolved deck '{deck}'")
        
        # If no notes found with specified field, try to auto-detect a better field
        if not note_ids and field == "Example":
            logger.info(f"No notes found with field '{field}' in deck '{deck}', attempting auto-detection")
            detected_field = await self.anki_client.detect_content_field(deck)
            if detected_field:
                logger.info(f"Auto-detected field '{detected_field}' for deck '{deck}'")
                field = detected_field
                query = self.anki_client.build_query(deck, field)
                note_ids = await self.anki_client.find_notes(query)
                logger.info(f"Found {len(note_ids)} notes with detected field '{field}'")
            else:
                logger.warning(f"Could not auto-detect a suitable field for deck '{deck}'")
        
        return deck, note_ids, field

    async def _prepare_card_data(self, note_ids: List[int], field: str) -> List[Dict[str, Any]]:
        """Prepare card data from note IDs."""
        # Get note information
        notes = await self.anki_client.notes_info(note_ids)
        
        # Prepare data for processing
        cards_data = []
        for note in notes:
            fields = note.get("fields", {})
            if field in fields and fields[field]["value"]:
                example_text = fields[field]["value"]
                
                cards_data.append({
                    "note_id": note["noteId"],
                    "example": example_text
                })
        
        return cards_data

    async def _apply_llm_filtering(
        self, 
        filter_description: str, 
        cards_data: List[Dict[str, Any]], 
        limit: int
    ) -> List[ListCardsItem]:
        """Apply LLM-based filtering to cards."""
        # Use LLM to filter cards based on description
        filtered_results = await self.llm_service.filter_cards_by_description(
            filter_description, cards_data, limit
        )
        
        # Convert to response format
        items = []
        for result in filtered_results:
            # Find the corresponding card data
            card_data = next(
                (card for card in cards_data if card["note_id"] == result["note_id"]), 
                None
            )
            if card_data:
                items.append(ListCardsItem(
                    note_id=result["note_id"],
                    score=result.get("score", 0.0),
                    example=card_data["example"],
                    reasoning=result.get("reasoning", "No reasoning provided")
                ))
        
        return items

    def _apply_natural_ordering(
        self, 
        cards_data: List[Dict[str, Any]], 
        position: str, 
        limit: int
    ) -> List[ListCardsItem]:
        """Apply natural deck ordering to cards."""
        # Take cards based on position (top or bottom)
        if position.lower() == "bottom":
            # Take last 'limit' cards from the end
            natural_order_cards = cards_data[-limit:] if len(cards_data) >= limit else cards_data
        else:
            # Default to "top" - take first 'limit' cards
            natural_order_cards = cards_data[:limit]
        
        items = [
            ListCardsItem(
                note_id=card["note_id"],
                score=1.0,  # All cards get same score when no filtering
                example=card["example"],
                reasoning=f"Natural deck order - {position} {len(natural_order_cards)} cards (no filtering applied)"
            )
            for card in natural_order_cards
        ]
        
        return items
