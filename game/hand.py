from .player import Player
from .deck import Deck, CardSuit, Card

from typing import List, Dict

class NotPlayerTurn(Exception):
    pass

class SpadesNotBroken(Exception):
    pass

class MustPlayOnSuit(Exception):
    pass

class Hand:
    def __init__(
        self,
        player_order: List[Player],
        spades_broken: bool
        ):
        self.spades_broken: bool = spades_broken
        self.player_cards: Dict[Player, Card] = {}
        self.player_order: List[Player] = player_order
        self.current_player_turn: int = 0

    @property
    def winner(self) -> Player:
        if len(self.player_cards) != 4:
            return None

        winning_card: Card = None
        winner: Player = None
        for player in self.player_order:
            if not winning_card:
                winning_card = self.player_cards[player]
                winner = player
            else:
                if self.player_cards[player] > winning_card:
                    winning_card = self.player_cards[player]
                    winner = player

        return winner
    
    def play_card(self, player: Player, card: Card):
        if self.current_player_turn > 3:
            return NotPlayerTurn(f'Not your turn {player.name}')

        if player.id != self.player_order[self.current_player_turn].id:
            raise NotPlayerTurn(f'Not your turn {player.name}')

        # Check if spades are allowed to be played
        if self.current_player_turn == 0 and not self.spades_broken and card.suit == CardSuit.Spade:
            # Check if they only have spades in their hand.
            for c in player.cards:
                if c.suit != CardSuit.Spade:
                    raise SpadesNotBroken('Spades have not been broken')

        # Check if they are trying to play off suit when they have it
        if self.current_player_turn >= 1:
            first_card_suit = self.player_cards[self.player_order[0]].suit
            print(f'found first card suit {first_card_suit}')
            if first_card_suit != card.suit:
                for c in player.cards:
                    if c.suit == first_card_suit:
                        raise MustPlayOnSuit(f'You must play {first_card_suit.value}')


        player.play_card(card)
        self.player_cards[player] = card
        self.current_player_turn += 1

    def active_hand_json(self):
        ahj = {}
        for p in self.player_order:
            ahj[p.id] = 'Waiting'

            if self.current_player_turn <= 3:
                if p.id == self.player_order[self.current_player_turn].id:
                    ahj[p.id] = 'Current Turn'
            
            if p in self.player_cards:
                c = self.player_cards[p]
                ahj[p.id] = f'{c.suit.value} {c.value.face_value}'

        return ahj

    def result_json(self):
        return {
            'winner': self.winner.to_safeson()
        }