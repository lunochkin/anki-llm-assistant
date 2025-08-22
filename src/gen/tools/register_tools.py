"""
GENERATED – DO NOT EDIT

Tier-3 tool registration for Anki LLM Assistant.
This file registers decorated tools with the tool registry.
"""

from .deck_tools_gen import anki_list_decks
from .card_tools_gen import anki_list_cards
from src.core.tools.tool_spec_loader import validate_tool_exists


def register_generated_tools(registry):
    """Register all Tier-3 decorated tools with the registry"""
    
    # Only register tools that are specified in Tier-1
    if validate_tool_exists("anki_list_decks"):
        registry.register_tool(
            name="anki_list_decks",
            tool_func=anki_list_decks,  # Tier-3 decorated tool
            schema=None  # Schema validation handled by Pydantic models
        )
    
    if validate_tool_exists("anki_list_cards"):
        registry.register_tool(
            name="anki_list_cards",
            tool_func=anki_list_cards,  # Tier-3 decorated tool
            schema=None  # Schema validation handled by Pydantic models
        )
