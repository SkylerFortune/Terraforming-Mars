from abc import abstractmethod

from src.engine.classes.helper.action import Action
from src.engine.classes.helper.game_state import GameState


class BaseAgent:
    def __init__(self) -> None:
        pass

    @abstractmethod
    def choose_action(self, actions: list[Action]) -> Action:
        pass