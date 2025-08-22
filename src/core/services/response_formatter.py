from ..contracts import DeckListMessage, CardListMessage


class ResponseFormatter:
    def format_deck_list(self, decks: list) -> DeckListMessage:
        # Business logic: response structure
        return DeckListMessage(kind="deck_list", decks=decks)

    def format_card_list(self, deck: str, cards: list) -> CardListMessage:
        # Business logic: response structure
        return CardListMessage(kind="card_list", deck=deck, cards=cards)