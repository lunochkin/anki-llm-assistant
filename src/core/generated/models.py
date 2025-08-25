# GENERATED - DO NOT EDIT
from __future__ import annotations
from pydantic import BaseModel
from typing import Optional, List, Literal, Any

class Card(BaseModel):
    id: int
    question: str
    answer: str
    deck: str

class DeckList(BaseModel):
    kind: Literal['deck_list']
    decks: List['Deck']

class CardList(BaseModel):
    kind: Literal['card_list']
    deck: str
    cards: List['Card']

class CardListInput(BaseModel):
    deck: str
    limit: int

class DeckListInput(BaseModel):
    limit: int

class Deck(BaseModel):
    name: str
    note_count: int
    card_count: Optional[int] = 0

