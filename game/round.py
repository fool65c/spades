from typing import List, Dict

from .hand import Hand
from .player import Player
from .roundscore import RoundScore
from .deck import Deck, CardSuit, Card

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