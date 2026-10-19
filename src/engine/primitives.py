## --- GAME FUNCTIONS --- ##
from copy import copy
import math

from engine.helper.cards.card_def import CardDef
from engine.helper.cards.card_manager import CardManager
from engine.game_state import GameState
from engine.old.classes.helper.production import Production
from engine.old.classes.helper.resources import Resources
from engine.helper.cards.reward import Reward
from engine.old.classes.player import Player
from engine.helper.player.player_state import PlayerState


def give_cards(game_state: GameState, player: PlayerState, num_cards: int) -> GameState:
    cards = GameState.card_manager.draw_cards(num_cards)
    return GameState(
        board=game_state.board,
        players=game_state.players.update_player(player.gain_cards(cards)),
        card_manager=game_state.card_manager,
        first_player_id=game_state.first_player_id,
        current_player_id=game_state.current_player_id,
        generation=game_state.generation,
        planets=game_state.planets,
        awards_object=game_state.awards_object,
        milestones_object=game_state.milestones_object,
        temperature_track=game_state.temperature_track,
        oxygen_track=game_state.oxygen_track,
        venus_track=game_state.venus_track,
        oceans_placed=game_state.oceans_placed,
        pending=game_state.pending
    )

def find_europa_reward(self, game_state: GameState) -> Reward:
    # Find the reward for Europa based on the current game state
    europa = next((p for p in game_state.planets if p.name == "Europa"), None)
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

def evaluate_requirement(requirement: dict, game_state: GameState, player: PlayerState) -> bool:
    temperature = requirement.get("temperature", math.inf)
    oxygen = requirement.get("oxygen", math.inf)
    venus = requirement.get("venus", math.inf)
    oceans = requirement.get("oceans", math.inf)

    #TODO
    if temperature <= game_state.temperature_track.value and oxygen <= game_state.board.oxygen and venus <= game_state.board.venus and oceans <= game_state.board.oceans:
        return True
    return False

#TODO: implement
def can_play_card(game_state: GameState, player: PlayerState, card: CardDef) -> bool:
    # needs to meet requirements
    for requirement in card.requirements:
        if not evaluate_requirement(requirement, game_state, PlayerState):
            return False
    return True

def get_placement_bonus(position: tuple[int, int, int]) -> Reward | None:
    return game_state.board.get_tile_target(position).placement_bonus

def can_raise_temp(game_state: GameState) -> bool:
    if game_state.board.temp < constants.MAX_TEMP:
        return True
    return False

def raise_temp(game_state: GameState, player: Player, amount: int) -> GameState:
    new_state = copy.deepcopy(game_state)
    new_state.board.temp += amount
    player.increase_terraform_rating(amount)
    player.receive_reward(game_state.get_temp_reward(new_state.board.temp))
    return new_state

def can_raise_oxygen(game_state: GameState) -> bool:
    if game_state.board.oxygen < constants.MAX_OX:
        return True
    return False

def raise_oxygen(game_state: GameState, player: Player, amount: int) -> GameState:
    if can_raise_oxygen(game_state):
        new_state = copy.deepcopy(game_state)
        new_state.board.oxygen += amount
        player.increase_terraform_rating(amount)
        player.receive_reward(game_state.get_oxygen_reward(new_state.board.oxygen))
        return new_state
    return game_state

def can_raise_venus(game_state: GameState) -> bool:
    if game_state.board.venus < constants.MAX_VENUS:
        return True
    return False

def raise_venus(game_state: GameState, player: Player, amount: int) -> GameState:
    if can_raise_venus(game_state):
        new_state = copy.deepcopy(game_state)
        new_state.board.venus += amount
        player.increase_terraform_rating(amount)
        player.receive_reward(game_state.get_venus_reward(new_state.board.venus))
        return new_state
    return game_state

def can_trade(game_state: GameState, player: PlayerState) -> bool:
    return player.available_fleets > 0 and (player.has_resource("money", constants.TRADE_COST_MONEY) or player.has_resource("energy", constants.TRADE_COST_ENERGY) or player.has_resource("titanium", constants.TRADE_COST_TITANIUM))

def trade(game_state: GameState, player: Player, target: str) -> GameState:
    if can_trade(game_state, PlayerState):
        new_state = copy.deepcopy(game_state)
        new_state.players[game_state.players.index(PlayerState)].available_fleets -= 1
        return resolve_trade(new_state, player, target)
    return game_state

#TODO: add trading logic per planet
def resolve_trade(game_state: GameState, player: Player, target: str) -> GameState:
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
def play_card(game_state: GameState, player: Player, card: CardDef) -> GameState:
    new_state = copy.deepcopy(game_state)
    new_state.players[game_state.players.index(PlayerState)].play_card(card, new_state.board)
    return new_state

## --- STANDARD ACTIONS --- ##
def can_place_colony(game_state: GameState, player: Player, planet_name: str) -> bool:
    return (len(player.colonies) < constants.MAX_COLONIES) and (planet_name in [planet.name for planet in game_state.planets if planet.name == planet_name])

def place_colony(game_state: GameState, player: Player, planet_name: str) -> GameState:
    if can_place_colony(game_state, player, planet_name):
        new_state = copy.deepcopy(game_state)
        new_state.players[game_state.players.index(PlayerState)].colonies.append(new_state.get_planet(planet_name))
        return new_state
    return game_state

