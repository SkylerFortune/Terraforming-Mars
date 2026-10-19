from dataclasses import dataclass

from engine.game_state import GameState


@dataclass(frozen=True)
class AwardsObject:
    awards: dict[str, str]
    NUM_FUNDABLE_AWARDS: int  = 3

    def fund_award(self, award: str, player_id: str):
        return AwardsObject(
            awards={**self.awards, award: player_id}
        )

    def get_available_num_awards(self):
        return self.NUM_FUNDABLE_AWARDS - sum([1 for award, player_id in self.awards.items() if player_id])

    def get_first_second_place(self, game_state: 'GameState'):
        #TODO
        pass
        