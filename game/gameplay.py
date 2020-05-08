import uuid

from .player import Player
from .roundscore import RoundScore
from .round import Round

from typing import List

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