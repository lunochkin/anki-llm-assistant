"""
GENERATED – DO NOT EDIT

Tier-3 tool registration for Anki LLM Assistant.
This file registers decorated tools with the tool registry.
"""

from src.core.tools.schema_loader import load_schema
from .deck_tools_gen import anki_list_decks
from .card_tools_gen import anki_list_cards


def register_generated_tools(registry):
    """Register all Tier-3 decorated tools with the registry"""
    
    # Register deck tools
    registry.register_tool(
        name="anki_list_decks",
        tool_func=anki_list_decks,  # Tier-3 decorated tool
        schema=load_schema("schemas/tools/anki_list_decks.schema.json")
    )
    
    # Register card tools
    registry.register_tool(
        name="anki_list_cards",
        tool_func=anki_list_cards,  # Tier-3 decorated tool
        schema=load_schema("schemas/tools/anki_list_cards.schema.json")
    )
