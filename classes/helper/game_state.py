import random
from typing import Any

from classes.board import Board
from classes.card import Card
from classes.helper.constants import Constants
from classes.helper.resources import Resources
from classes.helper.reward import Reward
from classes.planet import Planet
from classes.player import Player


class GameState:
    def __init__(self, players: list[Player], ocean_locations: list[tuple[int, int, int]], volcano_locations: list[tuple[int, int, int]], expansions: list[str], settings: dict[str, Any], constants: Constants) -> None:
        self.board = Board(ocean_locations=ocean_locations, volcano_locations=volcano_locations)
        self.settings = settings
        self.expansions = expansions
        self.constants = constants
        self.draw_pile: list[Card] = self._init_draw_pile()
        self.discard_pile: list[Card] = []
        self.available_prelude_cards: list[Card] = self._init_preludes()
        self.available_corp_cards: list[Card] = self._init_corps()
        self.planets = self._init_planets(planet_data=self.settings.get("planets", {}))
        self.awards = self._init_awards()
        self.milestones = self._init_milestones()
        self.players: list[Player] = players
        self.first_player: Player = random.sample(self.players, 1)[0]
        self.current_player: Player = self.first_player
        self.generation_over: bool = False

    def next_player(self):
        current_index = self.players.index(self.current_player)
        return self.players[(current_index + 1) % len(self.players)]

    def draw_preludes(self, num_preludes: int) -> list[Card]:
        preludes = []
        for _ in range(num_preludes):
            if self.available_prelude_cards:
                preludes.append(self.available_prelude_cards.pop())
        return preludes

    def draw_corps(self, num_corps: int) -> list[Card]:
        corps = []
        for _ in range(num_corps):
            if self.available_corp_cards:
                corps.append(self.available_corp_cards.pop())
        return corps

    def draw_cards(self, num_cards: int) -> list[Card]:
        cards = []
        for _ in range(num_cards):
            if self.draw_pile:
                cards.append(self.draw_pile.pop())
            else:
                # If the draw pile is empty, shuffle the discard pile and use it as the new draw pile
                self.draw_pile = random.sample(self.discard_pile, len(self.discard_pile))
                self.discard_pile = []
                if self.draw_pile:
                    cards.append(self.draw_pile.pop())
        return cards

    def get_planet(self, planet_name: str) -> Planet:
        for planet in self.planets:
            if planet.name == planet_name:
                return planet
        raise ValueError("Planet not found")

    def get_other_players(self, player: 'Player') -> list['Player']:
        return [p for p in self.players if p != player]

    def get_temp_reward(self, temp: int) -> Reward:
        return self.constants.TEMP_REWARDS.get(temp, Reward())

    def get_oxygen_reward(self, oxygen: int) -> Reward:
        return self.constants.OX_REWARDS.get(oxygen, Reward())

    def get_venus_reward(self, venus: int) -> Reward:
        return self.constants.VENUS_REWARDS.get(venus, Reward())
    ## --- INIT --- ##

    def generate_awards(self) -> list[str]:
        # Generate a list of available awards
        return ["Award 1", "Award 2", "Award 3"]

    def generate_milestones(self) -> list[str]:
        # Generate a list of available milestones
        return ["Milestone 1", "Milestone 2", "Milestone 3"]

    def _init_planets(self, planet_data: dict[str, Any]) -> list[Planet]:
        # Generate a list of planets for the game
        """
        ceres = Planet("Ceres", placement_bonus=Reward(production=Production(steel=1)), colony_bonus=Reward(resources=Resources(steel=1)), track_values=[1, 2, 3, 4, 6, 8, 10], resource="steel")
        enceladus = Planet("Enceladus", placement_bonus=Reward(resources=Resources(microbes=3)), colony_bonus=Reward(resources=Resources(microbes=1)), track_values=[0, 1, 2, 3, 4, 4, 5], resource="microbes")
        europa = Planet("Europa", placement_bonus=Reward(ocean=1), colony_bonus=Reward(resources=Resources(money=1)), track_values=[0, 1, 2, 3, 4, 5, 6], resource="money")
        titan = Planet("Titan", placement_bonus=Reward(resources=Resources(floaters=3)), colony_bonus=Reward(resources=Resources(floaters=1)), track_values=[0, 1, 1, 2, 3, 3, 4], resource="floaters")
        luna = Planet("luna", placement_bonus=Reward(production=Production(money=2)), colony_bonus=Reward(resources=Resources(money=2)), track_values=[1, 2, 4, 7, 10, 13, 17], resource="money")
        io = Planet("Io", placement_bonus=Reward(production=Production(heat=1)), colony_bonus=Reward(resources=Resources(heat=2)), track_values=[2, 3, 4, 6, 8, 10, 13], resource="heat")
        pluto = Planet("Pluto", placement_bonus=Reward(resources=Resources(cards=2)), colony_bonus=lambda: self.find_pluto_reward(), track_values=[0, 1, 2, 2, 3, 3, 4], resource="cards")
        ganymede = Planet("Ganymede", placement_bonus=Reward(production=Production(plants=1)), colony_bonus=Reward(resources=Resources(plants=1)), track_values=[0, 1, 2, 3, 4, 5, 6], resource="plants")
        callisto = Planet("Callisto", placement_bonus=Reward(production=Production(energy=1)), colony_bonus=Reward(resources=Resources(energy=3)), track_values=[0, 2, 3, 5, 7, 10, 13], resource="energy")
        miranda = Planet("Miranda", placement_bonus=Reward(resources=Resources(animals=1)), colony_bonus=Reward(resources=Resources(cards=1)), track_values=[0, 1, 1, 2, 2, 3, 3], resource="cards")
        triton = Planet ("Triton", placement_bonus=Reward(resources=Resources(titanium=3)), colony_bonus=Reward(resources=Resources(titanium=1)), track_values=[0, 1, 1, 2, 3, 4, 5], resource="titanium")
        """
        if "colonies" not in self.expansions:
            return []
        planet_names = ["Ceres", "Enceladus", "Europa", "Titan", "luna", "Io", "Pluto", "Ganymede", "Callisto", "Miranda", "Triton"]
        planets = []
        for planet_name in planet_names:
            planets.append(
                Planet(
                    planet_name, 
                    placement_bonus=getattr(planet_data, f"{planet_name.lower()}_placement_reward"), 
                    colony_bonus=Reward(
                        resources=Resources(
                            **{getattr(planet_data, f'{planet_name.lower()}_colony_bonus').resources.__dict__[k]: v for k, v in getattr(planet_data, f'{planet_name.lower()}_colony_bonus').resources.__dict__.items() if v > 0})), 
                    track_values=getattr(planet_data, f"{planet_name.lower()}_track_values"),
                    resource=getattr(planet_data, f"{planet_name.lower()}_resource"))
            )
        return random.sample(planets, len(self.players) + self.constants.ADDITIONAL_PLANETS)
    #TODO: implement
    def _init_draw_pile(self) -> list[Card]:
        return []

    #TODO: implement
    def _init_preludes(self) -> list[Card]:
        return []

    #TODO: implement
    def _init_corps(self) -> list[Card]:
        return []

    #TODO: implement
    def _init_awards(self) -> list[str]:
        return []

    #TODO: implement
    def _init_milestones(self) -> list[str]:
        return []