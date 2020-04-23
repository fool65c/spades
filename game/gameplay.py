import uuid
import random

from .player import Player
from .deck import Deck, CardSuit, Card

from typing import List, Dict
from dataclasses import dataclass

class NotPlayerTurn(Exception):
    pass

class SpadesNotBroken(Exception):
    pass

class MustPlayOnSuit(Exception):
    pass

@dataclass
class RoundScore:
    team1_score: int = 0
    team1_bags: int = 0
    team2_score: int = 0 
    team2_bags: int = 0

    def to_json(self):
        return {
            'team1': {
                'score': self.team1_score,
                'bags': self.team1_bags
            },
            'team2': {
                'score': self.team2_score,
                'bags': self.team2_bags
            }
        }

class Game:
    def __init__(self, name: str):
        self.id = str(uuid.uuid1())
        self.name = name
        self.team1: List[Player] = []
        self.team2: List[Player] = []
        self.rounds: List[Round] = []

        self.dealer_order: List[Player] = []

        self.in_progress = False

    @property
    def players(self):
        return self.team1 + self.team2

    @property
    def current_round(self):
        return self.rounds[-1]

    def reconnect_player(self, player: Player):
        self.team1 = [p if p != player else player for p in self.team1]
        self.team2 = [p if p != player else player for p in self.team2]

    def start(self):
        self.in_progress = True
        self.dealer_order = []
        self.dealer_order.append(list(self.team1)[0])
        self.dealer_order.append(list(self.team2)[0])
        self.dealer_order.append(list(self.team1)[1])
        self.dealer_order.append(list(self.team2)[1])

        self.player_order: List[Player] = []

        self.start_next_round()

    def get_next_dealer(self) -> Player:
        # get the dealer off the list
        next_dealer = self.dealer_order.pop(0)
        # add them back to the end
        self.dealer_order.append(next_dealer)
        # set the player order to the "next" dealer order
        self.player_order = self.dealer_order.copy()

        return next_dealer

    def start_next_round(self):
        round = Round(
                    dealer=self.get_next_dealer(),
                    player_order=self.player_order,
                    team1=self.team1,
                    team2=self.team2
                )
        self.rounds.append(round)
        return round

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'team1': [t.to_json() for t in self.team1],
            'team2': [t.to_json() for t in self.team2]
        }

    @property
    def winner(self):
        score = self.get_round_scores()

        if score['overall']['team1']['score'] >= 300:
            return ' + '.join([p.name for p in self.team1])
        elif score['overall']['team2']['score'] >= 300:
            return ' + '.join([p.name for p in self.team2])
        else:
            return None

    def get_round_scores(self):
        rsl = []
        overall_score = RoundScore()

        for r in self.rounds:
            if r.complete:
                rs = r.round_score
                overall_score.team1_score += rs.team1_score
                overall_score.team2_score += rs.team2_score
                overall_score.team1_bags += rs.team1_bags
                overall_score.team2_bags += rs.team2_bags

                if overall_score.team1_bags >= 10:
                    overall_score.team1_score += -100
                    overall_score.team1_bags += -10

                if overall_score.team2_bags >= 10:
                    overall_score.team2_score += -100
                    overall_score.team2_bags += -10

                rsl.append(rs.to_json())

        return {
            'shortName': {
                'team1': '+'.join([ p.name[0] for p in self.team1]),
                'team2': '+'.join([ p.name[0] for p in self.team2])
            },
            'overall': overall_score.to_json(),
            'rounds': rsl
        }


