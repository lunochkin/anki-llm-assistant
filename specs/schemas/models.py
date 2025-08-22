"""
Pydantic models for Anki LLM Assistant.

This file contains the core data models used throughout the system.
These models are in Tier-1 (specs) and are imported directly by Tier-2 code.
"""

from typing import List, Literal, Union
from pydantic import BaseModel, Field
from src.core.configs.config import get_default_config


class Deck(BaseModel):
    name: str
    note_count: int


# Get invariants from config system
config = get_default_config()

class DeckListMessage(BaseModel):
    kind: Literal["deck_list"]
    decks: List[Deck] = Field(max_length=config.invariants.max_decks)


class Card(BaseModel):
    id: str
    front: str
    back: str


class CardListMessage(BaseModel):
    kind: Literal["card_list"]
    deck: str
    cards: List[Card] = Field(max_length=config.invariants.max_cards)


ReplyMessage = Union[DeckListMessage, CardListMessage]
