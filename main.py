"""
TODO:
    - MAKE GAMESTATE LOGIC IMMUTABLE
    - card input: united_nations_mars_initiative
    - Add resolve corps/preludes to game loop
    - Add isolated cities on board
    - Implement card playing logic
    - Start adding cards
    - Research player logic via deep learning -> simulation environment?
        -Requirements
    - Graph traversal for board, similar to catan
"""

import random

from agents.random_agent import RandomAgent
from classes.player import Player
from game_manager import GameManager

ocean_locations = []
volcano_locations = []
expansions = []
settings = {}

players = [Player(1, RandomAgent()), Player(2, RandomAgent()), Player(3, RandomAgent()), Player(4, RandomAgent())]

game_manager = GameManager(players=players, ocean_locations=ocean_locations, volcano_locations=volcano_locations, expansions=expansions, settings=settings)

#TODO: update all logic
def setup_phase(self):
    #deal cards, corps, and preludes
    for player in game_manager.game_state.players:
        give_cards(player, 10)
        player.gain_cards(game_manager.game_state.draw_corps(2))
        player.gain_cards(game_manager.game_state.draw_preludes(2))
    #TODO: players decide which cards to keep
    game_loop()

def game_loop(self):
    for player in game_manager.game_state.players:
        if player.corp:
            player.play_card(player.corp, game_manager.game_state.board)
        if player.preludes:
            for prelude in player.preludes:
                player.play_card(prelude, game_manager.game_state.board)
    #do turns
    while not is_game_over():
        resolve_current_player_turn()
        game_manager.game_state.current_player = game_manager.game_state.next_player()
        if game_manager.game_state.generation_over:
            production()
            game_manager.game_state.generation_over = False

    endgame()

def endgame(self):
    #place greenery tiles
    pass
    #count points
    for player in game_manager.game_state.players:
        print(f"{player.id}: {calculate_points(player)}")


#TODO: build main game loop