import uuid
import websockets

from .deck import Card, CardSuit

from typing import Set



class Player:
    def __init__(self, p_id: str, name: str, ws: websockets.protocol.WebSocketCommonProtocol):
        self.id = p_id
        self.cards: Set[Card] = set()
        self.name: str = name
        self.ws = ws

    def play_card(self, card: Card):
        self.cards.remove(card)

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'cards': self.__get_cards_json()
        }

    def to_safeson(self):
        return {
            'id': self.id,
            'name': self.name
        }

    def __get_cards_json(self):
        tmp = sorted([c for c in self.cards if c.suit == CardSuit.Diamond]) + \
            sorted([c for c in self.cards if c.suit == CardSuit.Club]) + \
            sorted([c for c in self.cards if c.suit == CardSuit.Heart]) + \
            sorted([c for c in self.cards if c.suit == CardSuit.Spade])

        return [c.to_json() for c in tmp]     

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return hash(str(self.id))