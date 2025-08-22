from ..contracts import Deck, Card


class AnkiService:
    def get_decks(self, limit: int) -> list[Deck]:
        # Business logic: data retrieval
        raw_decks = self._fetch_decks_from_anki()
        return raw_decks[:limit]  # Business rule: limit enforcement
    
    def _fetch_decks_from_anki(self) -> list[Deck]:
        # Business logic: data retrieval
        return [
            {"name": "French::A1", "note_count": 312},
            {"name": "EVP C1/C2", "note_count": 10452},
        ]
    
    def get_cards(self, deck: str, limit: int) -> list[Card]:
        # Business logic: data retrieval
        raw_cards = self._fetch_cards_from_anki(deck)
        return {"deck": deck, "cards": raw_cards[:limit]}
    
    def _fetch_cards_from_anki(self, deck: str) -> list:
        # Business logic: data retrieval
        return [{"id": str(i), "front": f"Front {i}", "back": f"Back {i}"} for i in range(1, 50)]