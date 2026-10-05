from dataclasses import dataclass
from typing import Any

from classes.helper.production import Production
from classes.helper.reward import Reward

@dataclass
class Constants:
    def __init__(self, **kwds: Any) -> None:
        self.FUNDED_AWARDS = 0
        self.AWARD_COSTS = [8, 14, 24]
        self.STARTING_CARDS = 10
        self.GIVEN_CARDS = 4
        self.MAX_TEMP = 8
        self.MAX_OX = 14
        self.MAX_VENUS = 30
        self.NUM_OCEANS = 9
        self.TRADE_COST_MONEY = 9
        self.TRADE_COST_TITANIUM = 3
        self.TRADE_COST_ENERGY = 3
        self.MAX_COLONIES = 3
        self.MILESTONE_COST = 8
        self.MAX_FUNDABLE_MILESTONES = 3
        self.NUM_MILESTONES = 5
        self.NUM_AWARDS = 5
        self.MAX_FUNDABLE_AWARDS = 3
        self.POWER_PLANT_COST = 11
        self.ASTEROID_COST = 14
        self.AQUIFER_COST = 18
        self.GREENERY_COST = 23
        self.CITY_COST = 25
        self.CITY_REWARD = Reward(production=Production(money=1))
        self.ADDITIONAL_PLANETS = 2
        self.AWARD_FIRST_PLACE = 5
        self.AWARD_SECOND_PLACE = 2

        for key, value in kwds.items():
            setattr(self, key, value)