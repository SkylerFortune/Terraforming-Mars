from glob import glob
import json
import random
from types import MappingProxyType

from src.engine.classes.board import Board
from src.engine.classes.card import CardDef, _as_tuple_of_dicts
from src.engine.classes.helper.production import Production
from src.engine.classes.helper.requirement import Requirement
from src.engine.classes.helper.reward import Reward
from src.engine.hooks.registry import HOOKS


class CardManager:
    def __init__(self, expansions: list[str]):
        self.expansions = expansions

        self.active_cards = self.load_cards("/terraforming_mars_jsons/active.json", HOOKS)
        self.event_cards = self.load_cards("/terraforming_mars_jsons/event.json", HOOKS)
        self.preludes = self.load_cards("/terraforming_mars_jsons/preludes.json", HOOKS)
        self.corporations = self.load_cards("/terraforming_mars_jsons/corporations.json", HOOKS)
        self.automated_cards = self.load_cards("/terraforming_mars_jsons/automated.json", HOOKS)

        self.card_deck = self._build_deck()
        self.corporations_deck = self._build_corporations_deck()
        self.preludes_deck = self._build_preludes_deck()

    def draw_cards(self, num_cards: int):
        return [self.card_deck.pop() for _ in range(num_cards)]

    def draw_corporations(self, num_corporations: int):
        return [self.corporations_deck.pop() for _ in range(num_corporations)]

    def draw_preludes(self, num_preludes: int):
        return [self.preludes_deck.pop() for _ in range(num_preludes)]

    def _build_deck(self):
        all_cards = list(self.active_cards.values()) + list(self.event_cards.values()) + list(self.automated_cards.values())
        return random.sample(all_cards, k=len(all_cards))

    def _build_corporations_deck(self):
        return random.sample(list(self.corporations.values()), k=len(list(self.corporations.values())))

    def _build_preludes_deck(self):
        return random.sample(list(self.preludes.values()), k=len(list(self.preludes.values())))

    def load_cards(self, directory, hooks):
        cards = {}
        for path in glob.glob(f"{directory}/*.json"):
            for raw in json.load(open(path, encoding="utf-8")):
                if (not raw["module"] in self.expansions):
                    continue

                cards[raw["id"]] = CardDef(
                    id=raw["id"], name=raw["name"], 
                    type=raw["type"], 
                    module=raw["module"],
                    cost=raw.get("cost"),
                    tags=tuple(raw.get("tags") or ()),
                    requirements=_as_tuple_of_dicts(raw.get("requirements")),
                    behavior=raw.get("behavior"),
                    action=raw.get("action"),
                    first_action=raw.get("firstAction"),
                    victory_points=raw.get("victoryPoints"),
                    resource_type=raw.get("resourceType"),
                    hooks=MappingProxyType(hooks.get(raw["id"], {})),
                )
        return cards
    
    #return list of cards