class Round:
    def __init__(
        self, 
        dealer: Player, 
        player_order: List[Player],
        team1: List[Player],
        team2: List[Player]
        ):

        self.hands: List[Hand] = []
        
        self.dealer = dealer
        self.player_order: List[Player] = player_order
        
        # BIDDING
        self.bid_order: List[Player] = player_order.copy()
        self.bids: Dict[str, int] = {p.id: None for p in player_order}
        self.high_bid = 0

        # Team definitions
        self.team1: Dict[str, Player] = {p.id: p for p in team1}
        self.team2: Dict[str, Player] = {p.id: p for p in team2}

        self.order_by_winner: Dict[str, List[Player]] = {}
        self.__populate_order_by_winner()

        self.deck = Deck()
        self.__deal()

    @property
    def complete(self):
        return 13 == len([h for h in self.hands if h.winner])

    @property
    def current_hand(self):
        if len(self.hands) >= 1:
            return self.hands[-1]
        else:
            return None

    @property
    def current_bidder(self):
        cb = None
        for p in self.bid_order:
            if not self.bids[p.id] and self.bids[p.id] != 0:
                cb = p
                break
        return cb

    def set_player_bid(self, p_id: str, bid: int):
        self.bids[p_id] = bid
        if bid > self.high_bid:
            self.player_order = self.order_by_winner[p_id].copy()
            self.high_bid = bid

    @property
    def team1_bids(self):
        team1_bids = 0
        for p_id in self.team1:
            if self.bids[p_id]:
                team1_bids += self.bids[p_id]

        return team1_bids

    @property
    def team2_bids(self):
        bids = 0
        for p_id in self.team2:
            if self.bids[p_id]:
                bids += self.bids[p_id]

        return bids

    @property
    def team_wins(self):
        t1_w = 0
        t2_w = 0
        for h in self.hands:
            if h.winner:
                if h.winner.id in self.team1:
                    t1_w += 1
                else:
                    t2_w += 1

        return {
            'team1': t1_w,
            'team2': t2_w
        }

    @property
    def stats(self):
        return {
            'bids': {
                'team1': self.team1_bids,
                'team2': self.team2_bids,
                'player': self.bids
            },
            'wins': self.team_wins,
            'shortName': {
                'team1': ' + '.join([ p.name[0] for p in self.team1.values()]),
                'team2': ' + '.join([ p.name[0] for p in self.team2.values()])
            }
        }

    def __populate_order_by_winner(self):
        po = self.player_order.copy()
        while po[0].id not in self.order_by_winner:
            self.order_by_winner[po[0].id] = po.copy()
            p = po.pop(0)
            po.append(p)

    def __deal(self):
        while self.deck.has_cards():
            p = self.get_next_player()
            c = self.deck.deal()
            p.cards.add(c)
            
    def get_next_player(self) -> Player:
        player: Player = self.player_order.pop(0)
        self.player_order.append(player)
        return player 

    def __spades_broken(self) -> bool:
        for h in self.hands:
            for c in h.player_cards.values():
                if c.suit == CardSuit.Spade:
                    return True
        return False

    def start(self):
        self.hands.append(Hand(
            player_order=self.player_order,
            spades_broken=self.__spades_broken()
        ))

    def start_new_hand(self):
        last_hand = self.current_hand
        if not last_hand:
            return

        if not last_hand.winner:
            return
        
        self.hands.append(Hand(
            player_order=self.order_by_winner[last_hand.winner.id],
            spades_broken=self.__spades_broken()
        ))

    @property
    def round_score(self) -> RoundScore:
        if not self.complete:
            return None

        rs = RoundScore()

        wins = self.team_wins
        team1_bids = self.team1_bids
        team2_bids = self.team2_bids

        # Calculate players going 0
        for p_id in [p_id for p_id, bid in self.bids.items() if bid == 0]:
            score = 0
            if p_id in [h.winner.id for h in self.hands]:
                score = -100
            else:
                score = 100

            if p_id in self.team1:
                rs.team1_score += score
            else:
                rs.team2_score += score

        # calculate the score
        def calc_score(bids: int, wins: int):
            if bids > wins:
                return bids * -10 + wins, 0
            else:
                return bids * 10 + (wins - bids), wins - bids

        t1s, t1b = calc_score(team1_bids, wins['team1'])
        t2s, t2b = calc_score(team2_bids, wins['team2'])

        rs.team1_score += t1s
        rs.team1_bags = t1b
        rs.team2_score += t2s
        rs.team2_bags = t2b

        return rs


        

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