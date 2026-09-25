from classes.player import Player
from game_manager import Reward


class Tile:
    def __init__(self, position: tuple[int, int, int], is_ocean_tile: bool = False, is_volcano: bool = False, reserved_by_player: Player | None = None, occupied_with: str | None = None, placement_bonus: Reward | None = None, owner: Player | None = None) -> None:
        self.occupied_with = occupied_with
        self.placement_bonus = placement_bonus
        self.position = position
        self.is_ocean_tile = is_ocean_tile
        self.is_volcano = is_volcano
        self.reserved_by_player = reserved_by_player
        self.owner = owner
        self.adj_tiles: list[Tile] = []

    def add_neighbor(self, neighbor):
        self.adj_tiles.append(neighbor)
