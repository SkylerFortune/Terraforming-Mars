from classes.helper.production import Production
from classes.helper.reward import Reward


class Constants:
    FUNDED_AWARDS = 0
    AWARD_COSTS = [8, 14, 24]
    STARTING_CARDS = 4
    MAX_TEMP = 8
    MAX_OX = 14
    MAX_VENUS = 30
    NUM_OCEANS = 9
    TRADE_COST_MONEY = 9
    TRADE_COST_TITANIUM = 3
    TRADE_COST_ENERGY = 3
    MAX_COLONIES = 3
    MILESTONE_COST = 8
    MAX_FUNDABLE_MILESTONES = 3
    NUM_MILESTONES = 5
    NUM_AWARDS = 5
    MAX_FUNDABLE_AWARDS = 3
    POWER_PLANT_COST = 11
    ASTEROID_COST = 14
    AQUIFER_COST = 18
    GREENERY_COST = 23
    CITY_COST = 25
    CITY_REWARD = Reward(production=Production(money=1))
    ADDITIONAL_PLANETS = 2
    AWARD_FIRST_PLACE = 5
    AWARD_SECOND_PLACE = 2