from dataclasses import dataclass

from engine.helper.cards.card_manager import CardManager
from engine.helper.awards.awards_object import AwardsObject
from engine.helper.milestones.milestones_object import MilestonesObject
from engine.helper.player.player_state import PlayerState
from engine.helper.board import Board
from engine.helper.player.list_players import ListPlayers
from engine.helper.tracks.oceans_track import OceansTrack
from engine.helper.tracks.oxygen_track import OxygenTrack
from engine.helper.tracks.temperature_track import TemperatureTrack
from engine.helper.tracks.venus_track import VenusTrack
from engine.helper.planet import Planet
from engine.pending import Pending


@dataclass(frozen=True)
class GameState:
    board: 'Board'
    card_manager: 'CardManager'
    players: ListPlayers
    first_player_id: str
    current_player_id: str
    generation: int
    planets: list[Planet]
    awards_object: AwardsObject
    milestones_object: MilestonesObject
    temperature_track: 'TemperatureTrack'
    oxygen_track: 'OxygenTrack'
    venus_track: 'VenusTrack'
    oceans_placed: 'OceansTrack'
    pending: 'Pending | None'

    def get_player_by_id(self, player_id: str) -> 'PlayerState':
        for player in self.players.players:
            if player.player_id == player_id:
                return player
        raise ValueError(f"Player with ID {player_id} not found")