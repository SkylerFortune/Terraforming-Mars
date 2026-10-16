import random

from src.agents.base_agent import BaseAgent
from src.engine.classes.helper.action import Action
from src.engine.classes.helper.game_state import GameState


class RandomAgent(BaseAgent):
    def __init__(self):
        pass

    def choose_action(self, actions: list[Action]) -> Action:
        return random.choice(actions)