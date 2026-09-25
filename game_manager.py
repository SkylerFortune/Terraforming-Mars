from dataclasses import dataclass
import random

from classes.board import Board
from classes.card import Card
from classes.planet import Planet
from classes.player import Player
from classes.requirement import Requirement
from classes.tile import Tile


class GameManager:
    def __init__(self, ocean_locations: list[tuple[int, int, int]], volcano_locations: list[tuple[int, int, int]]) -> None:
 
        self.game_state = GameState(ocean_locations=ocean_locations, volcano_locations=volcano_locations)

        self.milestones = self.generate_milestones()
        self.awards = self.generate_awards()

    ## --- GAME FLOW --- ##
    def setup_phase(self):
        #decide first person
        self.game_state.first_player = random.choice(self.game_state.players)
        self.game_state.current_player = self.game_state.first_player
        #deal cards, corps, and preludes
        for player in self.game_state.players:
            self.give_cards(player, 10)
            player.gain_cards(self.game_state.draw_corps(2))
            player.gain_cards(self.game_state.draw_preludes(2))
        #TODO: players decide which cards to keep
        self.game_loop()

    def game_loop(self):
        for player in self.game_state.players:
            if player.corp:
                player.play_card(player.corp, self.game_state.board)
            if player.preludes:
                for prelude in player.preludes:
                    player.play_card(prelude, self.game_state.board)
        #do turns
        while not self.is_game_over():
            self.resolve_current_player_turn()
            self.game_state.current_player = self.game_state.next_player()
            if self.game_state.generation_over:
                self.production()
                self.game_state.generation_over = False

        self.endgame()

    def endgame(self):
        #place greenery tiles
        pass
        #count points
        for player in self.game_state.players:
            print(f"{player.id}: {self.calculate_points(player)}")

    def production(self):
        for player in self.game_state.players:
            self.give_cards(player, 4)
            player.produce()
            #TODO: choose which cards

    def resolve_current_player_turn(self):
        current_player = self.game_state.current_player
        #TODO: Resolve logic

    ## --- GAME FUNCTIONS
    def give_cards(self, player: Player, num_cards: int) -> None:
        cards = self.game_state.draw_cards(num_cards)
        player.gain_cards(cards)

    def find_europa_reward(self) -> Reward:
        points_func = lambda: self.points(points)
        # Find the reward for Europa based on the current game state
        europa = next((p for p in self.game_state.planets if p.name == "Europa"), None)
        if europa:
            match europa.index + 1:
                case 1, 2:
                    return Reward(production=Production(steel=1))
                case 3, 4:
                    return Reward(production=Production(energy=1))
                case 5, 6, 7:
                    return Reward(production=Production(plants=1))
        return Reward()

    def find_pluto_reward(self) -> Reward:
        #TODO: Find the reward for Pluto based on the current game state
        return Reward(resources=Resources(steel=1))

    def place_tile(self, player: Player, tile_type: str, location: tuple[int, int, int]) -> None:
        self.game_state.board.place_tile(player, tile_type, location)
        placement_bonus = self.get_placement_bonus(location)
        if placement_bonus:
            player.receive_reward(placement_bonus, self.game_state.board)

    def get_placement_bonus(self, position: tuple[int, int, int]) -> Reward | None:
        return self.game_state.board.get_tile_target(position).placement_bonus

    def can_raise_temp(self) -> bool:
        if self.game_state.board.temp < 8:
            return True
        return False

    def raise_temp(self) -> None:
        self.game_state.board.temp += 1

    def can_raise_oxygen(self) -> bool:
        if self.game_state.board.oxygen < 14:
            return True
        return False

    def raise_oxygen(self, player: Player):
        if self.can_raise_oxygen():
            self.game_state.board.oxygen += 1

    def can_raise_venus(self) -> bool:
        if self.game_state.board.venus < 30:
            return True
        return False

    def raise_venus(self) -> None:
        self.game_state.board.venus += 1

    def can_trade(self, player: Player) -> bool:
        return player.available_fleets > 0 and (player.has_resource("money", 9) or player.has_resource("energy", 3) or player.has_resource("titanium", 3))

    def trade(self, player: Player, target: str) -> None:
        if self.can_trade(player):
            player.available_fleets -= 1
            self.resolve_trade(player, target)

    #TODO: add trading logic per planet
    def resolve_trade(self, player: Player, target: str) -> None:
        if target == "enceladus":
            pass
        elif target == "ceres":
            pass
        elif target == "triton":
            pass
        elif target == "pluto":
            pass
        elif target == "eris":
            pass
        elif target == "europa":
            pass
        elif target == "titan":
            pass
        elif target == "luna":
            pass
        elif target == "ganymede":
            pass
        elif target == "callisto":
            pass
        elif target == "miranda":
            pass
        else:
            raise ValueError("Invalid target")

    #TODO: add card playing logic
    def play_card(self, player: Player, card: Card) -> None:
        space_port = Card("space port", "", "green", ["city", "building"], 22, [Requirement(colonies=1)], Reward(production=Production(energy=-1, money=4), tile="city"))
        player.play_card(card, self.game_state.board)

    ## --- STANDARD ACTIONS --- ##
    def can_place_colony(self, player: Player, planet_name: str) -> bool:
        return (len(player.colonies) < 3) and (planet_name in [planet.name for planet in self.game_state.planets if planet.name == planet_name])

    def place_colony(self, player: Player, planet_name: str):
        if self.can_place_colony(player, planet_name):
            player.colonies.append(self.game_state.get_planet(planet_name))

    #milestones
    def get_num_funded_milestones(self):
        return sum([len(player.milestones) for player in self.game_state.players])

    def can_fund_milestone(self, player: Player, milestone_name: str) -> bool:
        return milestone_name in self.milestones and player.has_resource("money", 8) and (self.get_num_funded_milestones() < 3)

    def fund_milestone(self, player: Player, milestone_name: str):
        if self.can_fund_milestone(player, milestone_name):
            player.milestones.append(milestone_name)
        else:
            print("Milestone not found")

    #awards
    def get_num_funded_awards(self):
        return sum([len(player.awards) for player in self.game_state.players])

    def can_fund_award(self, player: Player, award_name: str) -> bool:
        num_funded_awards = self.get_num_funded_awards()
        if num_funded_awards == 0:
            cost = 8
        elif num_funded_awards == 1:
            cost = 14
        elif num_funded_awards == 2:
            cost = 20
        else:
            return False
        
        return award_name in self.awards and player.has_resource("money", cost)

    def fund_award(self, player: Player, award_name: str):
        if award_name in self.awards:
            player.awards.append(award_name)
        else:
            print("Award not found")

    def can_sell_patents(self, player: Player) -> bool:
        return len(player.cards) > 0

    def sell_patents(self, cards: list[Card], player: Player) -> None:
        count = 0
        for card in cards:
            if card in player.cards:
                player.cards.remove(card)
                count += 1
        player.resources.money += count

    def can_buy_power_plant(self, player: Player) -> bool:
        return player.has_resource("money", 11)

    def power_plant(self, player: Player):
        if self.can_buy_power_plant(player):
            player.spend("money", 11)
            player.receive_reward(Reward(production=Production(energy=1)))

    def can_buy_asteroid(self, player: Player) -> bool:
        return player.has_resource("money", 14)

    def asteroid(self, player: Player) -> None:
        if self.can_buy_asteroid(player):
            player.spend("money", 14)
            player.increase_terraform_rating(1)

    def can_buy_aquifer(self, player: Player) -> bool:
        return player.has_resource("money", 18)

    def aquifer(self, player: Player) -> None:
        if self.can_buy_aquifer(player):
            player.spend("money", 18)
            location = player.place_tile(self.game_state.board, "ocean")
            self.game_state.board.place_tile(player, "oceans", location)
            player.increase_terraform_rating(1)

    def can_place_greenery(self, player: Player) -> bool:
        return player.has_resource("money", 23)

    def greenery(self, player: Player) -> None:
        if self.can_place_greenery(player):
            player.spend("money", 23)
            location = player.place_tile(self.game_state.board, "greenery")
            self.game_state.board.place_tile(player, "greenery", location)
            self.raise_oxygen(player)

    def can_place_city(self, player: Player) -> bool:
        return player.has_resource("money", 25) and (self.game_state.board.available_locations_by_type("city") != [])

    def city(self, player: Player) -> None:
        if self.can_place_city(player):
            player.spend("money", 25)
            location = player.place_tile(self.game_state.board, "city")
            self.game_state.board.place_tile(player, "city", location)
            player.receive_reward(Reward(production=Production(money=1)))

    def is_game_over(self) -> bool:
        if (self.game_state.board.oxygen == 14 and
            self.game_state.board.temp == 8 and
            #TODO: 9 oceans?
            self.game_state.board.oceans == 9):
            return True
        return False

    def calculate_points(self, player: Player) -> int:
        points = 0
        #points from awards
        for award in player.awards:
            points += self.calculate_award(award)
        #points from milestones
        for milestone in player.milestones:
            points += 5
        #points from greeneries
        points += len(player.tiles.forests)
        #points from cities
        for city in player.tiles.cities:
            for adj in self.game_state.board.get_adjacent(city):
                if adj.occupied_with == "greenery":
                    points += 1
        #points from cards
        for card in player.cards:
            points += card.resolve_points(self.game_state.board)

        return points

    ## --- INIT --- ##
    def generate_awards(self) -> list[str]:
        # Generate a list of available awards
        return ["Award 1", "Award 2", "Award 3"]

    def generate_milestones(self) -> list[str]:
        # Generate a list of available milestones
        return ["Milestone 1", "Milestone 2", "Milestone 3"]

    def generate_planets(self, num_players: int) -> list[Planet]:
        # Generate a list of planets for the game
        ceres = Planet("Ceres", placement_bonus=Reward(production=Production(steel=1)), colony_bonus=Reward(resources=Resources(steel=1)), track_values=[1, 2, 3, 4, 6, 8, 10], resource="steel")
        enceladus = Planet("Enceladus", placement_bonus=Reward(resources=Resources(microbes=3)), colony_bonus=Reward(resources=Resources(microbes=1)), track_values=[0, 1, 2, 3, 4, 4, 5], resource="microbes")
        europa = Planet("Europa", placement_bonus=Reward(tile='ocean'), colony_bonus=Reward(resources=Resources(money=1)), track_values=[0, 1, 2, 3, 4, 5, 6], resource="money")
        titan = Planet("Titan", placement_bonus=Reward(resources=Resources(floaters=3)), colony_bonus=Reward(resources=Resources(floaters=1)), track_values=[0, 1, 1, 2, 3, 3, 4], resource="floaters")
        luna = Planet("luna", placement_bonus=Reward(production=Production(money=2)), colony_bonus=Reward(resources=Resources(money=2)), track_values=[1, 2, 4, 7, 10, 13, 17], resource="money")
        io = Planet("Io", placement_bonus=Reward(production=Production(heat=1)), colony_bonus=Reward(resources=Resources(heat=2)), track_values=[2, 3, 4, 6, 8, 10, 13], resource="heat")
        pluto = Planet("Pluto", placement_bonus=Reward(resources=Resources(cards=2)), colony_bonus=lambda: self.find_pluto_reward(), track_values=[0, 1, 2, 2, 3, 3, 4], resource="cards")
        ganymede = Planet("Ganymede", placement_bonus=Reward(production=Production(plants=1)), colony_bonus=Reward(resources=Resources(plants=1)), track_values=[0, 1, 2, 3, 4, 5, 6], resource="plants")
        callisto = Planet("Callisto", placement_bonus=Reward(production=Production(energy=1)), colony_bonus=Reward(resources=Resources(energy=3)), track_values=[0, 2, 3, 5, 7, 10, 13], resource="energy")
        miranda = Planet("Miranda", placement_bonus=Reward(resources=Resources(animals=1)), colony_bonus=Reward(resources=Resources(cards=1)), track_values=[0, 1, 1, 2, 2, 3, 3], resource="cards")
        triton = Planet ("Triton", placement_bonus=Reward(resources=Resources(titanium=3)), colony_bonus=Reward(resources=Resources(titanium=1)), track_values=[0, 1, 1, 2, 3, 4, 5], resource="titanium")

        planets = [ceres, enceladus, europa, titan, luna, pluto, io, ganymede, callisto, miranda, triton]
        return random.sample(planets, num_players + 2)


