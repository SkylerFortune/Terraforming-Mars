from dataclasses import dataclass
import random

from classes.board import Board
from classes.card import Card
from classes.planet import Planet
from classes.tile import Tile
from game_manager import GameState, Resources, Production, Reward
from numpy import tile


class Player:
    def __init__(self, id: int) -> None:
        self.id = id
        self.corp: Card | None = None
        self.possible_corps: list[Card] = []
        self.preludes: list[Card] | None = None
        self.possible_preludes: list[Card] = []
        self.cards_to_buy: list[Card] = []
        self.passed = False
        self.tiles = TileCollection()
        self.production = Production()
        self.resources = Resources()
        self.colonies: list[Planet] = []
        self.cards: list[Card] = []
        self.played_cards: list[Card] = []
        self.terraform_rating = 20
        self.trade_fleets = 1
        self.available_fleets = 1
        self.milestones: list[str] = []
        self.awards: list[str] = []

    def produce(self):
        self.resources.money += self.production.money + self.terraform_rating
        self.resources.steel += self.production.steel
        self.resources.titanium += self.production.titanium
        self.resources.plants += self.production.plants
        self.resources.heat += self.production.heat + self.resources.energy
        self.resources.energy = self.production.energy

        self.reset_fleets()

    def play_card(self, card: Card, board: "Board"):
        self.played_cards.append(card)
        if card.reward:
            self.receive_reward(card.reward, board)

    def receive_reward(self, reward: Reward, board: "Board" | None = None):
        if reward.production:
            self.production.money += reward.production.money
            self.production.steel += reward.production.steel
            self.production.titanium += reward.production.titanium
            self.production.plants += reward.production.plants
            self.production.heat += reward.production.heat
            self.production.energy += reward.production.energy

        if reward.resources:
            self.resources.money += reward.resources.money
            self.resources.steel += reward.resources.steel
            self.resources.titanium += reward.resources.titanium
            self.resources.plants += reward.resources.plants
            self.resources.heat += reward.resources.heat
            self.resources.energy += reward.resources.energy

        if reward.tile:
            self.place_tile(board, reward.tile)

    def increase_terraform_rating(self, amount: int) -> None:
        self.terraform_rating += amount

    def has_resource(self, resource: str, amount: int) -> bool:
        return getattr(self.resources, resource) >= amount

    def spend(self, resource: str, amount: int) -> None:
        if self.has_resource(resource, amount):
            setattr(self.resources, resource, getattr(self.resources, resource) - amount)
        else:
            raise ValueError("Not enough resources")

    def has_production(self, resource: str, amount: int) -> bool:
        return getattr(self.production, resource) >= amount

    def place_tile(self, board: "Board", tile_type: str) -> tuple[int, int, int]:
        possible_locations = board.get_available_locations()
        return random.choice(possible_locations)

    def add_tile(self, tile: Tile):
        self.tiles.add_tile(tile)

    def gain_cards(self, cards: list[Card]):
        #TODO: account for corps and preludes
        self.cards_to_buy = cards
        self.resolve_cards_to_buy()

    def resolve_cards_to_buy(self):
        #TODO: logic for picking a card to buy
        pass

    def reset_fleets(self):
        self.available_fleets = self.trade_fleets

    def calculate_points(self):
        pass

    def get_tags(self, tag: str) -> int:
        count = 0
        for card in self.played_cards:
            count += card.get_tags(tag)
        return count

    def get_card_by_type(self, card_type: str) -> list[Card]:
        return [card for card in self.cards if card.type == card_type]


@dataclass
class TileCollection:
    cities: list[Tile] = []
    forests: list[Tile] = []
    special: list[Tile] = []
    oceans: list[Tile] = []
    land_claims: list[Tile] = []

    def add_tile(self, tile: Tile):
        if tile.occupied_with == "city":
            self.cities.append(tile)
        elif tile.occupied_with == "forest":
            self.forests.append(tile)
        elif tile.occupied_with == "special":
            self.special.append(tile)
        elif tile.occupied_with == "ocean":
            self.oceans.append(tile)
        elif tile.occupied_with == "land_claim":
            self.land_claims.append(tile)