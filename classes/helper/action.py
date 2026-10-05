from dataclasses import dataclass


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