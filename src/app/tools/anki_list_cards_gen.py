"""
GENERATED – DO NOT EDIT

Tier-3 generated interface for anki_list_cards tool.
This file contains tool decorators that call Tier-2 business logic.
"""

from langchain.tools import tool
from src.core.dependencies import get_dependency_container


@tool
def anki_list_cards(deck: str, limit: int):
    """
    Retrieve cards from a specific Anki deck
    
    Args:
                deck: Name of the deck to retrieve cards from
        limit: Maximum number of cards to return
    
    Returns:
        List of cards from the specified deck
    """
    # NO BUSINESS LOGIC - just calls Tier-2
    deps = get_dependency_container()
    result = deps.cards_tool.list_cards(deck, limit)
    # Convert Pydantic model to dict for LangChain compatibility
    return result.model_dump()
