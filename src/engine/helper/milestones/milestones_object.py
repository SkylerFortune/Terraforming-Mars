from dataclasses import dataclass


@dataclass(frozen=True)
class MilestonesObject:
    milestones: dict[str, str]
    NUM_FUNDABLE_MILESTONES: int  = 3

    def fund_milestone(self, milestone: str, player_id: str):
        return MilestonesObject(
            milestones={**self.milestones, milestone: player_id}
        )

    def get_available_num_milestones(self):
        return self.NUM_FUNDABLE_MILESTONES - sum([1 for milestone, player_id in self.milestones.items() if player_id])