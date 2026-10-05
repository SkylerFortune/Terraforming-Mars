import json

from classes.board import Board
from classes.card import Card
from classes.helper.production import Production
from classes.helper.requirement import Requirement
from classes.helper.reward import Reward


class CardManager:
    def __init__(self, board: Board):
        self.board = board
        """self.cards = [
            Card(
                name = "Colonizer Training Camp",
                description = "",
                type = "green",
                tags = ["building"],
                cost = 8,
                requirements = [Requirement("oxygen", 5, True)],
                reward = Reward(),
                resources = "",
                points_func = lambda: self.points(self.board, 2)
            ),
            Card(
                name = "Asteroid Mining Consortium",
                description = "",
                type = "green",
                tags = ["jovian"],
                cost = 13,
                requirements = [Requirement("titanium_production", 1, True)],
                reward = Reward(production=Production(titanium=1)),
                resources = "",
                points_func = lambda: self.points(1)
            ),
            Card(
                name = "Deep Well Heating",
                description = "",
                type = "green",
                tags = ["energy", "building"],
                cost = 13,
                requirements = [],
                reward = Reward(production=Production(energy=1), temperature = 1),
                resources = "",
                points_func = lambda: self.points(0)
            )
        ]"""
        self.cards = self._init_cards(self.board)

    def _init_cards(self, board: Board):
        with open("cards_unified.json") as f:
            return [Card(data) for data in json.load(f)]

    def points(self, board: Board, point: int):
        return point
    
    #return list of cards


