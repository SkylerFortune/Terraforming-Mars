from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from classes.board import Board
from classes.helper.requirement import Requirement
from classes.helper.resources import Resources
from classes.helper.reward import Reward
class Card:
    """name: str
    description: str
    type: str
    tags: list[str]
    cost: int
    requirements: list[Requirement]
    reward: Reward
    resources: Resources
    points_func: Callable[[Board], int]"""

    def __init__(self, data: dict) -> None:
        self._parse_card_info(data)

    # TODO: implement
    def _parse_card_info(self, data: dict) -> None:
        self._set_defaults()
        """self.name = data.get("name", "")
        self.description = data.get("description", "")
        self.type = data.get("type", "")
        self.tags = data.get("tags", [])
        self.cost = data.get("cost", 0)
        self.requirements = [Requirement(**req) for req in data.get("requirements", [])]
        self.reward = Reward(**data.get("reward", {}))
        self.resources = Resources(**data.get("resources", {}))
        self.points_func = data.get("points_func", lambda board: 0)"""

    def _set_defaults(self) -> None:
        self.name = ""
        self.description = ""
        self.type = ""
        self.tags = []
        self.cost = 0
        self.requirements = []
        self.reward = Reward()
        self.resources = Resources()
        self.points_func = lambda board: 0

    def resolve_points(self, board: Board) -> int:
        return self.points_func(board)

    def get_tags(self, tag: str) -> int:
        return self.tags.count(tag)
