from engine.helper.player.player_state import PlayerState


"""
Briber: Pay 12 M€ to receive this milestone, in addition to the normal claim cost of 8 M€ (so, 20 M€ total).
Builder: 7 building tags.
Coastguard: 3 tiles adjacent to ocean.
Diversifier: 8 different tags.
Ecologist: 4 bio tags.
Energizer: 6 energy production.
Engineer: 10 energy production and heat production combined.
Farmer: 5 animal and microbe resources combined.
Forester: 3 plant production.
Fundraiser: 12 M€ production.
Gardener: 3 greeneries.
Generalist: 1 production of each resource. (If you play without the Corporate Era, you need 2 production of each resource instead.)
Geologist: 3 tiles on, or adjacent to, volcanic areas (marked with bold text on the maps). If playing with a map without volcanic areas, replace this milestone.
Hydrologist: Having placed 4 oceans. (Place owner markers on each ocean until claimed. This owner marker does not make the ocean tile yours, though.)
Landshaper: 1 city, 1 greenery, and 1 special tile.
Legend: 4 event cards.
Lobbyist: Having all your 7 delegates in parties (Party Leaders and Chairman also count).
Mayor: 3 cities.
Merchant: 2 of each standard resource (after paying the claim cost).
Metallurgist: 6 steel production and titanium production combined.
Philantropist: 5 cards with non-negative VP. (Cards that count 1 VP per 2 microbes or similar cards also count.)
Pioneer: 4 colonies.
Planetologist: 2 Earth tags, 2 Venus tags, and 2 Jovian tags.
Planner: 16 cards in hand (when claiming this milestone).
Producer: Combined total production of at least 16. Not all types need to be represented, and negative M€ production subtracts from the total.
Researcher: 4 science tags.
Rim settler: 3 Jovian tags.
Spacefarer: 4 space tags.
Sponsor: 3 cards with a cost of 20 M€ or more.
Tactician: 4 cards with requirements.
Terraformer: 29 TR.
Terran: 5 Earth tags.
Thawer: Having raised temperature 5 times. (Mark with your player marker on the temperature track each time you raise temperature until claimed.)
Trader: 3 different types of resources on cards.
"""
class Milestones:
    #TODO
    def hoverlord(self, player: PlayerState) -> bool:
        def _hoverlord_helper(player: PlayerState) -> int:
            return 0
        if _hoverlord_helper(player) >= 7:
            return True
        return False

    def farmer(self, player: PlayerState) -> bool:
        microbes = player.get_tags_by_type("microbe")
        animals = player.get_tags_by_type("animal")

        if microbes + animals >= 5:
            return True
        return False

    def sponser(self, player: PlayerState) -> bool:
        if player.get_num_cards_by_cost(20) >= 3:
            return True
        return False

    def engineer(self, player: PlayerState) -> bool:
        if player.production.heat + player.production.energy >= 10:
            return True
        return False

    def tycoon(self, player: PlayerState) -> bool:
        if len(player.get_cards_by_type("blue") + player.get_cards_by_type("green")) >= 10:
            return True
        return False

    def diversifier(self, player: PlayerState) -> bool:
        tags = ["plant", "microbe", "animal", "building", "city", "space", "jovian", "venusian", "earth", "energy"]
        if sum([1 for tag in tags if player.get_tags_by_type(tag) > 0]) >= 8:
            return True
        return False

    def merchant(self, player: PlayerState) -> bool:
        if player.resources.megacredits >= 2 and \
        player.resources.steel >= 2 and \
        player.resources.plants >= 2 and \
        player.resources.titanium >= 2 and \
        player.resources.energy >= 2 and \
        player.resources.heat >= 2:
            return True
        return False

    def terraformer(self, player: PlayerState) -> bool:
        if player.terraform_rating >= 29:
            return True
        return False

    def rim_settler(self, player: PlayerState) -> bool:
        if player.get_tags_by_type("jovian") >= 3:
            return True
        return False

    def forester(self, player: PlayerState) -> bool:
        if player.production.plants >= 3:
            return True
        return False

    def generalist(self, player: PlayerState) -> bool:
        for resource, value in player.production.__dict__.items():
            if value == 0:
                return False
        return True

    def gardener(self, player: PlayerState) -> bool:
        if len(player.get_tiles_by_type("forest")) >= 3:
            return True
        return False

    def spacefarer(self, player: PlayerState) -> bool:
        if player.get_tags_by_type("space") >= 4:
            return True
        return False

    def philantropist(self, player: PlayerState) -> bool:
        num_cards = len([card for card in player.played_cards if card.victory_points])
        if (num_cards >= 5):
            return True
        return False

    #TODO
    def trader(self, player: PlayerState) -> bool:
        def _trader_helper(player: PlayerState) -> int:
            return 0
        if _trader_helper(player) >= 3:
            return True
        return False

    def coastguard(self, player: PlayerState) -> bool:
        def _coastguard_helper(player: PlayerState) -> int:
            count = 0
            for tile in player.owned_tiles:
                if tile.occupied_with != "ocean":
                    for adj_tile in tile.adj_tiles:
                        if adj_tile.occupied_with == "ocean":
                            count += 1 
                            break
            return count

        if _coastguard_helper(player) >= 3:
            return True
        return False

    def mayor(self, player: PlayerState) -> bool:
        if len(player.owned_tiles) >= 3:
            return True
        return False

    def builder(self, player: PlayerState) -> bool:
        if player.get_tags_by_type("building") >= 7:
            return True
        return False
    
    def planetologist(self, player: PlayerState) -> bool:
        num_earth = player.get_tags_by_type("earth")
        num_venus = player.get_tags_by_type("venus")
        num_jovian = player.get_tags_by_type("jovian")

        if num_earth >= 2 and num_venus >= 2 and num_jovian >= 2:
            return True
        return False

    def tactician(self, player: PlayerState) -> bool:
        if len([1 for card in player.played_cards if card.requirements]) >= 4:
            return True
        return False

    def ecologist(self, player: PlayerState) -> bool:
        if player.get_tags_by_type("plants") + player.get_tags_by_type("microbes") + player.get_tags_by_type("animals") >= 4:
            return True
        return False

    def researcher(self, player: PlayerState) -> bool:
        if player.get_tags_by_type("science") >= 4:
            return True
        return False


    def hydrologist(self, player: PlayerState) -> bool:
        return True

    def legend(self, player: PlayerState) -> bool:
        if len(player.get_cards_by_type("event")) >= 4:
            return True
        return False

    def producer(self, player: PlayerState) -> bool:
        num_prod = sum([prod for _, prod in player.production.__dict__.values()])
        if num_prod >= 16:
            return True
        return False

    def metallurgist(self, player: PlayerState) -> bool:
        if player.production.steel + player.production.titanium >= 6:
            return True
        return False

    def landshaper(self, player: PlayerState) -> bool:
        if len(player.get_tiles_by_type("city")) > 0 and len(player.get_tiles_by_type("forest")) > 0 and len(player.get_tiles_by_type("special")) > 0:
            return True
        return False

    def terran(self, player: PlayerState) -> bool:
        if player.get_tags_by_type("earth") >= 3:
            return True
        return False

    def fundraiser(self, player: PlayerState) -> bool:
        if player.production.megacredits >= 12:
            return True
        return False

    def pioneer(self, player: PlayerState) -> bool:
        if len(player.colonies) >= 4:
            return True
        return False

    def planner(self, player: PlayerState) -> bool:
        if len(player.hand) >= 16:
            return True
        return False

    def geologist(self, player: PlayerState) -> bool:
        count = 0
        for tile in player.owned_tiles:
            if tile.is_volcano:
                count += 1
                continue
            for tile in tile.adj_tiles:
                if tile.is_volcano:
                    count += 1
                    break   

        if count >= 3:
            return True
        return False

    #TODO
    def lobbyist(self, player: PlayerState) -> bool:
        def _lobbyist_helper(player: PlayerState) -> bool:
            return True
        return False

    #TODO
    def briber(self, player: PlayerState) -> bool:
        return True
