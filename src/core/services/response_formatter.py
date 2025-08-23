from ..contracts import DeckList, CardList


class ResponseFormatter:
    def format_deck_list(self, decks: list) -> DeckList:
        # Business logic: response structure
        return DeckList(kind="deck_list", decks=decks)

    def format_card_list(self, deck: str, cards: list) -> CardList:
        # Business logic: response structure
        return CardList(kind="card_list", deck=deck, cards=cards)