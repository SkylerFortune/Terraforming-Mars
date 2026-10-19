import random

from src.agents.base_agent import BaseAgent
from engine.old.classes.helper.action import Action
from engine.game_state import GameState


class RandomAgent(BaseAgent):
    def __init__(self):
        pass

    def choose_action(self, actions: list[Action]) -> Action:
        return random.choice(actions)