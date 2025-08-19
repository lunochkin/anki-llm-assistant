"""Chat router for natural language commands."""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import ChatRequest, ChatResponse
from app.services.logic import LogicService, LogicServiceError
from app.services.llm import LLMService, LLMServiceError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


async def get_logic_service() -> LogicService:
    """Dependency to get logic service."""
    return LogicService()


async def get_llm_service() -> LLMService:
    """Dependency to get LLM service."""
    return LLMService()


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    logic_service: LogicService = Depends(get_logic_service),
    llm_service: LLMService = Depends(get_llm_service)
):
    """Handle natural language chat commands."""
    try:
        # Parse intent from natural language
        intent = await llm_service.parse_intent(request.message)
        action = intent["action"]
        
        deck_name = intent.get('deck', 'N/A')
        logger.info(f"Parsed intent: {action} for deck '{deck_name}'")
        
        if action == "compact_examples":
            return await handle_compact_examples(request, intent, logic_service)
        elif action == "rollback":
            return await handle_rollback(intent, logic_service)
        elif action == "list_cards":
            return await handle_list_cards(intent, logic_service)
        elif action == "list_decks":
            return await handle_list_decks(intent, logic_service)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {action}")
            
    except LLMServiceError as e:
        logger.error(f"LLM service error: {e}")
        raise HTTPException(status_code=500, detail=f"LLM service error: {e}")
    except LogicServiceError as e:
        logger.error(f"Logic service error: {e}")
        raise HTTPException(status_code=500, detail=f"Logic service error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in chat: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def handle_compact_examples(
    request: ChatRequest, 
    intent: Dict[str, Any], 
    logic_service: LogicService
) -> ChatResponse:
    """Handle compact examples action."""
    deck = intent["deck"]
    field = intent["field"]
    preview_count = intent["preview_count"]
    limit = intent["limit"]
    
    # Check if this is a confirmation
    if request.confirm or request.confirm_token:
        if request.confirm_token:
            # Apply compaction using token
            try:
                summary = await logic_service.apply_compaction(request.confirm_token)
                return ChatResponse(
                    message=f"Successfully compacted examples in deck '{deck}'. "
                           f"Updated: {summary.updated}, Skipped: {summary.skipped}, "
                           f"Tagged: {summary.tagged}",
                    action="compact_examples",
                    data=summary.dict(),
                    needs_confirmation=False
                )
            except LogicServiceError as e:
                raise HTTPException(status_code=400, detail=str(e))
        else:
            # Direct confirmation
            preview_response = await logic_service.compact_examples(
                deck=deck,
                field=field,
                preview_count=preview_count,
                limit=limit,
                dry_run=False
            )
            
            if preview_response.needs_confirmation:
                # This shouldn't happen with direct confirmation
                raise HTTPException(status_code=400, detail="Unexpected confirmation needed")
            
            return ChatResponse(
                message=f"Successfully compacted {preview_response.count} examples in deck '{deck}'",
                action="compact_examples",
                data={"count": preview_response.count},
                needs_confirmation=False
            )
    else:
        # Preview mode
        preview_response = await logic_service.compact_examples(
            deck=deck,
            field=field,
            preview_count=preview_count,
            limit=limit,
            dry_run=True
        )
        
        if preview_response.count == 0:
            return ChatResponse(
                message=f"No examples found for compaction in deck '{deck}'",
                action="compact_examples",
                data={"count": 0},
                needs_confirmation=False
            )
        
        # Show preview and ask for confirmation
        preview_text = format_preview_diffs(preview_response.diffs)
        message = (
            f"Found {preview_response.count} examples to compact in deck '{deck}'. "
            f"Here's a preview:\n\n{preview_text}\n\n"
            f"Use the confirmation token to apply these changes."
        )
        
        return ChatResponse(
            message=message,
            action="compact_examples",
            data=preview_response.dict(),
            needs_confirmation=True,
            confirm_token=preview_response.confirm_token
        )