#milestones
def get_num_funded_milestones(self):
    return sum([len(player.milestones) for player in game_state.players])

def can_fund_milestone(game_state: GameState, player: Player, milestone_name: str) -> bool:
    return milestone_name in game_state.milestones and player.has_resource("money", constants.MILESTONE_COST) and (get_num_funded_milestones() < constants.MAX_FUNDABLE_MILESTONES)

def fund_milestone(game_state: GameState, player: Player, milestone_name: str) -> GameState:
    if can_fund_milestone(game_state, player, milestone_name):
        new_state = copy.deepcopy(game_state)
        new_state.players[game_state.players.index(PlayerState)].milestones.append(milestone_name)
        return new_state
    return game_state

#awards
def get_num_funded_awards(self):
    return sum([len(player.awards) for player in game_state.players])

def can_fund_award(game_state: GameState, player: Player, award_name: str) -> bool:
    num_funded_awards = get_num_funded_awards()
    if num_funded_awards < constants.MAX_FUNDABLE_AWARDS:
        return award_name in game_state.awards and player.has_resource("money", constants.AWARD_COSTS[num_funded_awards])
    return False

def fund_award(game_state: GameState, player: Player, award_name: str) -> GameState:
    if award_name in game_state.awards:
        new_state = copy.deepcopy(game_state)
        new_state.players[game_state.players.index(PlayerState)].awards.append(award_name)
        return new_state
    return game_state

#TODO: add standard actions
def resolve_standard_action(game_state: GameState, player: Player, standard_action: str) -> GameState:
    
    return game_state

def can_sell_patents(game_state: GameState, player: PlayerState) -> bool:
    return len(player.cards) > 0

def sell_patents(game_state: GameState, cards: list[CardDef], player: PlayerState) -> GameState:
    new_state = copy.deepcopy(game_state)
    player_idx = game_state.players.index(PlayerState)
    count = 0
    for card in cards:
        if card in new_state.players[player_idx].cards:
            new_state.players[player_idx].cards.remove(card)
            count += 1
    new_state.players[player_idx].resources.money += count
    return new_state

def can_buy_power_plant(game_state: GameState, player: PlayerState) -> bool:
    return player.has_resource("money", constants.POWER_PLANT_COST)

def power_plant(game_state: GameState, player: PlayerState) -> GameState:
    if can_buy_power_plant(game_state, PlayerState):
        new_state = copy.deepcopy(game_state)
        new_state.players[game_state.players.index(PlayerState)].spend("money", constants.POWER_PLANT_COST)
        new_state.players[game_state.players.index(PlayerState)].receive_reward(Reward(production=Production(energy=1)))
        return new_state
    return game_state

def can_buy_asteroid(game_state: GameState, player: PlayerState) -> bool:
    return player.has_resource("money", constants.ASTEROID_COST)

def asteroid(game_state: GameState, player: PlayerState) -> GameState:
    if can_buy_asteroid(game_state, PlayerState):
        new_state = copy.deepcopy(game_state)
        new_state.players[game_state.players.index(PlayerState)].spend("money", constants.ASTEROID_COST)
        new_state.players[game_state.players.index(PlayerState)].increase_terraform_rating(1)
        return new_state
    return game_state

def can_buy_aquifer(game_state: GameState, player: PlayerState) -> bool:
    return player.has_resource("money", constants.AQUIFER_COST)

def aquifer(game_state: GameState, player: PlayerState) -> GameState:
    if can_buy_aquifer(game_state, PlayerState):
        new_state = copy.deepcopy(game_state)
        player_idx = game_state.players.index(PlayerState)
        new_state.players[player_idx].spend("money", constants.AQUIFER_COST)
        location = new_state.players[player_idx].place_tile(new_state.board, "ocean")
        new_state.board.place_tile(new_state.players[player_idx], "oceans", location)
        new_state.players[player_idx].increase_terraform_rating(1)
        return new_state
    return game_state

def can_place_greenery(game_state: GameState, player: PlayerState) -> bool:
    return player.has_resource("money", constants.GREENERY_COST)

def greenery(game_state: GameState, player: PlayerState) -> GameState:
    if can_place_greenery(game_state, PlayerState):
        new_state = copy.deepcopy(game_state)
        player_idx = game_state.players.index(PlayerState)
        new_state.players[player_idx].spend("money", constants.GREENERY_COST)
        location = new_state.players[player_idx].place_tile(new_state.board, "greenery")
        new_state.board.place_tile(new_state.players[player_idx], "greenery", location)
        new_state = raise_oxygen(new_state, new_state.players[player_idx])
        return new_state
    return game_state

def can_place_city(game_state: GameState, player: PlayerState) -> bool:
    return player.has_resource("money", constants.CITY_COST) and (game_state.board.available_locations_by_type("city") != [])

def city(game_state: GameState, player: PlayerState) -> GameState:
    if can_place_city(game_state, PlayerState):
        new_state = copy.deepcopy(game_state)
        player_idx = game_state.players.index(PlayerState)
        new_state.players[player_idx].spend("money", constants.CITY_COST)
        location = new_state.players[player_idx].place_tile(new_state.board, "city")
        new_state.board.place_tile(new_state.players[player_idx], "city", location)
        new_state.players[player_idx].receive_reward(constants.CITY_REWARD)
        return new_state
    return game_state
