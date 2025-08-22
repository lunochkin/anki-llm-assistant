"""
Reply validation service for Anki LLM Assistant.

This module handles validation of reply payloads against Pydantic models.
"""

from specs.schemas.models import DeckListMessage, CardListMessage, ReplyMessage


def validate_reply(payload: dict) -> ReplyMessage:
    """Validate a reply payload against the appropriate contract."""
    try:
        if payload.get("kind") == "deck_list":
            return DeckListMessage(**payload)
        elif payload.get("kind") == "card_list":
            return CardListMessage(**payload)
        else:
            raise ValueError(f"Unknown message kind: {payload.get('kind')}")
    except Exception as e:
        raise ValueError(f"Validation failed: {e}")
