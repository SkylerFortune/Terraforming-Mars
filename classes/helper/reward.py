from dataclasses import dataclass

from classes.helper.card_reward import CardReward
from classes.helper.production import Production
from classes.helper.resources import Resources

@dataclass
class Reward:
    production: Production | None = None
    resources: Resources | None = None
    city: int = 0
    greenery: int = 0
    ocean: int = 0
    special: str = ""
    temperature: int = 0
    oxygen: int = 0
    terraform_rating: int = 0
    cards: CardReward = CardReward()