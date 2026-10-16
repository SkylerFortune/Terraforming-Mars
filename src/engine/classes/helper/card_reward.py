from dataclasses import dataclass

@dataclass
class CardReward:
    card_type: str = "any"
    count: int = 0