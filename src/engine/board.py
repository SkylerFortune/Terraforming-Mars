"""The Mars board: the Tharsis map, adjacency and where each kind of tile may go.

The map layout itself is static (`SPACES`, `ADJACENT`). Which tiles are on which spaces is
part of the game state (`GameState.tiles`), so every query here takes the state.

Space ids follow the original engine: "01" and "02" are the off-Mars spaces Ganymede Colony
and Phobos Space Haven, and "03".."63" are the Mars spaces row by row from the top left.
"""
from __future__ import annotations

from dataclasses import dataclass

from engine.game_state import GameState, Tile

TILES_PER_ROW = (5, 6, 7, 8, 9, 8, 7, 6, 5)

GANYMEDE_COLONY = "01"
PHOBOS_SPACE_HAVEN = "02"
NOCTIS_CITY = "31"

CITY_TILES = frozenset({"city", "CAPITAL"})
OCEAN_TILES = frozenset({"ocean"})


@dataclass(frozen=True)
class Space:
    id: str
    type: str                     # land | ocean | colony (off Mars)
    x: int
    y: int
    bonus: tuple[str, ...]        # steel | titanium | plant | draw_card
    volcanic: bool = False


def _tharsis() -> list[Space]:
    S, T, P, C = "steel", "titanium", "plant", "draw_card"
    # (type, bonus, volcanic) per space, row by row. From the printed Tharsis map.
    rows = [
        [("land", (S, S)), ("ocean", (S, S)), ("land", ()), ("ocean", (C,)), ("ocean", ())],
        [("land", ()), ("volcanic", (S,)), ("land", ()), ("land", ()), ("land", ()), ("ocean", (C, C))],
        [("volcanic", (C,)), ("land", ()), ("land", ()), ("land", ()), ("land", ()), ("land", ()), ("land", (S,))],
        [("volcanic", (P, T)), ("land", (P,)), ("land", (P,)), ("land", (P,)), ("land", (P, P)),
         ("land", (P,)), ("land", (P,)), ("ocean", (P, P))],
        [("volcanic", (P, P)), ("land", (P, P)), ("land", (P, P)), ("ocean", (P, P)), ("ocean", (P, P)),
         ("ocean", (P, P)), ("land", (P, P)), ("land", (P, P)), ("land", (P, P))],
        [("land", (P,)), ("land", (P, P)), ("land", (P,)), ("land", (P,)), ("land", (P,)),
         ("ocean", (P,)), ("ocean", (P,)), ("ocean", (P,))],
        [("land", ()), ("land", ()), ("land", ()), ("land", ()), ("land", ()), ("land", (P,)), ("land", ())],
        [("land", (S, S)), ("land", ()), ("land", (C,)), ("land", (C,)), ("land", ()), ("land", (T,))],
        [("land", (S,)), ("land", (S, S)), ("land", ()), ("land", ()), ("ocean", (T, T))],
    ]
    spaces = [Space(GANYMEDE_COLONY, "colony", -1, -1, ()), Space(PHOBOS_SPACE_HAVEN, "colony", -1, -1, ())]
    widest = max(TILES_PER_ROW)
    n = 3
    for y, row in enumerate(rows):
        assert len(row) == TILES_PER_ROW[y], f"row {y} has {len(row)} spaces"
        for i, (kind, bonus) in enumerate(row):
            volcanic = kind == "volcanic"
            spaces.append(Space(f"{n:02d}", "land" if volcanic else kind, widest - len(row) + i, y,
                                tuple(bonus), volcanic))
            n += 1
    return spaces


SPACES: dict[str, Space] = {s.id: s for s in _tharsis()}
MARS_SPACES: tuple[str, ...] = tuple(s.id for s in SPACES.values() if s.type != "colony")
OCEAN_SPACES: tuple[str, ...] = tuple(s.id for s in SPACES.values() if s.type == "ocean")


