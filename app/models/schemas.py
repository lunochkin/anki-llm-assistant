"""Pydantic models for the Anki LLM Assistant."""

from typing import List, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str = Field(..., description="Natural language command")
    confirm: Optional[bool] = Field(None, description="Confirmation flag")
    confirm_token: Optional[str] = Field(None, description="Confirmation token")


class PreviewDiff(BaseModel):
    """Preview difference between old and new example."""
    note_id: int = Field(..., description="Anki note ID")
    word: str = Field(..., description="Target word/headword")
    old: str = Field(..., description="Original example sentence")
    new: str = Field(..., description="Compacted example sentence")


class CompactPreviewResponse(BaseModel):
    """Response for compact examples preview."""
    count: int = Field(..., description="Number of notes that would be updated")
    diffs: List[PreviewDiff] = Field(..., description="Preview of changes")
    needs_confirmation: bool = Field(..., description="Whether confirmation is needed")
    confirm_token: Optional[str] = Field(None, description="Token for confirmation")


class ApplySummary(BaseModel):
    """Summary of applied changes."""
    updated: int = Field(..., description="Number of notes updated")
    skipped: int = Field(..., description="Number of notes skipped")
    tagged: int = Field(..., description="Number of notes tagged")


class RollbackResponse(BaseModel):
    """Response for rollback operation."""
    restored: int = Field(..., description="Number of notes restored")
    untagged: int = Field(..., description="Number of notes untagged")


class ChatResponse(BaseModel):
    """Chat response model."""
    message: str = Field(..., description="Response message")
    action: str = Field(..., description="Action performed")
    data: Optional[dict] = Field(None, description="Response data")
    needs_confirmation: bool = Field(False, description="Whether confirmation is needed")
    confirm_token: Optional[str] = Field(None, description="Confirmation token")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    anki_connect: bool = Field(..., description="AnkiConnect availability")
    llm: bool = Field(..., description="LLM service availability")


class CompactRequest(BaseModel):
    """Compact examples request."""
    deck: str = Field(..., description="Deck name")
    field: str = Field("Example", description="Field to compact")
    preview_count: int = Field(5, description="Number of preview items")
    limit: int = Field(30, description="Maximum notes to process")
    dry_run: bool = Field(True, description="Whether to preview only")


class RollbackRequest(BaseModel):
    """Rollback request."""
    deck: str = Field(..., description="Deck name")
    field: str = Field("Example", description="Field to rollback")


class ListCardsRequest(BaseModel):
    """List cards with LLM filtering request."""
    deck: str = Field(..., description="Deck name")
    field: str = Field("Example", description="Field to analyze")
    filter_description: str = Field("", description="Natural language description of what to filter for")
    limit: int = Field(10, description="Maximum items to return")
    position: str = Field("top", description="Position in deck: 'top' or 'bottom'")


class ListCardsItem(BaseModel):
    """Item in filtered cards list."""
    note_id: int = Field(..., description="Anki note ID")
    score: float = Field(..., description="LLM relevance score (0.0-1.0)")
    example: str = Field(..., description="Example sentence excerpt")
    reasoning: str = Field(..., description="LLM reasoning for why this card matches")


class ListCardsResponse(BaseModel):
    """Response for filtered cards list."""
    items: List[ListCardsItem] = Field(..., description="List of filtered cards")
    total_found: int = Field(..., description="Total notes found")
    filter_applied: str = Field(..., description="Description of the filter that was applied")
    deck_resolved: Optional[str] = Field(None, description="Original deck name if it was resolved to a different name")
