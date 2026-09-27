import copy
from dataclasses import dataclass
import random
from typing import Any

from classes.board import Board
from classes.card import Card
from classes.planet import Planet
from classes.player import Player
from classes.tile import Tile
from classes.helper.game_state import GameState
from classes.helper.production import Production
from classes.helper.requirement import Requirement
from classes.helper.reward import Reward
from classes.helper.resources import Resources
from classes.helper.constants import Constants


class GameManager:
    def __init__(self, ocean_locations: list[tuple[int, int, int]], volcano_locations: list[tuple[int, int, int]], expansions: list[str], settings: dict[str, Any]) -> None:

        self.expansions = expansions
        self.game_state = GameState(ocean_locations=ocean_locations, volcano_locations=volcano_locations, expansions=expansions, settings=settings)

        self.milestones = self.generate_milestones()
        self.awards = self.generate_awards()

        self._override_variables(settings)

    ## --- GAME FLOW --- ##
    def production(self):
        for player in self.game_state.players:
            self.give_cards(player, Constants.STARTING_CARDS)
            player.produce()
            #TODO: choose which cards

    def resolve_current_player_turn(self):
        current_player = self.game_state.current_player
        #TODO: Resolve logic

    ## --- GAME FUNCTIONS
    def give_cards(self, player: Player, num_cards: int) -> None:
        cards = self.game_state.draw_cards(num_cards)
        player.gain_cards(cards)

    def find_europa_reward(self) -> Reward:
        # Find the reward for Europa based on the current game state
        europa = next((p for p in self.game_state.planets if p.name == "Europa"), None)
        if europa:
            match europa.index + 1:
                case 1, 2:
                    return Reward(production=Production(steel=1))
                case 3, 4:
                    return Reward(production=Production(energy=1))
                case 5, 6, 7:
                    return Reward(production=Production(plants=1))
        return Reward()

    def find_pluto_reward(self) -> Reward:
        #TODO: Find the reward for Pluto based on the current game state
        return Reward(resources=Resources(steel=1))

    def place_tile(self, player: Player, tile_type: str, location: tuple[int, int, int]) -> None:
        self.game_state.board.place_tile(player, tile_type, location)
        placement_bonus = self.get_placement_bonus(location)
        if placement_bonus:
            player.receive_reward(placement_bonus, self.game_state.board)

    #TODO: implement
    def can_play_card(self, game_state: GameState, player: Player, card: Card) -> bool:
        return True

    def get_placement_bonus(self, position: tuple[int, int, int]) -> Reward | None:
        return self.game_state.board.get_tile_target(position).placement_bonus

    def can_raise_temp(self, game_state: GameState) -> bool:
        if game_state.board.temp < Constants.MAX_TEMP:
            return True
        return False

    def raise_temp(self, game_state: GameState) -> GameState:
        new_state = copy.deepcopy(game_state)
        new_state.board.temp += 1
        return new_state

    def can_raise_oxygen(self, game_state: GameState) -> bool:
        if game_state.board.oxygen < Constants.MAX_OX:
            return True
        return False

    def raise_oxygen(self, game_state: GameState, player: Player) -> GameState:
        if self.can_raise_oxygen(game_state):
            new_state = copy.deepcopy(game_state)
            new_state.board.oxygen += 1
            return new_state
        return game_state

    def can_raise_venus(self, game_state: GameState) -> bool:
        if game_state.board.venus < Constants.MAX_VENUS:
            return True
        return False

    def raise_venus(self, game_state: GameState) -> GameState:
        if self.can_raise_venus(game_state):
            new_state = copy.deepcopy(game_state)
            new_state.board.venus += 1
            return new_state
        return game_state

    def can_trade(self, game_state: GameState, player: Player) -> bool:
        return player.available_fleets > 0 and (player.has_resource("money", Constants.TRADE_COST_MONEY) or player.has_resource("energy", Constants.TRADE_COST_ENERGY) or player.has_resource("titanium", Constants.TRADE_COST_TITANIUM))

    def trade(self, game_state: GameState, player: Player, target: str) -> GameState:
        if self.can_trade(game_state, player):
            new_state = copy.deepcopy(game_state)
            new_state.players[game_state.players.index(player)].available_fleets -= 1
            return self.resolve_trade(new_state, player, target)
        return game_state

    #TODO: add trading logic per planet
    def resolve_trade(self, game_state: GameState, player: Player, target: str) -> GameState:
        new_state = copy.deepcopy(game_state)
        if target == "enceladus":
            pass
        elif target == "ceres":
            pass
        elif target == "triton":
            pass
        elif target == "pluto":
            pass
        elif target == "eris":
            pass
        elif target == "europa":
            pass
        elif target == "titan":
            pass
        elif target == "luna":
            pass
        elif target == "ganymede":
            pass
        elif target == "callisto":
            pass
        elif target == "miranda":
            pass
        else:
            raise ValueError("Invalid target")
        return new_state

    #TODO: add card playing logic
    def play_card(self, game_state: GameState, player: Player, card: Card) -> GameState:
        new_state = copy.deepcopy(game_state)
        new_state.players[game_state.players.index(player)].play_card(card, new_state.board)
        return new_state

    ## --- STANDARD ACTIONS --- ##
    def can_place_colony(self, game_state: GameState, player: Player, planet_name: str) -> bool:
        return (len(player.colonies) < Constants.MAX_COLONIES) and (planet_name in [planet.name for planet in self.game_state.planets if planet.name == planet_name])

    def place_colony(self, game_state: GameState, player: Player, planet_name: str) -> GameState:
        if self.can_place_colony(game_state, player, planet_name):
            new_state = copy.deepcopy(game_state)
            new_state.players[game_state.players.index(player)].colonies.append(new_state.get_planet(planet_name))
            return new_state
        return game_state

    #milestones
    def get_num_funded_milestones(self):
        return sum([len(player.milestones) for player in self.game_state.players])

    def can_fund_milestone(self, game_state: GameState, player: Player, milestone_name: str) -> bool:
        return milestone_name in self.milestones and player.has_resource("money", Constants.MILESTONE_COST) and (self.get_num_funded_milestones() < Constants.MAX_FUNDABLE_MILESTONES)

    def fund_milestone(self, game_state: GameState, player: Player, milestone_name: str) -> GameState:
        if self.can_fund_milestone(game_state, player, milestone_name):
            new_state = copy.deepcopy(game_state)
            new_state.players[game_state.players.index(player)].milestones.append(milestone_name)
            return new_state
        return game_state

    #awards
    def get_num_funded_awards(self):
        return sum([len(player.awards) for player in self.game_state.players])

    def can_fund_award(self, game_state: GameState, player: Player, award_name: str) -> bool:
        num_funded_awards = self.get_num_funded_awards()
        if num_funded_awards < Constants.MAX_FUNDABLE_AWARDS:
            return award_name in self.awards and player.has_resource("money", Constants.AWARD_COSTS[num_funded_awards])
        return False

    def fund_award(self, game_state: GameState, player: Player, award_name: str) -> GameState:
        if award_name in self.awards:
            new_state = copy.deepcopy(game_state)
            new_state.players[game_state.players.index(player)].awards.append(award_name)
            return new_state
        return game_state

    def can_sell_patents(self, game_state: GameState, player: Player) -> bool:
        return len(player.cards) > 0

    def sell_patents(self, game_state: GameState, cards: list[Card], player: Player) -> GameState:
        new_state = copy.deepcopy(game_state)
        player_idx = game_state.players.index(player)
        count = 0
        for card in cards:
            if card in new_state.players[player_idx].cards:
                new_state.players[player_idx].cards.remove(card)
                count += 1
        new_state.players[player_idx].resources.money += count
        return new_state

    def can_buy_power_plant(self, game_state: GameState, player: Player) -> bool:
        return player.has_resource("money", Constants.POWER_PLANT_COST)

    def power_plant(self, game_state: GameState, player: Player) -> GameState:
        if self.can_buy_power_plant(game_state, player):
            new_state = copy.deepcopy(game_state)
            new_state.players[game_state.players.index(player)].spend("money", Constants.POWER_PLANT_COST)
            new_state.players[game_state.players.index(player)].receive_reward(Reward(production=Production(energy=1)))
            return new_state
        return game_state

    def can_buy_asteroid(self, game_state: GameState, player: Player) -> bool:
        return player.has_resource("money", Constants.ASTEROID_COST)

    def asteroid(self, game_state: GameState, player: Player) -> GameState:
        if self.can_buy_asteroid(game_state, player):
            new_state = copy.deepcopy(game_state)
            new_state.players[game_state.players.index(player)].spend("money", Constants.ASTEROID_COST)
            new_state.players[game_state.players.index(player)].increase_terraform_rating(1)
            return new_state
        return game_state

    def can_buy_aquifer(self, game_state: GameState, player: Player) -> bool:
        return player.has_resource("money", Constants.AQUIFER_COST)

    def aquifer(self, game_state: GameState, player: Player) -> GameState:
        if self.can_buy_aquifer(game_state, player):
            new_state = copy.deepcopy(game_state)
            player_idx = game_state.players.index(player)
            new_state.players[player_idx].spend("money", Constants.AQUIFER_COST)
            location = new_state.players[player_idx].place_tile(new_state.board, "ocean")
            new_state.board.place_tile(new_state.players[player_idx], "oceans", location)
            new_state.players[player_idx].increase_terraform_rating(1)
            return new_state
        return game_state

    def can_place_greenery(self, game_state: GameState, player: Player) -> bool:
        return player.has_resource("money", Constants.GREENERY_COST)

    def greenery(self, game_state: GameState, player: Player) -> GameState:
        if self.can_place_greenery(game_state, player):
            new_state = copy.deepcopy(game_state)
            player_idx = game_state.players.index(player)
            new_state.players[player_idx].spend("money", Constants.GREENERY_COST)
            location = new_state.players[player_idx].place_tile(new_state.board, "greenery")
            new_state.board.place_tile(new_state.players[player_idx], "greenery", location)
            new_state = self.raise_oxygen(new_state, new_state.players[player_idx])
            return new_state
        return game_state

    def can_place_city(self, game_state: GameState, player: Player) -> bool:
        return player.has_resource("money", Constants.CITY_COST) and (game_state.board.available_locations_by_type("city") != [])

    def city(self, game_state: GameState, player: Player) -> GameState:
        if self.can_place_city(game_state, player):
            new_state = copy.deepcopy(game_state)
            player_idx = game_state.players.index(player)
            new_state.players[player_idx].spend("money", Constants.CITY_COST)
            location = new_state.players[player_idx].place_tile(new_state.board, "city")
            new_state.board.place_tile(new_state.players[player_idx], "city", location)
            new_state.players[player_idx].receive_reward(Constants.CITY_REWARD)
            return new_state
        return game_state

    def is_game_over(self) -> bool:
        if (self.game_state.board.oxygen == Constants.MAX_OX and
            self.game_state.board.temp == Constants.MAX_TEMP and
            self.game_state.board.oceans == Constants.NUM_OCEANS):
            return True
        return False

    def calculate_award(self, award: str) -> int:
        #TODO: implement
        return Constants.AWARD_FIRST_PLACE

    def calculate_points(self, player: Player) -> int:
        points = 0
        #points from awards
        for award in player.awards:
            points += self.calculate_award(award)
        #points from milestones
        for milestone in player.milestones:
            points += 5
        #points from greeneries
        points += len(player.tiles.forests)
        #points from cities
        for city in player.tiles.cities:
            for adj in self.game_state.board.get_adjacent(city):
                if adj.occupied_with == "greenery":
                    points += 1
        #points from cards
        for card in player.cards:
            points += card.resolve_points(self.game_state.board)

        return points

    def get_legal_actions(self, game_state: GameState) -> list[Action]:
        """Returns all legal actions for the current player in the given game state."""
        actions = []
        current_player = game_state.current_player
        
        # Raise oxygen
        if self.can_raise_oxygen(game_state):
            actions.append(Action("raise_oxygen", current_player.id, {}))
        
        # Raise temperature
        if self.can_raise_temp(game_state):
            actions.append(Action("raise_temp", current_player.id, {}))
        
        # Raise venus
        if self.can_raise_venus(game_state):
            actions.append(Action("raise_venus", current_player.id, {}))
        
        # Play cards
        for card in current_player.cards:
            if self.can_play_card(game_state, current_player, card):
                actions.append(Action("play_card", current_player.id, {"card_name": card.name}))
        
        # Place colonies
        for planet in game_state.planets:
            if self.can_place_colony(game_state, current_player, planet.name):
                actions.append(Action("place_colony", current_player.id, {"planet_name": planet.name}))
        
        # Fund milestones
        for milestone in self.milestones:
            if self.can_fund_milestone(game_state, current_player, milestone):
                actions.append(Action("fund_milestone", current_player.id, {"milestone_name": milestone}))
        
        # Fund awards
        for award in self.awards:
            if self.can_fund_award(game_state, current_player, award):
                actions.append(Action("fund_award", current_player.id, {"award_name": award}))
        
        # Sell patents
        if self.can_sell_patents(game_state, current_player):
            # Generate all subsets of sellable cards
            from itertools import combinations
            for i in range(1, len(current_player.cards) + 1):
                for card_combo in combinations(current_player.cards, i):
                    actions.append(Action("sell_patents", current_player.id, {"card_ids": [c.id for c in card_combo]}))
        
        # Buy power plant
        if self.can_buy_power_plant(game_state, current_player):
            actions.append(Action("power_plant", current_player.id, {}))
        
        # Buy asteroid
        if self.can_buy_asteroid(game_state, current_player):
            actions.append(Action("asteroid", current_player.id, {}))
        
        # Buy aquifer
        if self.can_buy_aquifer(game_state, current_player):
            actions.append(Action("aquifer", current_player.id, {}))
        
        # Place greenery
        if self.can_place_greenery(game_state, current_player):
            actions.append(Action("greenery", current_player.id, {}))
        
        # Place city
        if self.can_place_city(game_state, current_player):
            actions.append(Action("city", current_player.id, {}))
        
        # Trade (for each available planet)
        for planet in game_state.planets:
            if self.can_trade(game_state, current_player):
                actions.append(Action("trade", current_player.id, {"target": planet.name}))
        
        return actions

    ## --- INIT --- ##

    def _override_variables(self, settings: dict[str, Any]):
        for key, value in settings.get("variable_overrides", {}).items():
            if hasattr(self, key):
                setattr(self, key, value)

    def generate_awards(self) -> list[str]:
        # Generate a list of available awards
        return ["Award 1", "Award 2", "Award 3"]

    def generate_milestones(self) -> list[str]:
        # Generate a list of available milestones
        return ["Milestone 1", "Milestone 2", "Milestone 3"]

    def generate_planets(self) -> list[Planet]:
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
        planet_names = ["Ceres", "Enceladus", "Europa", "Titan", "luna", "Io", "Pluto", "Ganymede", "Callisto", "Miranda", "Triton"]
        planets = []
        for planet_name in planet_names:
            planets.append(
                Planet(
                    planet_name, 
                    placement_bonus=getattr(self, f"{planet_name.lower()}_placement_reward"), 
                    colony_bonus=Reward(
                        resources=Resources(
                            **{getattr(self, f'{planet_name.lower()}_colony_bonus').resources.__dict__[k]: v for k, v in getattr(self, f'{planet_name.lower()}_colony_bonus').resources.__dict__.items() if v > 0})), 
                    track_values=getattr(self, f"{planet_name.lower()}_track_values"),
                    resource=getattr(self, f"{planet_name.lower()}_resource"))
            )
        return random.sample(planets, len(self.game_state.players) + self.additional_planets)

@dataclass
class Action:
    """Represents a game action that can be taken by a player."""
    action_type: str  # "raise_oxygen", "raise_temp", "play_card", "place_colony", etc.
    player_id: int
    params: dict  # Contains action-specific parameters
    
    def __hash__(self):
        return hash((self.action_type, self.player_id, tuple(sorted(self.params.items()))))
    
    def __eq__(self, other):
        if not isinstance(other, Action):
            return False
        return (self.action_type == other.action_type and 
                self.player_id == other.player_id and 
                self.params == other.params)