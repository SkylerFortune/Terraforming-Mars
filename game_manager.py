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
from classes.helper.action import Action
from classes.helper.constants import Constants


class GameManager:
    def __init__(self, players: list[Player], ocean_locations: list[tuple[int, int, int]], volcano_locations: list[tuple[int, int, int]], expansions: list[str], settings: dict[str, Any]) -> None:

        self.expansions = expansions
        self.constants = Constants(**settings.get("self.constants", {}))
        self.game_state = GameState(players, ocean_locations=ocean_locations, volcano_locations=volcano_locations, expansions=expansions, settings=settings, constants=self.constants)

    ## --- GAME FLOW --- ##
    def production(self):
        for player in self.game_state.players:
            self.give_cards(player, self.constants.GIVEN_CARDS)
            player.produce()

    def resolve_current_player_turn(self):
        current_player = self.game_state.current_player
        actions = self.get_legal_actions(self.game_state)
        if actions:
            chosen_action = current_player.interface.choose_action(actions)
            self.resolve_action(chosen_action)

    def resolve_action(self, action: Action):
        #TODO: Implement action resolution logic
        if action.action_type == "raise_temp":
            self.game_stat

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
        # needs to meet requirements
        for requirement in card.requirements:
            if not requirement.is_met(game_state, player):
                return False
        return True

    def get_placement_bonus(self, position: tuple[int, int, int]) -> Reward | None:
        return self.game_state.board.get_tile_target(position).placement_bonus

    def can_raise_temp(self, game_state: GameState) -> bool:
        if game_state.board.temp < self.constants.MAX_TEMP:
            return True
        return False

    def raise_temp(self, game_state: GameState) -> GameState:
        new_state = copy.deepcopy(game_state)
        new_state.board.temp += 1
        return new_state

    def can_raise_oxygen(self, game_state: GameState) -> bool:
        if game_state.board.oxygen < self.constants.MAX_OX:
            return True
        return False

    def raise_oxygen(self, game_state: GameState, player: Player) -> GameState:
        if self.can_raise_oxygen(game_state):
            new_state = copy.deepcopy(game_state)
            new_state.board.oxygen += 1
            return new_state
        return game_state

    def can_raise_venus(self, game_state: GameState) -> bool:
        if game_state.board.venus < self.constants.MAX_VENUS:
            return True
        return False

    def raise_venus(self, game_state: GameState) -> GameState:
        if self.can_raise_venus(game_state):
            new_state = copy.deepcopy(game_state)
            new_state.board.venus += 1
            return new_state
        return game_state

    def can_trade(self, game_state: GameState, player: Player) -> bool:
        return player.available_fleets > 0 and (player.has_resource("money", self.constants.TRADE_COST_MONEY) or player.has_resource("energy", self.constants.TRADE_COST_ENERGY) or player.has_resource("titanium", self.constants.TRADE_COST_TITANIUM))

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
        return (len(player.colonies) < self.constants.MAX_COLONIES) and (planet_name in [planet.name for planet in self.game_state.planets if planet.name == planet_name])

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
        return milestone_name in self.game_state.milestones and player.has_resource("money", self.constants.MILESTONE_COST) and (self.get_num_funded_milestones() < self.constants.MAX_FUNDABLE_MILESTONES)

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
        if num_funded_awards < self.constants.MAX_FUNDABLE_AWARDS:
            return award_name in self.game_state.awards and player.has_resource("money", self.constants.AWARD_COSTS[num_funded_awards])
        return False

    def fund_award(self, game_state: GameState, player: Player, award_name: str) -> GameState:
        if award_name in self.game_state.awards:
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
        return player.has_resource("money", self.constants.POWER_PLANT_COST)

    def power_plant(self, game_state: GameState, player: Player) -> GameState:
        if self.can_buy_power_plant(game_state, player):
            new_state = copy.deepcopy(game_state)
            new_state.players[game_state.players.index(player)].spend("money", self.constants.POWER_PLANT_COST)
            new_state.players[game_state.players.index(player)].receive_reward(Reward(production=Production(energy=1)))
            return new_state
        return game_state

    def can_buy_asteroid(self, game_state: GameState, player: Player) -> bool:
        return player.has_resource("money", self.constants.ASTEROID_COST)

    def asteroid(self, game_state: GameState, player: Player) -> GameState:
        if self.can_buy_asteroid(game_state, player):
            new_state = copy.deepcopy(game_state)
            new_state.players[game_state.players.index(player)].spend("money", self.constants.ASTEROID_COST)
            new_state.players[game_state.players.index(player)].increase_terraform_rating(1)
            return new_state
        return game_state

    def can_buy_aquifer(self, game_state: GameState, player: Player) -> bool:
        return player.has_resource("money", self.constants.AQUIFER_COST)

    def aquifer(self, game_state: GameState, player: Player) -> GameState:
        if self.can_buy_aquifer(game_state, player):
            new_state = copy.deepcopy(game_state)
            player_idx = game_state.players.index(player)
            new_state.players[player_idx].spend("money", self.constants.AQUIFER_COST)
            location = new_state.players[player_idx].place_tile(new_state.board, "ocean")
            new_state.board.place_tile(new_state.players[player_idx], "oceans", location)
            new_state.players[player_idx].increase_terraform_rating(1)
            return new_state
        return game_state

    def can_place_greenery(self, game_state: GameState, player: Player) -> bool:
        return player.has_resource("money", self.constants.GREENERY_COST)

    def greenery(self, game_state: GameState, player: Player) -> GameState:
        if self.can_place_greenery(game_state, player):
            new_state = copy.deepcopy(game_state)
            player_idx = game_state.players.index(player)
            new_state.players[player_idx].spend("money", self.constants.GREENERY_COST)
            location = new_state.players[player_idx].place_tile(new_state.board, "greenery")
            new_state.board.place_tile(new_state.players[player_idx], "greenery", location)
            new_state = self.raise_oxygen(new_state, new_state.players[player_idx])
            return new_state
        return game_state

    def can_place_city(self, game_state: GameState, player: Player) -> bool:
        return player.has_resource("money", self.constants.CITY_COST) and (game_state.board.available_locations_by_type("city") != [])

    def city(self, game_state: GameState, player: Player) -> GameState:
        if self.can_place_city(game_state, player):
            new_state = copy.deepcopy(game_state)
            player_idx = game_state.players.index(player)
            new_state.players[player_idx].spend("money", self.constants.CITY_COST)
            location = new_state.players[player_idx].place_tile(new_state.board, "city")
            new_state.board.place_tile(new_state.players[player_idx], "city", location)
            new_state.players[player_idx].receive_reward(self.constants.CITY_REWARD)
            return new_state
        return game_state

    def is_game_over(self) -> bool:
        if (self.game_state.board.oxygen == self.constants.MAX_OX and
            self.game_state.board.temp == self.constants.MAX_TEMP and
            self.game_state.board.oceans == self.constants.NUM_OCEANS):
            return True
        return False

    def calculate_award(self, award: str) -> int:
        #TODO: implement
        return self.constants.AWARD_FIRST_PLACE

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
        for milestone in self.game_state.milestones:
            if self.can_fund_milestone(game_state, current_player, milestone):
                actions.append(Action("fund_milestone", current_player.id, {"milestone_name": milestone}))
        
        # Fund awards
        for award in self.game_state.awards:
            if self.can_fund_award(game_state, current_player, award):
                actions.append(Action("fund_award", current_player.id, {"award_name": award}))
        
        # Sell patents
        if self.can_sell_patents(game_state, current_player):
            # Generate all subsets of sellable cards
            from itertools import combinations
            for i in range(1, len(current_player.cards) + 1):
                for card_combo in combinations(current_player.cards, i):
                    actions.append(Action("sell_patents", current_player.id, {"card_names": [c.name for c in card_combo]}))
        
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