from game_manager import GameState

class Requirement:
    def __init__(self, func) -> None:
        self.func = func

    def evaluate(self, game_state: 'GameState'):
        self.func(game_state)

    def production(self, game_state: 'GameState', production: dict[str, int]) -> bool:
        active_player = game_state.current_player
        for resource, amount in production.items():
            if getattr(active_player.production, resource, 0) - production[resource] < 0:
                return False
        return True

    def tags(self, game_state: 'GameState', tags: dict[str, int]) -> bool:
        active_player = game_state.current_player
        for tag, amount in tags.items():
            if active_player.get_tags(tag) < amount:
                return False
        return True