from dataclasses import dataclass

from engine.helper.cards.card_def import CardDef
from engine.helper.tiles.tile import Tile
from engine.helper.player.production_object import ProductionObject
from engine.helper.player.resource_object import ResourceObject


@dataclass(frozen=True)
class PlayerState:
    player_id: str
    terraform_rating: int
    hand: list[CardDef]
    played_cards: list[CardDef]
    resources: 'ResourceObject'
    production: 'ProductionObject'
    trade_fleets: int
    available_fleets: int
    colonies: list[str]
    owned_tiles: list['Tile']

    def do_production(self) -> 'PlayerState':
        new_resources = self.resources.move_energy() + self.production

        return PlayerState(
            player_id=self.player_id,
            terraform_rating=self.terraform_rating,
            trade_fleets=self.trade_fleets,
            available_fleets=self.available_fleets,
            hand=self.hand,
            played_cards=self.played_cards,
            resources=new_resources,
            production=self.production,
            colonies=self.colonies,
            owned_tiles=self.owned_tiles
        )

    def receive_reward(self, reward: 'ResourceObject | ProductionObject') -> 'PlayerState':
        #NOTE: Plausibility handling occours elsewhere
        #TODO: implement plausibility handling
        return PlayerState(
            player_id=self.player_id,
            terraform_rating=self.terraform_rating,
            trade_fleets=self.trade_fleets,
            available_fleets=self.available_fleets,
            hand=self.hand,
            played_cards=self.played_cards,
            resources=self.resources + reward if isinstance(reward, (ResourceObject)) else self.resources,
            production=self.production + reward if isinstance(reward, (ProductionObject)) else self.production,
            colonies=self.colonies,
            owned_tiles=self.owned_tiles
        )

    def increase_terraform_rating(self, amount: int) -> PlayerState:
        return PlayerState(
            player_id=self.player_id,
            terraform_rating=self.terraform_rating + amount,
            hand=self.hand,
            played_cards=self.played_cards,
            resources=self.resources,
            production=self.production,
            trade_fleets=self.trade_fleets,
            available_fleets=self.available_fleets,
            colonies=self.colonies,
            owned_tiles=self.owned_tiles,
        )

    def has_resource(self, resource: str, amount: int) -> bool:
        return getattr(self.resources, resource) >= amount

    def spend_resource(self, resource: str, amount: int) -> PlayerState:
        if self.has_resource(resource, amount):
            return PlayerState(
                player_id=self.player_id,
                terraform_rating=self.terraform_rating,
                hand=self.hand,
                played_cards=self.played_cards,
                resources=self.resources.decrease_resource(resource, amount),
                production=self.production,
                trade_fleets=self.trade_fleets,
                available_fleets=self.available_fleets,
                colonies=self.colonies,
                owned_tiles=self.owned_tiles,
            )
        else:
            raise ValueError("Not enough resources")

    def has_production(self, production: str, amount: int) -> bool:
        return getattr(self.production, production) >= amount

    def spend_production(self, production: str, amount: int) -> PlayerState:
        if self.has_production(production, amount):
            return PlayerState(
                player_id=self.player_id,
                terraform_rating=self.terraform_rating,
                hand=self.hand,
                played_cards=self.played_cards,
                resources=self.resources,
                production=self.production.decrease_production(production, amount),
                trade_fleets=self.trade_fleets,
                available_fleets=self.available_fleets,
                colonies=self.colonies,
                owned_tiles=self.owned_tiles,
            )
        else:
            raise ValueError("Not enough production")

    def add_tile(self, tile: Tile) -> PlayerState:
        return PlayerState(
            player_id=self.player_id,
            terraform_rating=self.terraform_rating,
            hand=self.hand,
            played_cards=self.played_cards,
            resources=self.resources,
            production=self.production,
            colonies=self.colonies,
            owned_tiles=self.owned_tiles + [tile],
            trade_fleets=self.trade_fleets,
            available_fleets=self.available_fleets
        )

    def get_tiles_by_type(self, tile_type: str) -> list[Tile]:
        return [tile for tile in self.owned_tiles if tile.occupied_with == tile_type]

    def gain_cards(self, cards: list[CardDef]):
        return PlayerState(
            player_id=self.player_id,
            terraform_rating=self.terraform_rating,
            hand=self.hand + cards,
            played_cards=self.played_cards,
            resources=self.resources,
            production=self.production,
            colonies=self.colonies,
            owned_tiles=self.owned_tiles,
            trade_fleets=self.trade_fleets,
            available_fleets=self.available_fleets
        )

    def reset_fleets(self) -> PlayerState:
        return PlayerState(
            player_id=self.player_id,
            terraform_rating=self.terraform_rating,
            trade_fleets=self.trade_fleets,
            available_fleets=self.available_fleets,
            hand=self.hand,
            played_cards=self.played_cards,
            resources=self.resources,
            production=self.production,
            colonies=self.colonies,
            owned_tiles=self.owned_tiles
        )

    def get_tags_by_type(self, tag: str) -> int:
        count = 0
        for card in self.get_faceup_cards():
            count += card.get_tags_by_type(tag)
        return count

    def get_cards_by_type(self, card_type: str) -> list[CardDef]:
        return [card for card in self.played_cards if card.type == card_type]

    def get_faceup_cards(self) -> list[CardDef]:
        active_cards = self.get_cards_by_type("active")
        automated_cards = self.get_cards_by_type("automated")
        corporations = self.get_cards_by_type("corporation")
        preludes = self.get_cards_by_type("prelude")

        return active_cards + automated_cards + corporations + preludes

    def get_num_cards_by_cost(self, cost: int) -> int:
        return len([card for card in self.played_cards if card.cost >= cost])