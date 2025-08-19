"""Direct operations router for testing and tooling."""

import logging
from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import (
    CompactRequest, CompactPreviewResponse, ApplySummary,
    RollbackRequest, RollbackResponse, ListLongestRequest, ListLongestResponse
)
from app.services.logic import LogicService, LogicServiceError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ops", tags=["operations"])


async def get_logic_service() -> LogicService:
    """Dependency to get logic service."""
    return LogicService()


@router.post("/compact/preview", response_model=CompactPreviewResponse)
async def compact_preview(
    request: CompactRequest,
    logic_service: LogicService = Depends(get_logic_service)
):
    """Preview compaction without applying changes."""
    try:
        return await logic_service.compact_examples(
            deck=request.deck,
            field=request.field,
            preview_count=request.preview_count,
            limit=request.limit,
            dry_run=True
        )
    except LogicServiceError as e:
        logger.error(f"Compaction preview failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compact/apply", response_model=ApplySummary)
async def compact_apply(
    confirm_token: str,
    logic_service: LogicService = Depends(get_logic_service)
):
    """Apply compaction using a confirmation token."""
    try:
        return await logic_service.apply_compaction(confirm_token)
    except LogicServiceError as e:
        logger.error(f"Compaction application failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/rollback", response_model=RollbackResponse)
async def rollback(
    request: RollbackRequest,
    logic_service: LogicService = Depends(get_logic_service)
):
    """Rollback compacted examples."""
    try:
        return await logic_service.rollback_compacted(
            deck=request.deck,
            field=request.field
        )
    except LogicServiceError as e:
        logger.error(f"Rollback failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/list-longest", response_model=ListLongestResponse)
async def list_longest(
    request: ListLongestRequest,
    logic_service: LogicService = Depends(get_logic_service)
):
    """List longest examples in a deck."""
    try:
        return await logic_service.list_longest_examples(
            deck=request.deck,
            field=request.field,
            limit=request.limit
        )
    except LogicServiceError as e:
        logger.error(f"List longest failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