async def handle_rollback(
    intent: Dict[str, Any], 
    logic_service: LogicService
) -> ChatResponse:
    """Handle rollback action."""
    deck = intent["deck"]
    field = intent["field"]
    
    # Rollback doesn't need confirmation for safety
    rollback_response = await logic_service.rollback_compacted(deck, field)
    
    if rollback_response.restored == 0:
        return ChatResponse(
            message=f"No compacted examples found to rollback in deck '{deck}'",
            action="rollback",
            data=rollback_response.dict(),
            needs_confirmation=False
        )
    
    return ChatResponse(
        message=f"Successfully rolled back {rollback_response.restored} examples "
               f"in deck '{deck}'",
        action="rollback",
        data=rollback_response.dict(),
        needs_confirmation=False
    )


async def handle_list_cards(
    intent: Dict[str, Any], 
    logic_service: LogicService
) -> ChatResponse:
    """Handle list cards action."""
    deck = intent["deck"]
    field = intent["field"]
    limit = intent["limit"]
    filter_description = intent.get("filter_description", "")
    position = intent.get("position", "top")
    
    list_response = await logic_service.list_cards(deck, field, filter_description, limit, position)
    
    if list_response.total_found == 0:
        return ChatResponse(
            message=f"No cards found in deck '{deck}'",
            action="list_cards",
            data={"total_found": 0},
            needs_confirmation=False
        )
    
    # Format the list
    items_text = format_cards_list(list_response.items)
    
    # Customize message based on whether filtering was applied
    if filter_description:
        message = (
            f"Found {list_response.total_found} cards in deck '{deck}' matching '{filter_description}'. "
            f"Top {len(list_response.items)}:\n\n{items_text}"
        )
    else:
        position_text = position.capitalize()
        message = (
            f"Found {list_response.total_found} cards in deck '{deck}'. "
            f"{position_text} {len(list_response.items)} (natural deck order):\n\n{items_text}"
        )
    
    # Add deck resolution information if applicable
    if list_response.deck_resolved:
        message = f"Note: Resolved deck name '{list_response.deck_resolved}' to '{deck}'\n\n" + message
    
    return ChatResponse(
        message=message,
        action="list_cards",
        data=list_response.dict(),
        needs_confirmation=False
    )


async def handle_list_decks(
    intent: Dict[str, Any], 
    logic_service: LogicService
) -> ChatResponse:
    """Handle list decks action."""
    # This action doesn't need confirmation
    decks = await logic_service.list_decks()
    
    if not decks:
        return ChatResponse(
            message="No decks found.",
            action="list_decks",
            data={"total_found": 0},
            needs_confirmation=False
        )
    
    # Format the list
    items_text = format_decks_list(decks)
    message = (
        f"Found {len(decks)} decks:\n\n{items_text}"
    )
    
    return ChatResponse(
        message=message,
        action="list_decks",
        data={"total_found": len(decks)},
        needs_confirmation=False
    )


def format_preview_diffs(diffs) -> str:
    """Format preview diffs for display."""
    if not diffs:
        return "No diffs to show"
    
    lines = []
    for diff in diffs:
        lines.append(f"Note {diff.note_id} (word: '{diff.word}'):")
        lines.append(f"  Old: {diff.old}")
        lines.append(f"  New: {diff.new}")
        lines.append("")
    
    return "\n".join(lines)


def format_cards_list(cards) -> str:
    """Format cards list for display."""
    if not cards:
        return "No cards to show"
    
    lines = []
    for i, card in enumerate(cards, 1):
        score_text = f"Score: {card.score:.2f}"
        lines.append(f"{i}. Note {card.note_id} ({score_text}):")
        lines.append(f"   {card.example[:100]}{'...' if len(card.example) > 100 else ''}")
        if card.reasoning:
            lines.append(f"   Reason: {card.reasoning}")
        lines.append("")
    
    return "\n".join(lines)


def format_decks_list(decks) -> str:
    """Format decks list for display."""
    if not decks:
        return "No decks to show"
    
    lines = []
    for i, deck in enumerate(decks, 1):
        deck_id = deck.get("id", "N/A")
        note_count = deck.get("note_count", 0)
        example_count = deck.get("example_count", 0)
        lines.append(f"{i}. {deck['name']} (ID: {deck_id})")
        lines.append(f"   Notes: {note_count}, Examples: {example_count}")
        lines.append("")
    
    return "\n".join(lines)
