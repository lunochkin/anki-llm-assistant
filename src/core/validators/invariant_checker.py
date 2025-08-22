from src.core.validators.invariant_checker_exceptions import InvariantViolation

class InvariantChecker:
    def ensure_deck_limit(self, decks: list):
        # Business rule: INV-READ-1
        if len(decks) > 10:
            raise InvariantViolation("INV-READ-1: Never show more than 10 decks")
    
    def ensure_card_limit(self, cards: list):
        # Business rule: INV-READ-2
        if len(cards) > 10:
            raise InvariantViolation("INV-READ-2: Never show more than 10 cards")