class GameState:
    def __init__(self, ocean_locations: list[tuple[int, int, int]], volcano_locations: list[tuple[int, int, int]]) -> None:
        self.board = Board(ocean_locations=ocean_locations, volcano_locations=volcano_locations)
        self.draw_pile: list[Card] = []
        self.discard_pile: list[Card] = []
        self.available_prelude_cards: list[Card] = []
        self.available_corp_cards: list[Card] = []
        self.players: list[Player]
        self.planets: list[Planet]
        self.awards = list[str]
        self.milestones = list[str]
        self.first_player: Player
        self.current_player: Player
        self.generation_over: bool = False

    def next_player(self):
        current_index = self.players.index(self.current_player)
        return self.players[(current_index + 1) % len(self.players)]

    def draw_preludes(self, num_preludes: int) -> list[Card]:
        preludes = []
        for _ in range(num_preludes):
            if self.available_prelude_cards:
                preludes.append(self.available_prelude_cards.pop())
        return preludes

    def draw_corps(self, num_corps: int) -> list[Card]:
        corps = []
        for _ in range(num_corps):
            if self.available_corp_cards:
                corps.append(self.available_corp_cards.pop())
        return corps

    def draw_cards(self, num_cards: int) -> list[Card]:
        cards = []
        for _ in range(num_cards):
            if self.draw_pile:
                cards.append(self.draw_pile.pop())
            else:
                # If the draw pile is empty, shuffle the discard pile and use it as the new draw pile
                self.draw_pile = random.sample(self.discard_pile, len(self.discard_pile))
                self.discard_pile = []
                if self.draw_pile:
                    cards.append(self.draw_pile.pop())
        return cards

    def get_planet(self, planet_name: str) -> Planet:
        for planet in self.planets:
            if planet.name == planet_name:
                return planet
        raise ValueError("Planet not found")

@dataclass
class Reward:
    production: Production | None = None
    resources: Resources | None = None
    city: int = 0
    greenery: int = 0
    ocean: int = 0
    special: str = ""

@dataclass
class Production:
    money: int = 0
    steel: int = 0
    titanium: int = 0
    plants: int = 0
    heat: int = 0
    energy: int = 0

@dataclass
class Resources:
    money: int = 0
    steel: int = 0
    titanium: int = 0
    plants: int = 0
    heat: int = 0
    energy: int = 0
    microbes: int = 0
    animals: int = 0
    science: int = 0
    floaters: int = 0
    asteroid: int = 0
    cards: int = 0

@dataclass
class Tiles:
    cities: int = 0
    greeneries: int = 0
    special: str = ""
    oceans: int = 0