from classes.player import Player
from classes.tile import Tile
from game_manager import Reward

class Board:
    def __init__(self, ocean_locations: list[tuple[int, int, int]], volcano_locations: list[tuple[int, int, int]]) -> None:
        self.ocean_locations = ocean_locations
        self.volcano_locations = volcano_locations
        self.tiles: list[Tile] = []
        self._create_board()
        self.directions = [
            [1, -1, 0],
            [1, 0, -1],
            [0, 1, -1],
            [-1, 1, 0],
            [-1, 0, 1],
            [0, -1, 1]
        ]
        self.temp = -32
        self.oceans = 0
        self.venus = 0
        self.oxygen = 0

    def can_place_tile(self, location: tuple[int, int, int], tile_type: str) -> bool:
        #TODO: restrictions and exceptions
        target = self.get_tile_target(location)
        if tile_type == "ocean":
            return target.is_ocean_tile and target.occupied_with is None

        #TODO: efficiency gains by storing possible city state rather than updating every time
        elif tile_type == "city":
            for tile in target.adj_tiles:
                if tile.occupied_with == "city":
                    return False
            return not target.is_ocean_tile and target.occupied_with is None
        elif tile_type == "forest":
            return not target.is_ocean_tile and target.occupied_with is None
        #TODO: special tiles
        elif tile_type == "special":
            pass
        return True

    def place_tile(self, player: Player, tile_type: str, location: tuple[int, int, int]) -> Tile:
        target = self.get_tile_target(location)
        target.occupied_with = tile_type
        reward = self.get_placement_bonus(location)
        if reward:
            player.receive_reward(reward, self)
        target.add_neighbor(self.get_tile_target(location))
        return target

    def get_tile_target(self, position: tuple[int, int, int]) -> Tile:
        return [tile for tile in self.tiles if tile.position == position][0]

    def get_placement_bonus(self, position: tuple[int, int, int]) -> Reward | None:
        return self.get_tile_target(position).placement_bonus

    def get_available_locations(self) -> list[tuple[int, int, int]]:
        return [tile.position for tile in self.tiles if tile.occupied_with is None]

    def get_adjacent(self, tile: Tile) -> list[Tile]:
        return [tile for tile in tile.adj_tiles if tile.occupied_with is not None]

    def available_locations_by_type(self, tile_type: str) -> list[tuple[int, int, int]]:
        if tile_type == "city":
            available_locations = []
            for tile in self.tiles:
                if [tile for tile in tile.adj_tiles if tile.occupied_with == "city"] == []:
                    available_locations.append(tile.position)
            return available_locations
        elif tile_type == "forest":
            return [tile.position for tile in self.tiles if not tile.is_ocean_tile and tile.occupied_with is None]
        elif tile_type == "ocean":
            return [tile.position for tile in self.tiles if tile.is_ocean_tile and tile.occupied_with is None]
        elif tile_type == "volcano":
            return [tile.position for tile in self.tiles if tile.is_volcano and tile.occupied_with is None]
        return []

    def _create_board(self) -> None:
        center = (0, 0, 0)
    
        seed_tile = Tile(position=center, is_ocean_tile=False, reserved_by_player=None, occupied_with="test", placement_bonus=None, owner=None)
        self.tiles.append(seed_tile)
    
        self._create_all_tiles(seed_tile, self.tiles)

    def _create_all_tiles(self, center_tile: Tile, tiles: list[Tile]) -> None:
        directions = [(+1, -1, 0),
                           (+1, 0, -1),
                           (0, +1, -1),
                           (-1, +1, 0),
                           (-1, 0, +1),
                           (0, -1, +1)]
        
        def create_ring_tiles(center_tile: Tile):
            #TODO: add adj_tiles on creations
            for direction in directions:
                #if tile already exists
                for tile in tiles:
                    if (direction[0] + center_tile.position[0], direction[1] + center_tile.position[1], direction[2] + center_tile.position[2]) == (tile.position[0], tile.position[1], tile.position[2]):
                        break
                else: # else create new tile in that direction
                    new_p = center_tile.position[0] + direction[0]
                    new_q = center_tile.position[1] + direction[1]
                    new_s = center_tile.position[2] + direction[2]

                    new_location = (new_p, new_q, new_s)
                    is_ocean_tile = self.get_tile_target(new_location).is_ocean_tile

                    new_tile = Tile(position=new_location, is_ocean_tile=is_ocean_tile, reserved_by_player=None, occupied_with=None, placement_bonus=None, owner=None)
                    
                    tiles.append(new_tile)

        def assign_tiles(locations: list[tuple[int, int, int]], tile_type: str):
            for location in locations:
                tile = self.get_tile_target(location)
                if tile:
                    tile.occupied_with = tile_type

        create_ring_tiles(center_tile)
        
        #second ring
        first_ring: list[Tile] = tiles[1:7]
        for tile in first_ring:
            create_ring_tiles(tile)

        #third ring
        second_ring: list[Tile] = tiles[7:19]
        for tile in second_ring:
            create_ring_tiles(tile)

        #fourth ring
        third_ring: list[Tile] = tiles[19:37]
        for tile in third_ring:
            create_ring_tiles(tile)

        assign_tiles(self.ocean_locations, "ocean")
        assign_tiles(self.volcano_locations, "volcano")


            
