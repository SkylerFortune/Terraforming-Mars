from classes.player import Player
from game_manager import GameState

#TODO: implement helper functions
class Awards:
    def venuphile(self, game_state: GameState) -> tuple[Player, Player]:
        sorted_players = sorted(
            game_state.players, 
            key=lambda p: (p.get_tags("venus")), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def landscaper(self, game_state: GameState) -> tuple[Player, Player]:
        sorted_players = sorted(
            game_state.players, 
            key=lambda p: (self._landscaper_helper(p, game_state)), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def _landscaper_helper(self, player: Player, game_state: GameState) -> int:
        return 0

    def suburbian(self, game_state: GameState) -> tuple[Player, Player]:
        sorted_players = sorted(
            game_state.players, 
            key=lambda p: (self._suburbian_helper(p, game_state)), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def _suburbian_helper(self, player: Player, game_state: GameState) -> int:
        return 0

    def magnate(self, game_state: GameState) -> tuple[Player, Player]:
        sorted_players = sorted(
            game_state.players, 
            key=lambda p: (p.get_cards_by_type("green")), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def industrialist(self, game_state: GameState) -> tuple[Player, Player]:
        sorted_players = sorted(
            game_state.players, 
            key=lambda p: (p.resources.energy + p.resources.heat), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def landlord(self, game_state: GameState) -> tuple[Player, Player]:
        sorted_players = sorted(
            game_state.players, 
            key=lambda p: (len(p.tiles.cities) + len(p.tiles.forests) + len(p.tiles.special)), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def banker(self, game_state: GameState) -> tuple[Player, Player]:
        sorted_players = sorted(
            game_state.players, 
            key=lambda p: (p.production.money), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def politician(self, game_state: GameState) -> tuple[Player, Player]:
        sorted_players = sorted(
            game_state.players, 
            key=lambda p: (self._politician_helper(p, game_state)), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)
    
    def _politician_helper(self, player: Player, game_state: GameState) -> int:
        return 0

    def incorporator(self, game_state: GameState) -> tuple[Player, Player]:
        sorted_players = sorted(
            game_state.players, 
            key=lambda p: (self._incorporator_helper(p, game_state)), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def _incorporator_helper(self, player: Player, game_state: GameState) -> int:
        return 0

    def traveller(self, game_state: GameState) -> tuple[Player, Player]:
        sorted_players = sorted(
            game_state.players, 
            key=lambda p: (p.get_tags("jovian") + p.get_tags("earth")), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def forecaster(self, game_state: GameState) -> tuple[Player, Player]:
        sorted_players = sorted(
            game_state.players, 
            key=lambda p: (self._forecaster_helper(p, game_state)), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def _forecaster_helper(self, player: Player, game_state: GameState) -> int:
        return 0

    def biologist(self, game_state: GameState) -> tuple[Player, Player]:
        sorted_players = sorted(
            game_state.players, 
            key=lambda p: (p.get_tags("microbe") + p.get_tags("animal") + p.get_tags("plant")), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def thermalist(self, game_state: GameState) -> tuple[Player, Player]:
        sorted_players = sorted(
            game_state.players, 
            key=lambda p: (p.resources.heat), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def administrator(self, game_state: GameState) -> tuple[Player, Player]:
        sorted_players = sorted(
            game_state.players, 
            key=lambda p: (len([card for card in p.cards if len(card.tags) == 0])), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def founder(self, game_state: GameState) -> tuple[Player, Player]:
        sorted_players = sorted(
            game_state.players, 
            key=lambda p: (self._founder_helper(p, game_state)), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def _founder_helper(self, player: Player, game_state: GameState) -> int:
        return 0

    def highlander(self, game_state: GameState) -> tuple[Player, Player]:
        sorted_players = sorted(
            game_state.players, 
            key=lambda p: (self._highlander_helper(p, game_state)), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def _highlander_helper(self, player: Player, game_state: GameState) -> int:
        return 0

    def celebrity(self, game_state: GameState) -> tuple[Player, Player]:
        sorted_players = sorted(
            game_state.players, 
            key=lambda p: (self._celebrity_helper(p, game_state)), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def _celebrity_helper(self, player: Player, game_state: GameState) -> int:
        return 0

    def botanist(self, game_state: GameState) -> tuple[Player, Player]:
        sorted_players = sorted(
            game_state.players, 
            key=lambda p: (p.production.plants), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def miner(self, game_state: GameState) -> tuple[Player, Player]:
        sorted_players = sorted(
            game_state.players, 
            key=lambda p: (p.resources.steel + p.resources.titanium), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def promoter(self, game_state: GameState) -> tuple[Player, Player]:
        sorted_players = sorted(
            game_state.players, 
            key=lambda p: (len(p.get_cards_by_type("event"))), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def visionary(self, game_state: GameState) -> tuple[Player, Player]:
        sorted_players = sorted(
            game_state.players, 
            key=lambda p: (p.cards), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def excentric(self, game_state: GameState) -> tuple[Player, Player]:
        sorted_players = sorted(
            game_state.players, 
            key=lambda p: (self._excentric_helper(p, game_state)), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def _excentric_helper(self, player: Player, game_state: GameState) -> int:
        return 0

    def manufacturer(self, game_state: GameState) -> tuple[Player, Player]:
        sorted_players = sorted(
            game_state.players, 
            key=lambda p: (p.production.steel + p.production.heat), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def mogul(self, game_state: GameState) -> tuple[Player, Player]:
        sorted_players = sorted(
            game_state.players, 
            key=lambda p: (self._mogul_helper(p, game_state)), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def _mogul_helper(self, player: Player, game_state: GameState) -> int:
        return 0

    def electrician(self, game_state: GameState) -> tuple[Player, Player]:
        sorted_players = sorted(
            game_state.players, 
            key=lambda p: (p.get_tags("energy")), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def estate_dealer(self, game_state: GameState) -> tuple[Player, Player]:
        sorted_players = sorted(
            game_state.players, 
            key=lambda p: (self._estate_dealer_helper(p, game_state)), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def _estate_dealer_helper(self, player: Player, game_state: GameState) -> int:
        return 0

    def benefactor(self, game_state: GameState) -> tuple[Player, Player]:
        sorted_players = sorted(
            game_state.players, 
            key=lambda p: (p.terraform_rating), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def scientist(self, game_state: GameState) -> tuple[Player, Player]:
        sorted_players = sorted(
            game_state.players, 
            key=lambda p: (p.get_tags("science")), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def contrator(self, game_state: GameState) -> tuple[Player, Player]:
        sorted_players = sorted(
            game_state.players, 
            key=lambda p: (p.get_tags("building")), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def metropolist(self, game_state: GameState) -> tuple[Player, Player]:
        sorted_players = sorted(
            game_state.players, 
            key=lambda p: (len(p.tiles.cities)), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def cultivator(self, game_state: GameState) -> tuple[Player, Player]:
        sorted_players = sorted(
            game_state.players, 
            key=lambda p: (len(p.tiles.forests)), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def collector(self, game_state: GameState) -> tuple[Player, Player]:
        sorted_players = sorted(
            game_state.players, 
            key=lambda p: (self._collector_helper(p, game_state)), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def _collector_helper(self, player: Player, game_state: GameState) -> int:
        return 0

    def space_baron(self, game_state: GameState) -> tuple[Player, Player]:
        sorted_players = sorted(
            game_state.players, 
            key=lambda p: (p.get_tags("space")), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def investor(self, game_state: GameState) -> tuple[Player, Player]:
        sorted_players = sorted(
            game_state.players, 
            key=lambda p: (p.get_tags("earth")), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def zoologist(self, game_state: GameState) -> tuple[Player, Player]:
        sorted_players = sorted(
            game_state.players, 
            key=lambda p: (self._zoologist_helper(p, game_state)), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def _zoologist_helper(self, player: Player, game_state: GameState) -> int:
        return 0