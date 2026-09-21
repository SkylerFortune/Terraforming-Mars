from dataclasses import dataclass

from classes.requirement import Requirement
from game_manager import Reward

@dataclass
class Card:
    name: str
    description: str
    type: str
    tags: list[str]
    cost: int
    requirements: list[Requirement]
    reward: Reward

    def get_tags(self, tag: str) -> int:
        return self.tags.count(tag)