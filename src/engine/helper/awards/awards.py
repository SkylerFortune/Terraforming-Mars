from engine.helper.player.player_state import PlayerState
from engine.old.classes.player import Player
from engine.game_manager import GameState

"""
Facedown cards (events) and their tags are never counted, unless specified. A wild tag does not count when determining Award winners.
Administrator: Most cards with no tags (don't forget the corporation and Prelude cards).
Banker: Highest M€ production.
Benefactor: Highest TR. If you play with this Award, count it before all other Awards and Milestones!
Biologist: Most bio tags combined (plant, microbe, and animal).
Botanist: Highest plant production.
Celebrity: Most cards that have a cost of 20 M€ or more.
Collector: Most different types of resources, both on your player board and on your cards.
Constructor: Most colonies and cities combined.
Contractor: Most building tags.
Cultivator: Most greeneries.
Electrician: Most power tags.
Estate Dealer: Most tiles next to ocean.
Excentric: Most resources on cards.
Forecaster: Most cards with requirements.
Founder: Most tiles adjacent to special tiles.
Highlander: Most tiles not adjacent to ocean.
Incorporator: Most cards costing 10 M€ or less.
Industrialist: Most steel and energy resources combined.
Investor: Most Earth tags.
Landlord: Most tiles.
Landscaper: Most tiles connected together (each player counts his/her largest group of tiles).
Magnate: Most green cards.
Manufacturer: Highest production of steel and heat combined.
Metropolist: Most cities.
Miner: Having most steel and titanium resources combined.
Mogul: Highest production of steel, titanium, plants, energy, and heat combined (all except M€ production).
Politician: Most Party Leaders and influence combined.
Promoter: Most cards in your event pile.
Scientist: Most science tags.
Space Baron: Most space tags.
Suburbian: Most tiles on areas along the edges of the map.
Thermalist: Most heat resources.
Traveller: Most Jovian and Earth tags combined.
Visionary: Most cards in hand.
Zoologist: Most animal and microbe resources combined.
"""
class Awards:
    def venuphile(self, game_state: GameState) -> tuple[PlayerState, PlayerState]:
        sorted_players = sorted(
            game_state.players.players, 
            key=lambda p: (p.get_tags_by_type("venus")), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    #TODO
    def landscaper(self, game_state: GameState) -> tuple[PlayerState, PlayerState]:
        def _landscaper_helper(player: PlayerState, game_state: GameState) -> int:
            return 0
        sorted_players = sorted(
            game_state.players.players, 
            key=lambda p: (_landscaper_helper(p, game_state)), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    #TODO
    def suburbian(self, game_state: GameState) -> tuple[PlayerState, PlayerState]:
        def _suburbian_helper(player: PlayerState, game_state: GameState) -> int:
            return 0
        sorted_players = sorted(
            game_state.players.players, 
            key=lambda p: (_suburbian_helper(p, game_state)), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def magnate(self, game_state: GameState) -> tuple[PlayerState, PlayerState]:
        sorted_players = sorted(
            game_state.players.players, 
            key=lambda p: (p.get_cards_by_type("green")), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def industrialist(self, game_state: GameState) -> tuple[PlayerState, PlayerState]:
        sorted_players = sorted(
            game_state.players.players, 
            key=lambda p: (p.resources.energy + p.resources.heat), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def landlord(self, game_state: GameState) -> tuple[PlayerState, PlayerState]:
        sorted_players = sorted(
            game_state.players.players, 
            key=lambda p: (len(p.owned_tiles)), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def banker(self, game_state: GameState) -> tuple[PlayerState, PlayerState]:
        sorted_players = sorted(
            game_state.players.players, 
            key=lambda p: (p.production.megacredits), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    #TODO
    def politician(self, game_state: GameState) -> tuple[PlayerState, PlayerState]:
        def _politician_helper(player: PlayerState, game_state: GameState) -> int:
            return 0
        sorted_players = sorted(
            game_state.players.players, 
            key=lambda p: (_politician_helper(p, game_state)), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    #TODO
    def incorporator(self, game_state: GameState) -> tuple[PlayerState, PlayerState]:
        def _incorporator_helper(player: PlayerState, game_state: GameState) -> int:
            return 0
        sorted_players = sorted(
            game_state.players.players, 
            key=lambda p: (_incorporator_helper(p, game_state)), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def traveller(self, game_state: GameState) -> tuple[PlayerState, PlayerState]:
        sorted_players = sorted(
            game_state.players.players, 
            key=lambda p: (p.get_tags_by_type("jovian") + p.get_tags_by_type("earth")), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    #TODO
    def forecaster(self, game_state: GameState) -> tuple[PlayerState, PlayerState]:
        def _forecaster_helper(player: PlayerState, game_state: GameState) -> int:
            return 0
        sorted_players = sorted(
            game_state.players.players, 
            key=lambda p: (_forecaster_helper(p, game_state)), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def biologist(self, game_state: GameState) -> tuple[PlayerState, PlayerState]:
        sorted_players = sorted(
            game_state.players.players, 
            key=lambda p: (p.get_tags_by_type("microbe") + p.get_tags_by_type("animal") + p.get_tags_by_type("plant")), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def thermalist(self, game_state: GameState) -> tuple[PlayerState, PlayerState]:
        sorted_players = sorted(
            game_state.players.players, 
            key=lambda p: (p.resources.heat), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def administrator(self, game_state: GameState) -> tuple[PlayerState, PlayerState]:
        sorted_players = sorted(
            game_state.players.players, 
            key=lambda p: (len([card for card in p.played_cards if card.tags.sum() == 0])), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    #TODO
    def founder(self, game_state: GameState) -> tuple[PlayerState, PlayerState]:
        def _founder_helper(player: PlayerState, game_state: GameState) -> int:
            return 0
        sorted_players = sorted(
            game_state.players.players, 
            key=lambda p: (_founder_helper(p, game_state)), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    #TODO
    def highlander(self, game_state: GameState) -> tuple[PlayerState, PlayerState]:
        def _highlander_helper(player: PlayerState, game_state: GameState) -> int:
            return 0
        sorted_players = sorted(
            game_state.players.players, 
            key=lambda p: (_highlander_helper(p, game_state)), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    #TODO
    def celebrity(self, game_state: GameState) -> tuple[PlayerState, PlayerState]:
        def _celebrity_helper(player: PlayerState, game_state: GameState) -> int:
            return 0
        sorted_players = sorted(
            game_state.players.players, 
            key=lambda p: (_celebrity_helper(p, game_state)), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    

    def botanist(self, game_state: GameState) -> tuple[PlayerState, PlayerState]:
        sorted_players = sorted(
            game_state.players.players, 
            key=lambda p: (p.production.plants), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def miner(self, game_state: GameState) -> tuple[PlayerState, PlayerState]:
        sorted_players = sorted(
            game_state.players.players, 
            key=lambda p: (p.resources.steel + p.resources.titanium), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def promoter(self, game_state: GameState) -> tuple[PlayerState, PlayerState]:
        sorted_players = sorted(
            game_state.players.players, 
            key=lambda p: (len(p.get_cards_by_type("event"))), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def visionary(self, game_state: GameState) -> tuple[PlayerState, PlayerState]:
        sorted_players = sorted(
            game_state.players.players, 
            key=lambda p: (p.played_cards), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    #TODO
    def excentric(self, game_state: GameState) -> tuple[PlayerState, PlayerState]:
        def _excentric_helper(player: PlayerState, game_state: GameState) -> int:
            return 0
        sorted_players = sorted(
            game_state.players.players, 
            key=lambda p: (_excentric_helper(p, game_state)), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def manufacturer(self, game_state: GameState) -> tuple[PlayerState, PlayerState]:
        sorted_players = sorted(
            game_state.players.players, 
            key=lambda p: (p.production.steel + p.production.heat), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    #TODO
    def mogul(self, game_state: GameState) -> tuple[PlayerState, PlayerState]:
        def _mogul_helper(player: PlayerState, game_state: GameState) -> int:
            return 0
        sorted_players = sorted(
            game_state.players.players, 
            key=lambda p: (_mogul_helper(p, game_state)), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)



    def electrician(self, game_state: GameState) -> tuple[PlayerState, PlayerState]:
        sorted_players = sorted(
            game_state.players.players, 
            key=lambda p: (p.get_tags_by_type("energy")), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    #TODO
    def estate_dealer(self, game_state: GameState) -> tuple[PlayerState, PlayerState]:
        def _estate_dealer_helper(player: PlayerState, game_state: GameState) -> int:
            return 0
        sorted_players = sorted(
            game_state.players.players, 
            key=lambda p: (_estate_dealer_helper(p, game_state)), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)



    def benefactor(self, game_state: GameState) -> tuple[PlayerState, PlayerState]:
        sorted_players = sorted(
            game_state.players.players, 
            key=lambda p: (p.terraform_rating), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def scientist(self, game_state: GameState) -> tuple[PlayerState, PlayerState]:
        sorted_players = sorted(
            game_state.players.players, 
            key=lambda p: (p.get_tags_by_type("science")), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def contrator(self, game_state: GameState) -> tuple[PlayerState, PlayerState]:
        sorted_players = sorted(
            game_state.players.players, 
            key=lambda p: (p.get_tags_by_type("building")), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def metropolist(self, game_state: GameState) -> tuple[PlayerState, PlayerState]:
        sorted_players = sorted(
            game_state.players.players, 
            key=lambda p: (len(p.get_tiles_by_type("city"))), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def cultivator(self, game_state: GameState) -> tuple[PlayerState, PlayerState]:
        sorted_players = sorted(
            game_state.players.players, 
            key=lambda p: (len(p.get_tiles_by_type("forest"))), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    #TODO
    def collector(self, game_state: GameState) -> tuple[PlayerState, PlayerState]:
        def _collector_helper(player: PlayerState, game_state: GameState) -> int:
            return 0
        sorted_players = sorted(
            game_state.players.players, 
            key=lambda p: (_collector_helper(p, game_state)), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)



    def space_baron(self, game_state: GameState) -> tuple[PlayerState, PlayerState]:
        sorted_players = sorted(
            game_state.players.players, 
            key=lambda p: (p.get_tags_by_type("space")), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    def investor(self, game_state: GameState) -> tuple[PlayerState, PlayerState]:
        sorted_players = sorted(
            game_state.players.players, 
            key=lambda p: (p.get_tags_by_type("earth")), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)

    #TODO
    def zoologist(self, game_state: GameState) -> tuple[PlayerState, PlayerState]:
        def _zoologist_helper(player: PlayerState, game_state: GameState) -> int:
            return 0
        sorted_players = sorted(
            game_state.players.players, 
            key=lambda p: (_zoologist_helper(p, game_state)), 
            reverse=True
        )
        first_place = sorted_players[0]
        second_place = sorted_players[1]
        return (first_place, second_place)