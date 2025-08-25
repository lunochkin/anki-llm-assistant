"""
Tests for Anki service implementations.

This file tests both the MockAnkiService and AnkiConnectService
to ensure they properly implement the AnkiService interface.
"""

from src.core.services.anki_service import MockAnkiService, AnkiConnectService, AnkiService
from src.core.contracts import Deck, Card
from src.core.generated.models import CardList


class TestMockAnkiService:
    """Test the mock Anki service implementation"""
    
    def test_mock_service_implements_interface(self):
        """Test that MockAnkiService is a proper subclass of AnkiService"""
        service = MockAnkiService()
        assert isinstance(service, AnkiService)
    
    def test_get_decks_returns_deck_list(self):
        """Test that get_decks returns a list of Deck objects"""
        service = MockAnkiService()
        decks = service.get_decks(limit=3)
        
        assert isinstance(decks, list)
        assert len(decks) == 3
        assert all(isinstance(deck, Deck) for deck in decks)
        
        # Check specific deck names
        deck_names = [deck.name for deck in decks]
        assert "French::A1" in deck_names
        assert "EVP C1/C2" in deck_names
    
    def test_get_decks_respects_limit(self):
        """Test that get_decks respects the limit parameter"""
        service = MockAnkiService()
        
        # Test with different limits
        decks_2 = service.get_decks(limit=2)
        decks_4 = service.get_decks(limit=4)
        
        assert len(decks_2) == 2
        assert len(decks_4) == 4
    
    def test_get_cards_returns_card_list(self):
        """Test that get_cards returns a CardList object"""
        service = MockAnkiService()
        card_list = service.get_cards(deck="French::A1", limit=5)
        
        assert isinstance(card_list, CardList)
        assert card_list.kind == "card_list"
        assert card_list.deck == "French::A1"
        assert len(card_list.cards) == 5
        assert all(isinstance(card, Card) for card in card_list.cards)
        
        # Check card properties
        for card in card_list.cards:
            assert card.deck == "French::A1"
            assert card.question.startswith("Question ")
            assert card.answer.startswith("Answer ")
        
        # Check metadata
        assert card_list.total_count == 49
        assert card_list.limit_applied == 5
        assert card_list.has_more == True
    
    def test_get_cards_respects_limit(self):
        """Test that get_cards respects the limit parameter"""
        service = MockAnkiService()
        
        card_list_3 = service.get_cards(deck="French::A1", limit=3)
        card_list_7 = service.get_cards(deck="French::A1", limit=7)
        
        assert len(card_list_3.cards) == 3
        assert len(card_list_7.cards) == 7
        assert card_list_3.limit_applied == 3
        assert card_list_7.limit_applied == 7


class TestAnkiConnectService:
    """Test the AnkiConnect service implementation"""
    
    def test_anki_connect_service_implements_interface(self):
        """Test that AnkiConnectService is a proper subclass of AnkiService"""
        service = AnkiConnectService()
        assert isinstance(service, AnkiService)
    
    def test_anki_connect_service_initialization(self):
        """Test that AnkiConnectService initializes with custom URL"""
        custom_url = "http://localhost:9999"
        service = AnkiConnectService(anki_url=custom_url)
        assert service.anki_url == custom_url
    
    def test_anki_connect_service_default_url(self):
        """Test that AnkiConnectService uses default URL when none provided"""
        service = AnkiConnectService()
        assert service.anki_url == "http://127.0.0.1:8765"


class TestAnkiServiceInterface:
    """Test that both services implement the interface correctly"""
    
    def test_interface_consistency(self):
        """Test that both services have the same interface"""
        mock_service = MockAnkiService()
        anki_connect_service = AnkiConnectService()
        
        # Both should have the same methods
        assert hasattr(mock_service, 'get_decks')
        assert hasattr(mock_service, 'get_cards')
        assert hasattr(anki_connect_service, 'get_decks')
        assert hasattr(anki_connect_service, 'get_cards')
        
        # Both should be callable
        assert callable(mock_service.get_decks)
        assert callable(mock_service.get_cards)
        assert callable(anki_connect_service.get_decks)
        assert callable(anki_connect_service.get_cards)
