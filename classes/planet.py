from typing import Callable, Optional

from classes.player import Player
from classes.tile import Tile
from game_manager import GameState, Reward

class Planet:
    def __init__(self, name: str, placement_bonus: Reward, colony_bonus: Reward | Callable[[], Reward], track_values: list[int] | None, starting_index: int = 1, resource: str | Callable[[], Reward] | None = None) -> None:
        self.name = name
        self.placement_bonus = placement_bonus
        self.colony_bonus = colony_bonus
        self.index = starting_index
        self.track_values = track_values
        self.colonies: list[Player] = [] #list of player refs
        if track_values:
            self.maximum_index = len(track_values)
        else:
            self.maximum_index = 7
        self.resource = resource

    def advance_track(self, game: "GameState") -> None:
        if self.index < self.maximum_index:
            self.index += 1

    def place_colony(self, player: Player) -> None:
        if len(self.colonies) == 3:
            return

        if len(player.colonies) == 3:
            return

        self.colonies.append(player)