def _adjacent(space: Space) -> tuple[str, ...]:
    if space.type == "colony":
        return ()
    middle = (len(TILES_PER_ROW) - 1) // 2
    x, y = space.x, space.y
    left, right = (x - 1, y), (x + 1, y)
    top_left, top_right = [x, y - 1], [x, y - 1]
    bottom_left, bottom_right = [x, y + 1], [x, y + 1]
    if y < middle:
        bottom_left[0] -= 1
        top_right[0] += 1
    elif y == middle:
        bottom_right[0] += 1
        top_right[0] += 1
    else:
        bottom_right[0] += 1
        top_left[0] -= 1
    by_xy = {(s.x, s.y): s.id for s in SPACES.values() if s.type != "colony"}
    coords = [tuple(top_left), tuple(top_right), right, tuple(bottom_right), tuple(bottom_left), left]
    return tuple(by_xy[c] for c in coords if c in by_xy)


ADJACENT: dict[str, tuple[str, ...]] = {sid: _adjacent(s) for sid, s in SPACES.items()}


# ---- queries on a state --------------------------------------------------------------
def tile_at(state: GameState, space_id: str) -> Tile | None:
    return state.tiles.get(space_id)


def is_city(tile: Tile | None) -> bool:
    return tile is not None and tile.type in CITY_TILES


def is_greenery(tile: Tile | None) -> bool:
    return tile is not None and tile.type == "greenery"


def is_ocean(tile: Tile | None) -> bool:
    return tile is not None and tile.type in OCEAN_TILES


def cities(state: GameState, owner: str | None = None, where: str = "everywhere") -> list[str]:
    out = []
    for sid, t in state.tiles.items():
        if not is_city(t) or (owner is not None and t.owner != owner):
            continue
        on_mars = SPACES[sid].type != "colony"
        if where == "onmars" and not on_mars or where == "offmars" and on_mars:
            continue
        out.append(sid)
    return out


def greeneries(state: GameState, owner: str | None = None) -> list[str]:
    return [sid for sid, t in state.tiles.items() if is_greenery(t) and (owner is None or t.owner == owner)]


def oceans(state: GameState) -> list[str]:
    return [sid for sid, t in state.tiles.items() if is_ocean(t)]


def owned_tiles(state: GameState, owner: str) -> list[str]:
    return [sid for sid, t in state.tiles.items() if t.owner == owner]


def adjacent_with(state: GameState, space_id: str, pred) -> list[str]:
    return [a for a in ADJACENT[space_id] if pred(state.tiles.get(a))]


def is_available_land(state: GameState, space_id: str, player: str) -> bool:
    """An empty land space on Mars this player may use (Noctis City's space is reserved)."""
    space = SPACES[space_id]
    if space.type != "land" or space_id in state.tiles or space_id == NOCTIS_CITY:
        return False
    owner = state.reserved.get(space_id)
    return owner is None or owner == player


def land_spaces(state: GameState, player: str) -> list[str]:
    return [sid for sid in MARS_SPACES if is_available_land(state, sid, player)]


def ocean_spaces_available(state: GameState, player: str) -> list[str]:
    return [sid for sid in OCEAN_SPACES
            if sid not in state.tiles and state.reserved.get(sid) in (None, player)]


def city_spaces(state: GameState, player: str) -> list[str]:
    return [sid for sid in land_spaces(state, player) if not adjacent_with(state, sid, is_city)]


def greenery_spaces(state: GameState, player: str) -> list[str]:
    land = land_spaces(state, player)
    next_to_mine = [sid for sid in land
                    if adjacent_with(state, sid, lambda t: t is not None and t.owner == player)]
    return next_to_mine or land


def isolated_spaces(state: GameState, player: str) -> list[str]:
    return [sid for sid in land_spaces(state, player) if not adjacent_with(state, sid, lambda t: t is not None)]


def volcanic_spaces(state: GameState, player: str) -> list[str]:
    return [sid for sid in land_spaces(state, player) if SPACES[sid].volcanic]


def spaces_for(state: GameState, player: str, rule: str) -> list[str]:
    """Spaces allowed by one of the placement rules named in the card data (`on`)."""
    if rule == "land":
        return land_spaces(state, player)
    if rule == "ocean":
        return ocean_spaces_available(state, player)
    if rule == "greenery":
        return greenery_spaces(state, player)
    if rule == "city":
        return city_spaces(state, player)
    if rule == "away-from-cities":
        return city_spaces(state, player)
    if rule == "isolated":
        return isolated_spaces(state, player)
    if rule == "volcanic":
        return volcanic_spaces(state, player)
    raise ValueError(f"unknown placement rule {rule!r}")
