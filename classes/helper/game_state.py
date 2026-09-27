import random
from typing import Any

from classes.board import Board
from classes.card import Card
from classes.planet import Planet
from classes.player import Player


class GameState:
    def __init__(self, ocean_locations: list[tuple[int, int, int]], volcano_locations: list[tuple[int, int, int]], expansions: list[str], settings: dict[str, Any]) -> None:
        self.board = Board(ocean_locations=ocean_locations, volcano_locations=volcano_locations)
        self.settings = settings
        self.expansions = expansions
        self.draw_pile: list[Card] = self._init_draw_pile()
        self.discard_pile: list[Card] = []
        self.available_prelude_cards: list[Card] = self._init_preludes()
        self.available_corp_cards: list[Card] = self._init_corps()
        self.players: list[Player] = []
        self.planets = self._init_planets()
        self.awards = self._init_awards()
        self.milestones = self._init_milestones()
        self.first_player: Player
        self.current_player: Player
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

    ## --- INIT --- ##
    #TODO: implement
    def _init_draw_pile(self) -> list[Card]:
        return []

    #TODO: implement
    def _init_preludes(self) -> list[Card]:
        return []

    #TODO: implement
    def _init_corps(self) -> list[Card]:
        return []

    def _init_planets(self) -> list[Planet]:
        if  "colonies" not in self.expansions:
            return []

        return []

    def _init_awards(self) -> list[str]:
        return []

    def _init_milestones(self) -> list[str]:
        return []