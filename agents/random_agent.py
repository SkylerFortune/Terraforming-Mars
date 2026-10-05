import random

from agents.base_agent import BaseAgent
from classes.helper.action import Action
from classes.helper.game_state import GameState


class RandomAgent(BaseAgent):
    def __init__(self):
        pass

    def choose_action(self, actions: list[Action]) -> Action:
        return random.choice(actions)