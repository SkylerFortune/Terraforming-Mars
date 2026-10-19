from dataclasses import dataclass


@dataclass(frozen=True)
class CardReward:
    card_type: str
    amount: int