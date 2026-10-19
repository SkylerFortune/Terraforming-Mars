import copy
from dataclasses import dataclass
import random
from typing import Any

from engine.helper.awards import awards
from engine.helper.player.list_players import ListPlayers
from engine.helper.tracks.oceans_track import OceansTrack
from engine.helper.tracks.oxygen_track import OxygenTrack
from engine.helper.tracks.temperature_track import TemperatureTrack
from engine.helper.tracks.venus_track import VenusTrack
from numpy import var
from engine.helper.board import Board
from engine.helper.cards.card_def import CardDef
from engine.helper.planet import Planet
from engine.helper.tiles.tile import Tile
from engine.game_state import GameState
from engine.helper.cards.requirement import Requirement
from engine.helper.cards.reward import Reward
from engine.old.classes.helper.action import Action
from engine.constants import Constants

from engine.primitives import *


class GameManager:
    def __init__(self, players: list[Player], board: Board, expansions: list[str], settings: dict[str, Any]) -> None:

        self.expansions = expansions
        self.constants = Constants(**settings.get("constants", {}))

        self.game_state = GameState(
            board=board,
            card_manager=CardManager(expansions=expansions),
            players=ListPlayers(players),
            first_player_id=random.sample(players, 1)[0].id,
            current_player_id=random.sample(players, 1)[0].id,
            generation=1,
            planets=self._init_planets(expansions),
            awards_object=self._init_awards(expansions),
            milestones_object=self._init_milestones(expansions),
            temperature_track=TemperatureTrack(),
            oxygen_track=OxygenTrack(),
            venus_track=VenusTrack(),
            oceans_placed=OceansTrack(),
            pending=None
        )

    ## --- GAME FLOW --- ##
    def production(self):
        for player in game_state.players:
            give_cards(player, constants.GIVEN_CARDS)
            player.produce()

    def resolve_current_player_turn(self):
        current_player = game_state.current_player
        actions = get_legal_actions(game_state)
        if actions:
            chosen_action = current_player.interface.choose_action(actions)
            resolve_action(chosen_action)

    def resolve_action(self, action: Action):
        #TODO: Implement action resolution logic
        current_player = game_state.current_player

        if action.action_type == "raise_temp":
            raise_temp(game_state, current_player, action.params.get("amount", 1))
        
        elif action.action_type == "raise_oxygen":
            raise_oxygen(game_state, current_player, action.params.get("amount", 1))
        
        elif action.action_type == "raise_venus":
            raise_venus(game_state, current_player, action.params.get("amount", 1))
        
        elif action.action_type == "place_tile":
            tile_type = action.params.get("tile_type", "default")
            location = current_player.place_tile(game_state.board, tile_type)
            place_tile(current_player, tile_type, location)
        
        elif action.action_type == "play_card":
            card = action.params.get("card", None)
            if card:
                current_player.play_card(card, game_state.board)

        elif action.action_type == "standard_action":
            standard_action = action.params.get("standard_action", None)
            if standard_action:
                resolve_standard_action(game_state, current_player, standard_action)

    def is_game_over(self) -> bool:
        if (game_state.board.oxygen == constants.MAX_OX and
            game_state.board.temp == constants.MAX_TEMP and
            game_state.board.oceans == constants.NUM_OCEANS):
            return True
        return False

    def calculate_award(self, award: str) -> int:
        #TODO: implement
        return constants.AWARD_FIRST_PLACE

    def calculate_points(self, player: Player) -> int:
        points = 0
        #points from awards
        for award in player.awards:
            points += calculate_award(award)
        #points from milestones
        for milestone in player.milestones:
            points += 5
        #points from greeneries
        points += len(player.tiles.forests)
        #points from cities
        for city in player.tiles.cities:
            for adj in game_state.board.get_adjacent(city):
                if adj.occupied_with == "greenery":
                    points += 1
        #points from cards
        for card in player.cards:
            points += card.resolve_points(game_state.board)

        return points

    def get_legal_actions(self, game_state: GameState) -> list[Action]:
        """Returns all legal actions for the current player in the given game state."""
        actions = []
        current_player_id = game_state.current_player_id
        current_player = game_state.get_player_by_id(current_player_id)
        
        # Raise oxygen
        if can_raise_oxygen(game_state):
            actions.append(Action("raise_oxygen", current_player.id, {}))
        
        # Raise temperature
        if can_raise_temp(game_state):
            actions.append(Action("raise_temp", current_player.id, {}))
        
        # Raise venus
        if can_raise_venus(game_state):
            actions.append(Action("raise_venus", current_player.id, {}))
        
        # Play cards
        for card in current_player.hand:
            if can_play_card(game_state, current_player, card):
                actions.append(Action("play_card", current_player.id, {"card_name": card.name}))
        
        # Place colonies
        for planet in game_state.planets:
            if can_place_colony(game_state, current_player, planet.name):
                actions.append(Action("place_colony", current_player.id, {"planet_name": planet.name}))
        
        # Fund milestones
        for milestone in game_state.milestones_object.milestones:
            if can_fund_milestone(game_state, current_player, milestone):
                actions.append(Action("fund_milestone", current_player.id, {"milestone_name": milestone}))
        
        # Fund awards
        for award in game_state.awards_object.awards:
            if can_fund_award(game_state, current_player, award):
                actions.append(Action("fund_award", current_player.id, {"award_name": award}))
        
        # Sell patents
        if can_sell_patents(game_state, current_player):
            # Generate all subsets of sellable cards
            from itertools import combinations
            for i in range(1, len(current_player.cards) + 1):
                for card_combo in combinations(current_player.cards, i):
                    actions.append(Action("sell_patents", current_player.id, {"card_names": [c.name for c in card_combo]}))
        
        # Buy power plant
        if can_buy_power_plant(game_state, current_player):
            actions.append(Action("power_plant", current_player.id, {}))
        
        # Buy asteroid
        if can_buy_asteroid(game_state, current_player):
            actions.append(Action("asteroid", current_player.id, {}))
        
        # Buy aquifer
        if can_buy_aquifer(game_state, current_player):
            actions.append(Action("aquifer", current_player.id, {}))
        
        # Place greenery
        if can_place_greenery(game_state, current_player):
            actions.append(Action("greenery", current_player.id, {}))
        
        # Place city
        if can_place_city(game_state, current_player):
            actions.append(Action("city", current_player.id, {}))
        
        # Trade (for each available planet)
        for planet in game_state.planets:
            if can_trade(game_state, current_player):
                actions.append(Action("trade", current_player.id, {"target": planet.name}))
        
        return actions

