from collections.abc import Callable
from dataclasses import dataclass

from classes.board import Board
from classes.helper.requirement import Requirement
from classes.helper.resources import Resources
from classes.helper.reward import Reward

@dataclass
class Card:
    name: str
    description: str
    type: str
    tags: list[str]
    cost: int
    requirements: list[Requirement]
    reward: Reward
    resources: Resources
    points_func: Callable[[Board], int]

    def resolve_points(self, board: Board) -> int:
        return self.points_func(board)

    def get_tags(self, tag: str) -> int:
        return self.tags.count(tag)
