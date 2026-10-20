"""The game state: plain, frozen data.

Nothing in this module changes a state in place. Every update builds a new object with
`dataclasses.replace` (or the small helpers below), so a state can be copied, hashed, saved
and replayed freely. That is what lets the engine pause for a decision (see `engine.pending`)
and lets agents search ahead without side effects.

Players are referred to by id (`"p1"`, `"p2"`, ...) and cards by their JSON id
(`"BIRDS"`), never by object reference.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field, replace
from typing import Any, Iterator, Mapping

RESOURCES: tuple[str, ...] = ("megacredits", "steel", "titanium", "plants", "energy", "heat")

# Lowest production allowed for each resource.
PRODUCTION_MINIMUMS: Mapping[str, int] = {
    "megacredits": -5, "steel": 0, "titanium": 0, "plants": 0, "energy": 0, "heat": 0,
}


class FMap(Mapping[str, Any]):
    """An immutable, hashable mapping. `set` and `without` return a new map."""

    __slots__ = ("_d", "_h")

    def __init__(self, data: Mapping[str, Any] | None = None, **kwargs: Any) -> None:
        d = dict(data or {})
        d.update(kwargs)
        self._d = d
        self._h: int | None = None

    def __getitem__(self, key: str) -> Any:
        return self._d[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._d)

    def __len__(self) -> int:
        return len(self._d)

    def __hash__(self) -> int:
        if self._h is None:
            self._h = hash(frozenset(self._d.items()))
        return self._h

    def __eq__(self, other: object) -> bool:
        if isinstance(other, FMap):
            return self._d == other._d
        return isinstance(other, Mapping) and self._d == dict(other)

    def __repr__(self) -> str:
        return f"FMap({self._d!r})"

    def __reduce__(self):
        return (FMap, (self._d,))

    def set(self, key: str, value: Any) -> "FMap":
        d = dict(self._d)
        d[key] = value
        return FMap(d)

    def without(self, key: str) -> "FMap":
        d = dict(self._d)
        d.pop(key, None)
        return FMap(d)


@dataclass(frozen=True, slots=True)
class Units:
    """An amount of each of the six standard resources. Used for both stock and production."""

    megacredits: int = 0
    steel: int = 0
    titanium: int = 0
    plants: int = 0
    energy: int = 0
    heat: int = 0

    @staticmethod
    def of(data: Mapping[str, int] | None = None, **kwargs: int) -> "Units":
        merged = {**(data or {}), **kwargs}
        unknown = set(merged) - set(RESOURCES)
        if unknown:
            raise KeyError(f"unknown resources: {sorted(unknown)}")
        return Units(**merged)

    def get(self, resource: str) -> int:
        return getattr(self, resource)

    def add(self, resource: str, amount: int) -> "Units":
        return replace(self, **{resource: getattr(self, resource) + amount})

    def set(self, resource: str, amount: int) -> "Units":
        return replace(self, **{resource: amount})

    def __add__(self, other: "Units") -> "Units":
        return Units(*(a + b for a, b in zip(self.as_tuple(), other.as_tuple())))

    def __sub__(self, other: "Units") -> "Units":
        return Units(*(a - b for a, b in zip(self.as_tuple(), other.as_tuple())))

    def as_tuple(self) -> tuple[int, ...]:
        return tuple(getattr(self, r) for r in RESOURCES)

    def items(self) -> Iterator[tuple[str, int]]:
        return ((r, getattr(self, r)) for r in RESOURCES)

    def nonzero(self) -> dict[str, int]:
        return {r: v for r, v in self.items() if v}


@dataclass(frozen=True, slots=True)
class Tile:
    """A tile on a space. `type` is "city", "greenery", "ocean" or a special tile type such as
    "CAPITAL" (the special tile types are the upper-case names used in the card JSON)."""

    type: str
    owner: str | None = None       # oceans have no owner
    card: str | None = None        # the card that placed it, for special tiles


@dataclass(frozen=True, slots=True)
class Pending:
    """One entry in the queue of things still to do.

    A `kind="auto"` entry is a deferred step that needs no decision: the engine runs its
    continuation as soon as it reaches the front of the queue. Any other kind is a question
    for `player`, answered by `engine.pending.resume`.

    The continuation is a string key into `engine.pending.CONTINUATIONS` plus `ctx`, never a
    closure, so a pending state can be copied, hashed and saved.
    """

    player: str
    kind: str                       # auto | action | space | card | cards | option | player | amount
    then: str
    options: tuple = ()
    ctx: tuple[tuple[str, Any], ...] = ()
    min: int = 1                    # how many options to pick; with min == max == 1 the
    max: int = 1                    # choice is a single option, otherwise a tuple of options
    allow_pass: bool = False        # if true, None is also a valid choice
    title: str = ""
    priority: int = 0
    seq: int = 0

    @property
    def context(self) -> dict[str, Any]:
        return dict(self.ctx)

    @property
    def multi(self) -> bool:
        # A "cards" question always takes a tuple, even when exactly one card must be picked.
        return self.kind == "cards" or not (self.min == 1 and self.max == 1)


@dataclass(frozen=True)
class GameOptions:
    modules: tuple[str, ...] = ("base", "corpera", "prelude")
    board: str = "tharsis"
    draft: bool = False                 # not modelled yet
    max_generations: int = 100          # safety stop for simulations that never terraform
    log: bool = True


@dataclass(frozen=True)
class PlayerState:
    id: str
    tr: int = 20
    stock: Units = Units()
    production: Units = Units()
    hand: tuple[str, ...] = ()
    tableau: tuple[str, ...] = ()           # corporation, preludes and project cards, in play order
    events: tuple[str, ...] = ()            # played events, face down
    corporation: str | None = None
    card_resources: FMap = FMap()           # card id -> resources on it
    actions_used: frozenset[str] = frozenset()  # cards whose action was used this generation
    steel_value: int = 2
    titanium_value: int = 3
    plants_per_greenery: int = 8
    passed: bool = False
    tr_raised_this_generation: bool = False
    last_card_played: str | None = None     # this generation
    can_use_heat_as_mc: bool = False        # Helion
    # Setup-phase scratch space: cards dealt but not yet chosen.
    dealt_corporations: tuple[str, ...] = ()
    dealt_preludes: tuple[str, ...] = ()
    preludes_in_hand: tuple[str, ...] = ()
    research: tuple[str, ...] = ()          # cards drawn in the research phase, not yet bought
    first_action_done: bool = True
    # Free-form per-card memory for hooks, e.g. which resource Mining Rights produced.
    card_data: FMap = FMap()

    def resources_on(self, card_id: str) -> int:
        return self.card_resources.get(card_id, 0)

    def has_card(self, card_id: str) -> bool:
        return card_id in self.tableau


@dataclass(frozen=True)
class GameState:
    players: tuple[PlayerState, ...]
    options: GameOptions = GameOptions()
    tiles: FMap = FMap()                   # space id -> Tile
    reserved: FMap = FMap()                # space id -> player id (Land Claim)
    temperature: int = -30
    oxygen: int = 0
    oceans: int = 0
    venus: int = 0
    generation: int = 1
    phase: str = "setup"                   # setup | preludes | action | production | research | final_greenery | end
    first_player: int = 0                  # index into players
    active: int = 0                        # index into players
    actions_this_turn: int = 0
    deck: tuple[str, ...] = ()
    discard: tuple[str, ...] = ()
    corporation_deck: tuple[str, ...] = ()
    prelude_deck: tuple[str, ...] = ()
    milestones: tuple[str, ...] = ()       # names in play
    awards: tuple[str, ...] = ()
    claimed_milestones: tuple[tuple[str, str], ...] = ()   # (name, player id)
    funded_awards: tuple[tuple[str, str], ...] = ()        # (name, player id)
    pending: tuple[Pending, ...] = ()
    pending_seq: int = 0
    seed: int = 0
    rng_calls: int = 0
    log: tuple[str, ...] = ()
    # Transient facts some hooks need, e.g. the card currently being played.
    context: FMap = FMap()

    # ---- players -------------------------------------------------------------------
    def player(self, pid: str) -> PlayerState:
        for p in self.players:
            if p.id == pid:
                return p
        raise KeyError(f"no player {pid!r}")

    def player_index(self, pid: str) -> int:
        for i, p in enumerate(self.players):
            if p.id == pid:
                return i
        raise KeyError(f"no player {pid!r}")

    def with_player(self, player: PlayerState) -> "GameState":
        return replace(self, players=tuple(player if p.id == player.id else p for p in self.players))

    def update_player(self, pid: str, **changes: Any) -> "GameState":
        return self.with_player(replace(self.player(pid), **changes))

    def opponents(self, pid: str) -> tuple[PlayerState, ...]:
        return tuple(p for p in self.players if p.id != pid)

    @property
    def active_player(self) -> PlayerState:
        return self.players[self.active]

    def players_in_generation_order(self) -> tuple[PlayerState, ...]:
        n = len(self.players)
        return tuple(self.players[(self.first_player + i) % n] for i in range(n))

    @property
    def is_solo(self) -> bool:
        return len(self.players) == 1

    # ---- randomness ----------------------------------------------------------------
    def rng(self) -> tuple[random.Random, "GameState"]:
        """A seeded RNG for one use, plus the state with the call counter advanced.

        The RNG is derived from (seed, number of earlier calls), so replaying the same choices
        from the same seed gives the same game.
        """
        return random.Random(f"{self.seed}:{self.rng_calls}"), replace(self, rng_calls=self.rng_calls + 1)

    # ---- log -----------------------------------------------------------------------
    def logged(self, message: str) -> "GameState":
        if not self.options.log:
            return self
        return replace(self, log=self.log + (f"[gen {self.generation}] {message}",))

    @property
    def waiting_for(self) -> Pending | None:
        """The question the game is waiting on, if any."""
        return self.pending[0] if self.pending else None


def dataclass_replace(obj, **changes):
    """`dataclasses.replace`, re-exported so hooks need only import from the engine."""
    return replace(obj, **changes)


__all__ = [
    "RESOURCES", "PRODUCTION_MINIMUMS", "FMap", "Units", "Tile", "Pending", "GameOptions",
    "PlayerState", "GameState", "dataclass_replace", "field",
]
