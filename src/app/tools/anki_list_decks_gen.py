"""
GENERATED – DO NOT EDIT

Tier-3 generated interface for anki_list_decks tool.
This file contains tool decorators that call Tier-2 business logic.
"""

from langchain.tools import tool
from src.core.dependencies import get_dependency_container


@tool
def anki_list_decks(limit: int):
    """
    Retrieve a list of available Anki decks with metadata
    
    Args:
                limit: Maximum number of decks to return
    
    Returns:
        List of decks with metadata
    """
    # NO BUSINESS LOGIC - just calls Tier-2
    deps = get_dependency_container()
    result = deps.decks_tool.list_decks(limit)
    # Convert Pydantic model to dict for LangChain compatibility
    return result.model_dump()
