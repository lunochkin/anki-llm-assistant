from abc import ABC, abstractmethod
from ..contracts import Deck, Card
from ..generated.models import CardList


class AnkiService(ABC):
    """Abstract base class for Anki data access services"""
    
    @abstractmethod
    def get_decks(self, limit: int) -> list[Deck]:
        """Retrieve available Anki decks with metadata"""
        pass
    
    @abstractmethod
    def get_cards(self, deck: str, limit: int) -> list[Card]:
        """Retrieve cards from a specific Anki deck"""
        pass


class MockAnkiService(AnkiService):
    """Mock Anki service for testing and development"""
    
    def get_decks(self, limit: int) -> list[Deck]:
        raw_decks = self._fetch_decks_from_anki()
        return raw_decks[:limit]
    
    def _fetch_decks_from_anki(self) -> list[Deck]:
        return [
            Deck(name="French::A1", note_count=312, card_count=0),
            Deck(name="EVP C1/C2", note_count=10452, card_count=0),
            Deck(name="Default", note_count=0, card_count=0),
            Deck(name="English Personal", note_count=394, card_count=0),
        ]
    
    def get_cards(self, deck: str, limit: int) -> CardList:
        raw_cards = self._fetch_cards_from_anki(deck)
        cards = [Card(id=i, question=f"Question {i}", answer=f"Answer {i}", deck=deck) for i in raw_cards[:limit]]
        return CardList(
            kind="card_list",
            deck=deck,
            cards=cards,
            total_count=len(raw_cards),
            limit_applied=len(cards),
            has_more=len(raw_cards) > len(cards)
        )
    
    def _fetch_cards_from_anki(self, deck: str) -> list[int]:
        return list(range(1, 50))


class AnkiConnectService(AnkiService):
    """Real Anki service using AnkiConnect API"""
    
    def __init__(self, anki_url: str = "http://127.0.0.1:8765"):
        self.anki_url = anki_url
    
    def get_decks(self, limit: int) -> list[Deck]:
        """Retrieve available Anki decks via AnkiConnect"""
        import requests
        
        payload = {
            "action": "deckNames",
            "version": 6
        }
        
        try:
            response = requests.post(self.anki_url, json=payload, timeout=5)
            result = response.json()
            
            if result.get("error") is not None:
                raise Exception(f"AnkiConnect error: {result['error']}")
            
            deck_names = result.get("result", [])
            if not deck_names:
                raise Exception("No decks found in Anki collection")
            
            decks = []
            
            for deck_name in deck_names[:limit]:
                try:
                    stats = self._get_deck_stats(deck_name)
                    decks.append(Deck(
                        name=deck_name,
                        note_count=stats.get("note_count", 0),
                        card_count=stats.get("card_count", 0)
                    ))
                except Exception as e:
                    # Add deck with default stats if we can't get them
                    decks.append(Deck(
                        name=deck_name,
                        note_count=0,
                        card_count=0
                    ))
            
            return decks
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to connect to Anki: {e}")
        except Exception as e:
            raise Exception(f"Error retrieving decks: {e}")
    
    def _get_deck_stats(self, deck_name: str) -> dict:
        """Get deck statistics using getDeckStats"""
        import requests
        
        payload = {
            "action": "getDeckStats",
            "version": 6,
            "params": {"decks": [deck_name]}
        }
        
        try:
            response = requests.post(self.anki_url, json=payload, timeout=5)
            result = response.json()
            
            if result.get("error") is not None:
                raise Exception(f"AnkiConnect error: {result['error']}")
            
            stats = result.get("result", {})
            
            # Handle the actual AnkiConnect response structure
            note_count = 0
            card_count = 0
            
            if stats:
                # Find the deck stats (there should be only one entry)
                deck_stats = list(stats.values())[0] if stats else {}
                
                if deck_stats:
                    # Extract counts from the deck stats
                    card_count = deck_stats.get("total_in_deck", 0)
                    # For now, assume note_count equals card_count (this is usually true)
                    note_count = card_count
            
            return {
                "note_count": note_count,
                "card_count": card_count
            }
            
        except Exception as e:
            return {
                "note_count": 0,
                "card_count": 0
            }
    
    def get_cards(self, deck: str, limit: int) -> CardList:
        """Retrieve cards from a specific Anki deck via AnkiConnect"""
        import requests
        
        # Get card IDs for the deck
        payload = {
            "action": "findCards",
            "version": 6,
            "params": {
                "query": f"deck:{deck}"
            }
        }
        
        try:
            response = requests.post(self.anki_url, json=payload, timeout=5)
            response.raise_for_status()
            result = response.json()
            
            if result.get("error") is not None:
                raise Exception(f"AnkiConnect error: {result['error']}")
            
            all_card_ids = result.get("result", [])
            total_count = len(all_card_ids)
            
            # Apply limit for LLM processing
            limited_card_ids = all_card_ids[:limit]
            limit_applied = len(limited_card_ids)
            
            if not limited_card_ids:
                return CardList(
                    kind="card_list",
                    deck=deck,
                    cards=[],
                    total_count=total_count,
                    limit_applied=0,
                    has_more=total_count > 0
                )
            
            # Batch get info for limited cards
            cards_info = self._get_cards_info_batch(limited_card_ids)
            
            cards = []
            for i, card_info in enumerate(cards_info):
                cards.append(Card(
                    id=str(limited_card_ids[i]),
                    question=card_info.get("question", ""),
                    answer=card_info.get("answer", ""),
                    deck=deck
                ))
            
            return CardList(
                kind="card_list",
                deck=deck,
                cards=cards,
                total_count=total_count,
                limit_applied=limit_applied,
                has_more=total_count > limit_applied
            )
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to connect to Anki: {e}")
        except Exception as e:
            raise Exception(f"Error retrieving cards: {e}")
    
    def _get_cards_info_batch(self, card_ids: list[int]) -> list[dict]:
        """Get card information for multiple cards in a single API call"""
        import requests
        
        payload = {
            "action": "cardsInfo",
            "version": 6,
            "params": {"cards": card_ids}
        }
        
        try:
            response = requests.post(self.anki_url, json=payload, timeout=5)
            result = response.json()
            
            if result.get("error") is not None:
                raise Exception(f"AnkiConnect error: {result['error']}")
            
            cards_data = result.get("result", [])
            cards_info = []
            
            for card_data in cards_data:
                # Extract question and answer from fields
                fields = card_data.get("fields", {})
                
                # Try different possible field names
                question = ""
                answer = ""
                
                if "Front" in fields:
                    question = fields["Front"].get("value", "")
                elif "Question" in fields:
                    question = fields["Question"].get("value", "")
                else:
                    # Fallback: use first field as question
                    first_field = next(iter(fields.values()), {})
                    question = first_field.get("value", "")
                
                if "Back" in fields:
                    answer = fields["Back"].get("value", "")
                elif "Answer" in fields:
                    answer = fields["Answer"].get("value", "")
                else:
                    # Fallback: use second field as answer if available
                    field_values = list(fields.values())
                    if len(field_values) > 1:
                        answer = field_values[1].get("value", "")
                
                cards_info.append({
                    "question": question,
                    "answer": answer
                })
            
            return cards_info
            
        except Exception as e:
            # Return default info for all cards if batch call fails
            return [{"question": f"Card {cid}", "answer": "Information unavailable"} for cid in card_ids]