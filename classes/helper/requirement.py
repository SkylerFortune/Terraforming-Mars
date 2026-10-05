from classes.helper.tags import Tags
from classes.player import Player
from game_manager import GameState

class Requirement:
    def __init__(self, temp: int = 0, oceans: int = 0, oxygen: int = 0, venus: int = 0, tags: Tags = Tags()) -> None:
        self.temp = temp
        self.oceans = oceans
        self.oxygen = oxygen
        self.venus = venus
        self.tags = tags

    def is_met(self, game_state: GameState, player: 'Player') -> bool:
        return self.check_oxygen(game_state, player) and self.check_temp(game_state, player) and self.check_oceans(game_state, player) and self.check_venus(game_state, player) and self.check_tags(game_state, player)

    def check_oxygen(self, game_state: GameState, player: 'Player') -> bool:
        return game_state.board.oxygen >= self.oxygen

    def check_temp(self, game_state: GameState, player: 'Player') -> bool:
        return game_state.board.temp >= self.temp

    def check_oceans(self, game_state: GameState, player: 'Player') -> bool:
        return game_state.board.oceans >= self.oceans

    def check_venus(self, game_state: GameState, player: 'Player') -> bool:
        return game_state.board.venus >= self.venus

    def check_tags(self, game_state: GameState, player: 'Player') -> bool:
        if self.tags.other:
            for player in game_state.get_other_players(player):
                if not self.check_tags_single_player(game_state, player):
                    return False
        elif self.tags.everyone:
            for player in game_state.players:
                if not self.check_tags_single_player(game_state, player):
                    return False
        else:
            if not self.check_tags_single_player(game_state, player):
                return False
        return True

    def check_tags_single_player(self, game_state: GameState, player: 'Player') -> bool:
        for tag in self.tags.__dict__:
            if self.tags.__dict__[tag] > 0:
                if not player.get_tags(tag) >= self.tags.__dict__[tag]:
                    return False
        return True