from classes.player import Player


class Milestones:
    def hoverlord(self, player: Player) -> bool:
        #TODO: add function
        if player.get_num_resource_by_type("floaters") == 7: #type: ignore
            return True
        return False

    def farmer(self, player: Player) -> bool:
        microbes = 0
        animals = 0
        for card in player.played_cards:
            microbes += card.resources.microbes
            animals += card.resources.animals

        if microbes + animals >= 5:
            return True

        return False

    def sponser(self, player: Player) -> bool:
        count = 0
        for card in player.played_cards:
            if card.type != "event":
                if card.cost >= 20:
                    count += 1

        if count >= 3:
            return True
        return False

    def engineer(self, player: Player) -> bool:
        if player.production.heat + player.production.energy >= 10:
            return True
        return False

    def tycoon(self, player: Player) -> bool:
        if len(player.get_cards_by_type("blue") + player.get_cards_by_type("green")) >= 10:
            return True
        return False

    def diversifier(self, player: Player) -> bool:
        tags = ["plant", "microbe", "animal", "building", "city", "space", "jovian", "venusian", "earth", "energy"]
        if sum([1 for tag in tags if player.get_tags(tag) > 0]) >= 8:
            return True
        return False

    def merchant(self, player: Player) -> bool:
        if player.resources.money >= 2 and \
        player.resources.steel >= 2 and \
        player.resources.plants >= 2 and \
        player.resources.titanium >= 2 and \
        player.resources.energy >= 2 and \
        player.resources.heat >= 2:
            return True
        return False

    def terraformer(self, player: Player) -> bool:
        if player.terraform_rating >= 29:
            return True
        return False

    def rim_settler(self, player: Player) -> bool:
        if player.get_tags("jovian") >= 3:
            return True
        return False

    def forester(self, player: Player) -> bool:
        if player.production.plants >= 3:
            return True
        return False

    def generalist(self, player: Player) -> bool:
        for resource, value in player.production.__dict__.items():
            if value == 0:
                return False
        return True

    def gardener(self, player: Player) -> bool:
        if len(player.tiles.forests) >= 3:
            return True
        return False

    def metropolist(self, player: Player) -> bool:
        #TODO: implement
        return True

    def spacefarer(self, player: Player) -> bool:
        if player.get_tags("space") >= 4:
            return True
        return False

    def philantropist(self, player: Player) -> bool:
        num_cards = len([card for card in player.played_cards if card.points_func])
        if (num_cards >= 5):
            return True
        return False

    def trader(self, player: Player) -> bool:
        #TODO: implement
        return True

    def coastguard(self, player: Player) -> bool:
        #TODO: gross triple for loop
        count = 0
        for tile_type, tile_list in player.tiles.get_as_dict().items():
            if tile_type != "ocean":
                for tile in tile_list:
                    for adj_tile in tile.adj_tiles:
                        if adj_tile.occupied_with == "ocean":
                            count += 1 
                            break
        return False

    def mayor(self, player: Player) -> bool:
        if len(player.tiles.cities) >= 3:
            return True
        return False

    def builder(self, player: Player) -> bool:
        if player.get_tags("building") >= 7:
            return True
        return False
    
    def planetologist(self, player: Player) -> bool:
        num_earth = player.get_tags("earth")
        num_venus = player.get_tags("venus")
        num_jovian = player.get_tags("jovian")

        if num_earth >= 2 and num_venus >= 2 and num_jovian >= 2:
            return True
        return False

    def tactician(self, player: Player) -> bool:
        if len([1 for card in player.played_cards if card.requirements]) >= 4:
            return True
        return False

    def ecologist(self, player: Player) -> bool:
        if player.get_tags("plants") + player.get_tags("microbes") + player.get_tags("animals") >= 4:
            return True
        return False

    def researcher(self, player: Player) -> bool:
        if player.get_tags("science") >= 4:
            return True
        return False


    def hydrologist(self, player: Player) -> bool:
        return True

    def legend(self, player: Player) -> bool:
        if len(player.get_cards_by_type("event")) >= 4:
            return True
        return False

    def producer(self, player: Player) -> bool:
        num_prod = sum([prod for _, prod in player.production.__dict__.values()])
        if num_prod >= 16:
            return True
        return False

    def metallurgist(self, player: Player) -> bool:
        if player.production.steel + player.production.titanium >= 6:
            return True
        return False

    def landshaper(self, player: Player) -> bool:
        if len(player.tiles.cities) > 0 and len(player.tiles.forests) > 0 and len(player.tiles.special) > 0:
            return True
        return False

    def terran(self, player: Player) -> bool:
        if player.get_tags("earth") >= 3:
            return True
        return False

    def fundraiser(self, player: Player) -> bool:
        if player.production.money >= 12:
            return True
        return False

    def pioneer(self, player: Player) -> bool:
        if len(player.colonies) >= 4:
            return True
        return False

    def planner(self, player: Player) -> bool:
        pass

    def geologist(self, player: Player) -> bool:
        count = 0
        for tile_list in player.tiles.get_as_dict().values():
            for tile in tile_list:
                if tile.is_volcano:
                    count += 1
                    continue

                count += len([tile for tile in tile_list if tile.is_volcano])

        if count >= 3:
            return True
        return False

    def lobbyist(self, player: Player) -> bool:
        #TODO: implememnt
        return True

    def briber(self, player: Player) -> bool:
        #TODO: implement
        return True
