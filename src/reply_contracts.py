from typing import List, Literal, Union
from pydantic import BaseModel, Field, ValidationError
from src.config import load_invariants
INV = load_invariants()

class Deck(BaseModel):
    name: str
    note_count: int

class DeckListMessage(BaseModel):
    kind: Literal["deck_list"]
    decks: List[Deck] = Field(max_length=INV.max_decks)
    next_hint: str | None = None

class Card(BaseModel):
    id: str
    front: str
    back: str

class CardListMessage(BaseModel):
    kind: Literal["card_list"]
    deck: str
    cards: List[Card] = Field(max_length=INV.max_cards)

ReplyMessage = Union[DeckListMessage, CardListMessage]

def validate_reply(payload: dict) -> ReplyMessage:
    """Validate a reply payload against the appropriate contract."""
    try:
        if payload.get("kind") == "deck_list":
            return DeckListMessage(**payload)
        elif payload.get("kind") == "card_list":
            return CardListMessage(**payload)
        else:
            raise ValueError(f"Unknown message kind: {payload.get('kind')}")
    except ValidationError as e:
        raise ValueError(f"Validation failed: {e}")
