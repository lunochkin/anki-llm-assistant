"""
GENERATED – DO NOT EDIT

Tier-3 tool registration for Anki LLM Assistant.
This file registers decorated tools with the tool registry.
"""

import yaml
from pathlib import Path
from .deck_tools_gen import anki_list_decks
from .card_tools_gen import anki_list_cards


def register_generated_tools(registry):
    """Register all Tier-3 decorated tools with the registry"""

    # Load tool specifications from Tier-1
    project_root = Path(__file__).parent.parent.parent.parent
    tools_spec_path = project_root / "specs" / "tools.yaml"

    if not tools_spec_path.exists():
        print(f"⚠️  Tools specification not found: {tools_spec_path}")
        return

    with open(tools_spec_path, 'r') as f:
        tools_spec = yaml.safe_load(f)

    # Tool mapping: name -> function
    tools = {
        "anki_list_decks": anki_list_decks,
        "anki_list_cards": anki_list_cards,
    }

    # Register only tools specified in Tier-1
    available_tools = tools_spec.get('tools', {}).keys()
    for name, func in tools.items():
        if name in available_tools:
            registry.register_tool(
                name=name,
                tool_func=func,
                schema=None  # Schema validation handled by Pydantic models
            )
