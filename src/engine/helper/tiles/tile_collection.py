from dataclasses import dataclass

from engine.helper.tiles.tile import Tile


@dataclass(frozen=True)
class TileCollection:
    cities: list[Tile] = []
    forests: list[Tile] = []
    special: list[Tile] = []
    oceans: list[Tile] = []
    land_claims: list[Tile] = []
    
    def add_tile(self, tile: Tile):
        return TileCollection(
            cities=self.cities + [tile] if tile.occupied_with == "city" else self.cities,
            forests=self.forests + [tile] if tile.occupied_with == "forest" else self.forests,
            special=self.special + [tile] if tile.occupied_with == "special" else self.special,
            oceans=self.oceans + [tile] if tile.occupied_with == "ocean" else self.oceans,
            land_claims=self.land_claims + [tile] if tile.occupied_with == "land_claim" else self.land_claims
        )