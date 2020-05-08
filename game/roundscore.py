from dataclasses import dataclass

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