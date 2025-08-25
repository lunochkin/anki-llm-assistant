"""
GENERATED – DO NOT EDIT

Tier-3 generated interface for anki_list_decks tool.
This file contains tool decorators that call Tier-2 business logic.
"""

from langchain.tools import tool
from src.core.dependencies import get_dependency_container
from src.core.generated.models import DeckListInput


@tool
def anki_list_decks(input_data: str):
    """
    Retrieve a list of available Anki decks with metadata
    
    Expected input parameters:
                limit (int): Maximum number of decks to return
    
    Args:
        input_data: JSON string containing the input parameters
    
    Returns:
        List of decks with metadata
    """
    # NO BUSINESS LOGIC - just calls Tier-2
    import json
    
    deps = get_dependency_container()
    
    # Parse JSON string and create Pydantic model instance
    input_dict = json.loads(input_data)
    input_model = DeckListInput(**input_dict)
    
    result = deps.decks_tool.list_decks(input_model)
    # Convert Pydantic model to dict for LangChain compatibility
    return result.model_dump()
