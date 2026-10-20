"""The card database, loaded once from the generated JSON in `src/data/`.

`CARDS` maps a card id to its `CardDef`. Card definitions are static and shared by every
game; anything that changes during a game (resources on a card, whether its action was used)
lives on `PlayerState`, not here.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Card types as they appear in the JSON.
PROJECT_TYPES = frozenset({"automated", "active", "event"})


def _tags(raw: Any) -> tuple[str, ...]:
    return tuple(t.lower() for t in (raw or ()))


def _requirements(raw: Any) -> tuple[Mapping, ...]:
    if raw is None:
        return ()
    if isinstance(raw, dict):
        return (raw,)       # the data uses a dict for one requirement and a list for several
    return tuple(raw)


@dataclass(frozen=True)
class CardDef:
    id: str
    name: str
    type: str                        # automated | active | event | corporation | prelude | ...
    module: str                      # folder in the original repo (base, corporation, prelude, ...)
    game_module: str                 # expansion the card belongs to (base, corpera, prelude, ...)
    number: str
    cost: int
    tags: tuple[str, ...]
    requirements: tuple[Mapping, ...]
    behavior: Mapping | None
    action: Mapping | None
    first_action: Mapping | None
    victory_points: Any
    resource_type: str | None
    starting_megacredits: int
    card_discount: Any
    global_parameter_requirement_bonus: Mapping | None
    protected_resources: bool
    methods: tuple[str, ...]
    description: str = ""
    raw: Mapping = field(default_factory=dict, repr=False, compare=False)

    @property
    def is_project(self) -> bool:
        return self.type in PROJECT_TYPES

    @property
    def has_action(self) -> bool:
        return self.action is not None or "action" in self.methods


def _load(path: Path) -> dict[str, CardDef]:
    out: dict[str, CardDef] = {}
    for raw in json.loads(path.read_text(encoding="utf-8")):
        resource = raw.get("resourceType")
        out[raw["id"]] = CardDef(
            id=raw["id"],
            name=raw["name"],
            type=raw["type"],
            module=raw.get("module", ""),
            game_module=raw.get("gameModule", raw.get("module", "")),
            number=raw.get("cardNumber", ""),
            cost=raw.get("cost") or 0,
            tags=_tags(raw.get("tags")),
            requirements=_requirements(raw.get("requirements")),
            behavior=raw.get("behavior"),
            action=raw.get("action"),
            first_action=raw.get("firstAction"),
            victory_points=raw.get("victoryPoints"),
            resource_type=resource.lower() if resource else None,
            starting_megacredits=raw.get("startingMegaCredits", raw.get("startingMegacredits", 0)) or 0,
            card_discount=raw.get("cardDiscount"),
            global_parameter_requirement_bonus=raw.get("globalParameterRequirementBonus"),
            protected_resources=bool(raw.get("protectedResources")),
            methods=tuple(raw.get("methods") or ()),
            description=raw.get("description", ""),
            raw=raw,
        )
    return out


def load_all(data_dir: Path = DATA_DIR) -> dict[str, CardDef]:
    cards: dict[str, CardDef] = {}
    for path in sorted(data_dir.glob("*.json")):
        cards.update(_load(path))
    return cards


CARDS: dict[str, CardDef] = load_all()


def card(card_id: str) -> CardDef:
    try:
        return CARDS[card_id]
    except KeyError:
        raise KeyError(f"unknown card {card_id!r}") from None


def cards_for(modules: tuple[str, ...], types: frozenset[str] | set[str]) -> list[str]:
    """Ids of the cards of the given types that belong to the given expansions, in a stable order."""
    return sorted(cid for cid, c in CARDS.items() if c.game_module in modules and c.type in types)
