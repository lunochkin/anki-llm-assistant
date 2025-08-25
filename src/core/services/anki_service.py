from ..contracts import Deck, Card


class AnkiService:
    def get_decks(self, limit: int) -> list[Deck]:
        # Business logic: data retrieval
        raw_decks = self._fetch_decks_from_anki()
        return raw_decks[:limit]  # Business rule: limit enforcement
    
    def _fetch_decks_from_anki(self) -> list[Deck]:
        # Business logic: data retrieval
        return [
            Deck(name="French::A1", note_count=312, card_count=0),
            Deck(name="EVP C1/C2", note_count=10452, card_count=0),
        ]
    
    def get_cards(self, deck: str, limit: int) -> list[Card]:
        # Business logic: data retrieval
        raw_cards = self._fetch_cards_from_anki(deck)
        return [Card(id=i, question=f"Question {i}", answer=f"Answer {i}", deck=deck) for i in raw_cards[:limit]]
    
    def _fetch_cards_from_anki(self, deck: str) -> list[int]:
        # Business logic: data retrieval
        return list(range(1, 50))