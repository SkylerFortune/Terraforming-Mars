from dataclasses import dataclass

from engine.helper.player.player_state import PlayerState


@dataclass(frozen=True)
class ListPlayers:
    players: list[PlayerState]

    def update_player(self, new_player: PlayerState) -> 'ListPlayers':
        new_players = [p if p != new_player else new_player for p in self.players]
        return ListPlayers(players=new_players)