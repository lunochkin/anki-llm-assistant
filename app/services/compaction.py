"""Service for handling example compaction operations."""

import logging
import secrets
from typing import Dict, Any
from app.services.anki import AnkiConnectClient
from app.services.llm import LLMService
from app.models.schemas import (
    CompactRequest, CompactPreviewResponse, PreviewDiff, 
    ApplySummary, RollbackResponse
)

logger = logging.getLogger(__name__)


class CompactionServiceError(Exception):
    """Custom exception for compaction service errors."""
    pass


class CompactionService:
    """Service for handling example compaction operations."""

    def __init__(self):
        """Initialize the compaction service."""
        self.anki_client = AnkiConnectClient()
        self.llm_service = LLMService()
        self.confirm_tokens = {}  # Store confirmation tokens

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
            # Find notes suitable for compaction
            note_ids = await self.anki_client.find_notes_for_compaction(
                CompactRequest(deck=deck, field=field, preview_count=preview_count, limit=limit)
            )
            
            if not note_ids:
                return CompactPreviewResponse(
                    count=0,
                    diffs=[],
                    needs_confirmation=False
                )
            
            # Limit the number of notes
            note_ids = note_ids[:limit]
            
            # Get note information
            notes = await self.anki_client.notes_info(note_ids)
            
            # Prepare data for LLM compaction
            sentences_data = []
            for note in notes:
                headword = self.anki_client.extract_headword(note)
                if not headword:
                    logger.warning(f"Skipping note {note['noteId']}: no headword found")
                    continue
                
                fields = note.get("fields", {})
                if field not in fields or not fields[field]["value"]:
                    continue
                
                sentences_data.append({
                    "note_id": note["noteId"],
                    "target": headword,
                    "sentence": fields[field]["value"]
                })
            
            if not sentences_data:
                return CompactPreviewResponse(
                    count=0,
                    diffs=[],
                    needs_confirmation=False
                )
            
            # Compact sentences using LLM
            compacted_results = await self.llm_service.compact_multiple_sentences(sentences_data)
            
            # Create preview diffs
            diffs = []
            for result in compacted_results:
                if result["success"]:
                    diffs.append(PreviewDiff(
                        note_id=result["note_id"],
                        word=result["target"],
                        old=result["original"],
                        new=result["compacted"]
                    ))
            
            # Generate confirmation token if needed
            confirm_token = None
            if not dry_run and diffs:
                confirm_token = secrets.token_urlsafe(16)
                self.confirm_tokens[confirm_token] = {
                    "deck": deck,
                    "field": field,
                    "note_ids": [diff.note_id for diff in diffs],
                    "diffs": diffs
                }
            
            return CompactPreviewResponse(
                count=len(diffs),
                diffs=diffs[:preview_count],  # Only show preview_count in response
                needs_confirmation=not dry_run and bool(diffs),
                confirm_token=confirm_token
            )
            
        except Exception as e:
            logger.error(f"Failed to compact examples: {e}")
            raise CompactionServiceError(f"Compaction failed: {e}")

    async def apply_compaction(self, confirm_token: str) -> ApplySummary:
        """Apply compaction changes using a confirmation token."""
        if confirm_token not in self.confirm_tokens:
            raise CompactionServiceError("Invalid confirmation token")
        
        token_data = self.confirm_tokens[confirm_token]
        deck = token_data["deck"]
        field = token_data["field"]
        note_ids = token_data["note_ids"]
        diffs = token_data["diffs"]
        
        try:
            updated = 0
            skipped = 0
            tagged = 0
            
            for diff in diffs:
                try:
                    # Backup original field
                    backup_field = f"{field}_Original"
                    backup_success = await self.anki_client.backup_field(
                        diff.note_id, field, backup_field
                    )
                    
                    if not backup_success:
                        logger.warning(f"Failed to backup field for note {diff.note_id}")
                        skipped += 1
                        continue
                    
                    # Update with compacted version
                    await self.anki_client.update_note_fields(
                        diff.note_id, {field: diff.new}
                    )
                    
                    # Add tag
                    await self.anki_client.add_tags([diff.note_id], "compact_examples")
                    
                    updated += 1
                    tagged += 1
                    
                except Exception as e:
                    logger.error(f"Failed to update note {diff.note_id}: {e}")
                    skipped += 1
            
            # Clean up token
            del self.confirm_tokens[confirm_token]
            
            return ApplySummary(
                updated=updated,
                skipped=skipped,
                tagged=tagged
            )
            
        except Exception as e:
            logger.error(f"Failed to apply compaction: {e}")
            raise CompactionServiceError(f"Application failed: {e}")

    async def rollback_compacted(self, deck: str, field: str = "Example") -> RollbackResponse:
        """Rollback compacted examples to their original versions."""
        try:
            # Find notes that can be rolled back
            note_ids = await self.anki_client.find_notes_for_rollback(deck, field)
            
            if not note_ids:
                return RollbackResponse(restored=0, untagged=0)
            
            restored = 0
            untagged = 0
            
            for note_id in note_ids:
                try:
                    # Get note information
                    notes = await self.anki_client.notes_info([note_id])
                    if not notes:
                        continue
                    
                    note = notes[0]
                    fields = note.get("fields", {})
                    backup_field = f"{field}_Original"
                    
                    if backup_field not in fields or not fields[backup_field]["value"]:
                        continue
                    
                    # Restore original value
                    await self.anki_client.update_note_fields(
                        note_id, {field: fields[backup_field]["value"]}
                    )
                    
                    # Remove tag
                    await self.anki_client.remove_tags([note_id], "compact_examples")
                    
                    restored += 1
                    untagged += 1
                    
                except Exception as e:
                    logger.error(f"Failed to rollback note {note_id}: {e}")
            
            return RollbackResponse(restored=restored, untagged=untagged)
            
        except Exception as e:
            logger.error(f"Failed to rollback: {e}")
            raise CompactionServiceError(f"Rollback failed: {e}")
