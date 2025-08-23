from src.core.services.anki_service import AnkiService
from src.core.validators.input_validator import InputValidator
from src.core.validators.invariant_checker import InvariantChecker
from src.core.services.response_formatter import ResponseFormatter
from ..contracts import CardList


class CardsTool:
    def __init__(
        self,
        anki_service: AnkiService,
        validator: InputValidator,
        invariant_checker: InvariantChecker,
        response_formatter: ResponseFormatter,
    ):
        self.anki_service = anki_service
        self.validator = validator
        self.invariant_checker = invariant_checker
        self.response_formatter = response_formatter
    
    def list_cards(self, deck: str, limit: int) -> CardList:
        # Business logic: validate input
        validated_limit = self.validator.validate_deck_limit(limit)
        # Business logic: get data
        cards = self.anki_service.get_cards(deck, validated_limit)
        
        # Business logic: check invariants
        self.invariant_checker.ensure_card_limit(cards)
        
        # Business logic: format response
        return self.response_formatter.format_card_list(deck, cards)