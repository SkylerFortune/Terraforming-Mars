from classes.card import Card
from classes.helper.production import Production
from classes.helper.requirement import Requirement
from classes.helper.reward import Reward


class CardManager:
    def __init__(self):
        self.cards = [
            Card(
                name = "Colonizer Training Camp",
                description = "",
                type = "green",
                tags = ["building"],
                cost = 8,
                requirements = [Requirement("oxygen", 5, True)],
                reward = Reward(),
                resources = "",
                points_func = lambda: self.points(2)
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
        ]

    def points(self, int: point):
        return point
    
    #return list of cards


