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


class ListLongestItem(BaseModel):
    """Item in longest examples list."""
    note_id: int = Field(..., description="Anki note ID")
    length: int = Field(..., description="Word count of example")
    example: str = Field(..., description="Example sentence excerpt")


class ListLongestResponse(BaseModel):
    """Response for longest examples list."""
    items: List[ListLongestItem] = Field(..., description="List of longest examples")
    total_found: int = Field(..., description="Total notes found")


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


class ListLongestRequest(BaseModel):
    """List longest examples request."""
    deck: str = Field(..., description="Deck name")
    field: str = Field("Example", description="Field to analyze")
    limit: int = Field(10, description="Maximum items to return")
