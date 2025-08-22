from src.core.services.anki_service import AnkiService
from src.core.validators.input_validator import InputValidator
from src.core.validators.invariant_checker import InvariantChecker
from src.core.services.response_formatter import ResponseFormatter
from ..contracts import DeckListMessage


class DecksTool:
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
    
    def list_decks(self, limit: int) -> DeckListMessage:
        # Business logic: validate input
        validated_limit = self.validator.validate_deck_limit(limit)
        
        # Business logic: get data
        decks = self.anki_service.get_decks(validated_limit)
        
        # Business logic: check invariants
        self.invariant_checker.ensure_deck_limit(decks)
        
        # Business logic: format response
        return self.response_formatter.format_deck_list(decks)
