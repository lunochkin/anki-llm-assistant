"""
GENERATED – DO NOT EDIT

Tier-3 generated interface for deck-related tools.
This file contains tool decorators that call Tier-2 business logic.
"""

from langchain.tools import tool
from src.core.dependencies import get_dependency_container


@tool("anki_list_decks")
def anki_list_decks(limit: int):
    """
    List available Anki decks with a limit on the number of decks returned.
    
    Args:
        limit: Maximum number of decks to return (1-10)
    
    Returns:
        Dictionary containing deck list with metadata
    """
    # NO BUSINESS LOGIC - just calls Tier-2
    deps = get_dependency_container()
    return deps.decks_tool.list_decks(limit)
