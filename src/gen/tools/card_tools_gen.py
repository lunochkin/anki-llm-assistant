"""
GENERATED – DO NOT EDIT

Tier-3 generated interface for card-related tools.
This file contains tool decorators that call Tier-2 business logic.
"""

from langchain.tools import tool
from src.core.dependencies import get_dependency_container


@tool("anki_list_cards")
def anki_list_cards(deck: str, limit: int):
    """
    List cards from a specific Anki deck with a limit on the number of cards returned.
    
    Args:
        deck: Exact deck name to query
        limit: Maximum number of cards to return (1-10)
    
    Returns:
        Dictionary containing card list with front/back content
    """
    # NO BUSINESS LOGIC - just calls Tier-2
    deps = get_dependency_container()
    return deps.cards_tool.list_cards(deck, limit)
