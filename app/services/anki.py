"""AnkiConnect client service."""

import httpx
import logging
from typing import List, Dict, Any, Optional
from app.models.schemas import CompactRequest

logger = logging.getLogger(__name__)


class AnkiConnectError(Exception):
    """Custom exception for AnkiConnect errors."""
    pass


class AnkiConnectClient:
    """Client for interacting with AnkiConnect."""

    def __init__(self, base_url: str = "http://127.0.0.1:8765"):
        """Initialize the AnkiConnect client."""
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()

    async def rpc(self, action: str, **params) -> Any:
        """Make a JSON-RPC call to AnkiConnect."""
        payload = {
            "action": action,
            "version": 6,
            "params": params
        }
        
        try:
            response = await self.client.post(self.base_url, json=payload)
            response.raise_for_status()
            result = response.json()
            
            # Debug logging
            logger.debug(f"AnkiConnect RPC {action} response: {result}")
            
            if "error" in result and result["error"] is not None:
                raise AnkiConnectError(f"AnkiConnect error: {result['error']}")
            
            return result.get("result")
        except httpx.HTTPError as e:
            raise AnkiConnectError(f"HTTP error: {e}")
        except Exception as e:
            raise AnkiConnectError(f"Unexpected error: {e}")

    async def find_notes(self, query: str) -> List[int]:
        """Find notes matching the query."""
        result = await self.rpc("findNotes", query=query)
        if result is None:
            return []
        return result if isinstance(result, list) else []

    async def notes_info(self, note_ids: List[int]) -> List[Dict[str, Any]]:
        """Get information about notes."""
        if not note_ids:
            return []
        result = await self.rpc("notesInfo", notes=note_ids)
        if result is None:
            return []
        return result if isinstance(result, list) else []

    async def update_note_fields(self, note_id: int, fields: Dict[str, str]) -> None:
        """Update note fields."""
        await self.rpc("updateNoteFields", note={"id": note_id, "fields": fields})

    async def add_tags(self, note_ids: List[int], tag: str) -> None:
        """Add tags to notes."""
        if not note_ids:
            return
        await self.rpc("addTags", notes=note_ids, tags=tag)

    async def remove_tags(self, note_ids: List[int], tag: str) -> None:
        """Remove tags from notes."""
        if not note_ids:
            return
        await self.rpc("removeTags", notes=note_ids, tags=tag)

    async def get_deck_names(self) -> List[str]:
        """Get list of deck names."""
        logger.debug("Calling get_deck_names")
        result = await self.rpc("deckNames")
        logger.debug(f"deckNames result: {result}")
        if result is None:
            return []
        return result if isinstance(result, list) else []

    async def get_deck_stats(self) -> List[Dict[str, Any]]:
        """Get detailed deck statistics."""
        deck_names = await self.get_deck_names()
        if not deck_names:
            return []
        
        deck_stats = []
        for deck_name in deck_names:
            try:
                # Count notes in deck
                query = f'deck:"{deck_name}"'
                notes = await self.find_notes(query)
                note_count = len(notes)
                
                # Count examples (notes with Example field)
                example_query = f'deck:"{deck_name}" has:field:Example'
                examples = await self.find_notes(example_query)
                example_count = len(examples)
                
                deck_stats.append({
                    "name": deck_name,
                    "id": None,  # We'll skip the ID for now
                    "note_count": note_count,
                    "example_count": example_count
                })
            except Exception as e:
                logger.warning(f"Failed to get stats for deck '{deck_name}': {e}")
                # Add basic info if detailed stats fail
                deck_stats.append({
                    "name": deck_name,
                    "id": None,
                    "note_count": 0,
                    "example_count": 0
                })
        
        return deck_stats

    async def get_model_field_names(self, model_name: str) -> List[str]:
        """Get field names for a note type."""
        result = await self.rpc("modelFieldNames", modelName=model_name)
        return result or []

    def build_query(self, deck: str, field: str, exclude_tag: Optional[str] = None) -> str:
        """Build an Anki query string."""
        if not deck or not deck.strip():
            raise ValueError("Deck name cannot be empty")
        
        # Use field:* syntax to find notes with content in the specified field
        query_parts = [f'deck:"{deck}"', f'{field}:*']
        
        if exclude_tag:
            query_parts.append(f'-tag:{exclude_tag}')
        
        return " ".join(query_parts)

    def build_rollback_query(self, deck: str, field: str, backup_field: str) -> str:
        """Build query for rollback operation."""
        return f'deck:"{deck}" tag:compact_examples has:field:{backup_field}'

    async def health_check(self) -> bool:
        """Check if AnkiConnect is available."""
        try:
            await self.rpc("version")
            return True
        except Exception:
            return False

    async def find_notes_for_compaction(self, request: CompactRequest) -> List[int]:
        """Find notes suitable for compaction."""
        query = self.build_query(
            deck=request.deck,
            field=request.field,
            exclude_tag="compact_examples"
        )
        return await self.find_notes(query)

    async def find_notes_for_rollback(self, deck: str, field: str) -> List[int]:
        """Find notes that can be rolled back."""
        backup_field = f"{field}_Original"
        query = self.build_rollback_query(deck, field, backup_field)
        return await self.find_notes(query)

    def extract_headword(self, note: Dict[str, Any]) -> Optional[str]:
        """Extract headword from note fields."""
        fields = note.get("fields", {})
        
        # Priority order for headword fields
        headword_fields = ["Word", "Lemma", "Target", "Headword"]
        
        for field_name in headword_fields:
            if field_name in fields and fields[field_name]["value"]:
                return fields[field_name]["value"].strip()
        
        return None

    async def detect_content_field(self, deck: str) -> Optional[str]:
        """Detect the best content field for a deck by analyzing sample notes."""
        try:
            # Get some sample notes from the deck
            sample_notes = await self.find_notes(f'deck:"{deck}"')
            if not sample_notes:
                return None
            
            # Analyze first few notes to find fields with substantial content
            sample_size = min(5, len(sample_notes))
            notes_info = await self.notes_info(sample_notes[:sample_size])
            
            field_stats = {}  # field_name -> (total_chars, non_empty_count)
            
            for note in notes_info:
                fields = note.get("fields", {})
                for field_name, field_info in fields.items():
                    content = field_info.get("value", "").strip()
                    if field_name not in field_stats:
                        field_stats[field_name] = [0, 0]
                    
                    field_stats[field_name][0] += len(content)  # total chars
                    if content:
                        field_stats[field_name][1] += 1  # non-empty count
            
            # Priority order: Example > Back > Front > other fields with most content
            priority_fields = ["Example", "Back", "Front", "Definition", "Meaning", "Translation"]
            
            # First check priority fields
            for field_name in priority_fields:
                if field_name in field_stats and field_stats[field_name][1] > 0:
                    return field_name
            
            # If no priority fields found, use field with most average content
            if field_stats:
                best_field = max(field_stats.items(), 
                               key=lambda x: x[1][0] / max(x[1][1], 1))  # avg chars per non-empty
                if best_field[1][1] > 0:  # has non-empty content
                    return best_field[0]
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to detect content field for deck '{deck}': {e}")
            return None

    async def backup_field(self, note_id: int, field: str, backup_field: str) -> bool:
        """Backup a field value."""
        try:
            note_info = await self.notes_info([note_id])
            if not note_info:
                return False
            
            note = note_info[0]
            fields = note.get("fields", {})
            
            if field not in fields or not fields[field]["value"]:
                return False
            
            # Create backup field if it doesn't exist
            backup_value = fields[field]["value"]
            await self.update_note_fields(note_id, {backup_field: backup_value})
            return True
        except Exception as e:
            logger.error(f"Failed to backup field {field} for note {note_id}: {e}")
            return False
