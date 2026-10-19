from dataclasses import dataclass

from engine.helper.player.resource_object import ResourceObject
from engine.helper.player.production_object import ProductionObject

@dataclass
class Reward:
    production: ProductionObject | None = None
    resources: ResourceObject | None = None
    city: int = 0
    greenery: int = 0
    ocean: int = 0
    special: str = ""
    temperature: int = 0
    oxygen: int = 0
    terraform_rating: int = 0
    cards: CardReward = CardReward()