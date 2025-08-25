"""
GENERATED – DO NOT EDIT

Tier-3 generated interface for anki_list_cards tool.
This file contains tool decorators that call Tier-2 business logic.
"""

from langchain.tools import tool
from src.core.dependencies import get_dependency_container
from src.core.generated.models import CardListInput


@tool
def anki_list_cards(input_data: str):
    """
    Retrieve cards from a specific Anki deck
    
    Expected input parameters:
                deck (str): Name of the deck to retrieve cards from
        limit (int): Maximum number of cards to return
    
    Args:
        input_data: JSON string containing the input parameters
    
    Returns:
        List of cards from the specified deck
    """
    # NO BUSINESS LOGIC - just calls Tier-2
    import json
    
    deps = get_dependency_container()
    
    # Parse JSON string and create Pydantic model instance
    input_dict = json.loads(input_data)
    input_model = CardListInput(**input_dict)
    
    result = deps.cards_tool.list_cards(input_model)
    # Convert Pydantic model to dict for LangChain compatibility
    return result.model_dump()
