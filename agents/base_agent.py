from abc import abstractmethod

from classes.helper.action import Action
from classes.helper.game_state import GameState


class BaseAgent:
    def __init__(self) -> None:
        pass

    @abstractmethod
    def choose_action(self, actions: list[Action]) -> Action:
        pass