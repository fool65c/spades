import random

from enum import Enum
from typing import Set

class CardValue(Enum):
    Two = 2
    Three = 3
    Four = 4
    Five = 5
    Six = 6
    Seven = 7
    Eight = 8
    Nine = 9
    Ten = 10
    Jack = 11
    Queen = 12
    King = 13
    Ace = 14

    @property
    def face_value(self):
        if self == CardValue.Jack:
            return 'J'
        elif self == CardValue.Queen:
            return 'Q'
        elif self == CardValue.King:
            return 'K'
        elif self == CardValue.Ace:
            return 'A'
        else:
            return self.value


class CardSuit(Enum):
    Spade = '♠️'
    Heart = '♥️'
    Club = '♣️'
    Diamond = '♦️'

class Card:
    def __init__(self, card_value: CardValue, card_suit: CardSuit):
        self.value = card_value
        self.suit = card_suit

    @classmethod
    def from_str(cls, value: str, suit: str):
        if value == 'A':
            cv = CardValue.Ace
        elif value == 'K':
            cv = CardValue.King
        elif value == 'Q':
            cv = CardValue.Queen
        elif value == 'J':
            cv = CardValue.Jack
        else:
            cv = CardValue(int(value))

        return cls(card_value=cv, card_suit=CardSuit(suit))


    def __lt__(self, other):
        # Other card is a spade and we are not
        if other.suit == CardSuit.Spade and self.suit != CardSuit.Spade:
            return True
        
        # We are a spade and other is not
        if self.suit == CardSuit.Spade and other.suit != CardSuit.Spade:
            return False

        # suits are different
        if self.suit != other.suit:
            return True

        return self.value.value < other.value.value

    def __gt__(self, other):
        return self.__lt__(other) == False

    def __eq__(self, other):
        return self.suit == other.suit and self.value == other.value

    def __le__(self, other):
        if self.__eq__(other):
            return True
        return self.__lt__(other)

    def __ge__(self, other):
        if self.__eq__(other):
            return True
        return self.__gt__(other)

    def __hash__(self):
        return hash(str(self.suit.value) + str(self.value.value))
    
    def to_json(self):
        return {
            'suit': self.suit.value,
            'value': self.value.face_value
        }


class Deck:
    def __init__(self):
        self.cards: List[Card] = []
        for suit in CardSuit:
            for value in CardValue:
                self.cards.append(Card(
                    card_value=value,
                    card_suit=suit
                ))

        random.shuffle(self.cards)
        random.shuffle(self.cards)
        random.shuffle(self.cards)
        random.shuffle(self.cards)

    def deal(self) -> Card:
        return self.cards.pop()

    def has_cards(self) -> bool:
        return len(self.cards) > 0
