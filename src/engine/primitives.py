"""Small state-to-state operations that every other module builds on.

Every function here takes a `GameState` and returns a new one. None of them mutate. Hooks
should use these rather than editing a `PlayerState` directly, because several of them also
fire triggers (gaining TR, placing a tile, gaining production) that other cards react to.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Callable, Iterable

from engine import board as B
from engine.cards import CARDS, CardDef, card
from engine.game_state import PRODUCTION_MINIMUMS, RESOURCES, FMap, GameState, Tile, Units
from engine.pending import Priority, ask, continuation, defer

MAX_TEMPERATURE = 8
MIN_TEMPERATURE = -30
MAX_OXYGEN = 14
MAX_OCEANS = 9
MAX_VENUS = 30
OCEAN_ADJACENCY_BONUS = 2


# ---- hooks ---------------------------------------------------------------------------
def get_hook(card_id: str, name: str) -> Callable | None:
    from engine.hooks.registry import HOOKS
    return HOOKS.get(card_id, {}).get(name)


def trigger_own(state: GameState, pid: str, name: str, *args) -> GameState:
    """Call hook `name` on each card in `pid`'s tableau, in play order."""
    for cid in state.player(pid).tableau:
        fn = get_hook(cid, name)
        if fn is not None:
            state = fn(state, pid, *args)
    return state


def trigger_all(state: GameState, name: str, *args) -> GameState:
    """Call hook `name` on every card in play, players in generation order."""
    for p in state.players_in_generation_order():
        for cid in state.player(p.id).tableau:
            fn = get_hook(cid, name)
            if fn is not None:
                state = fn(state, p.id, *args)
    return state


def query_own(state: GameState, pid: str, name: str, *args, default=0) -> list:
    """Collect the results of query hook `name` from `pid`'s tableau."""
    out = []
    for cid in state.player(pid).tableau:
        fn = get_hook(cid, name)
        if fn is not None:
            out.append(fn(state, pid, *args))
    return out


# ---- log -----------------------------------------------------------------------------
def log(state: GameState, message: str) -> GameState:
    return state.logged(message)


# ---- tags ----------------------------------------------------------------------------
def tag_count(state: GameState, pid: str, tag: str, include_events: bool = False) -> int:
    """Tags on `pid`'s face-up cards. Events are face down and don't count (unless asked)."""
    p = state.player(pid)
    ids: Iterable[str] = p.tableau + (p.events if include_events else ())
    return sum(card(cid).tags.count(tag) for cid in ids)


def all_tags(state: GameState, pid: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for cid in state.player(pid).tableau:
        for t in card(cid).tags:
            out[t] = out.get(t, 0) + 1
    return out


# ---- stock and production ------------------------------------------------------------
def add_stock(state: GameState, pid: str, resource: str, amount: int) -> GameState:
    """Gain (or, with a negative amount, lose) resources. Stock never goes below zero."""
    if amount == 0:
        return state
    p = state.player(pid)
    new = max(0, p.stock.get(resource) + amount)
    return state.with_player(replace(p, stock=p.stock.set(resource, new)))


def add_stock_units(state: GameState, pid: str, units: Units) -> GameState:
    for r, v in units.items():
        state = add_stock(state, pid, r, v)
    return state


def can_adjust_production(state: GameState, pid: str, units: Units) -> bool:
    p = state.player(pid)
    return all(p.production.get(r) + v >= PRODUCTION_MINIMUMS[r] for r, v in units.items())


def add_production(state: GameState, pid: str, resource: str, amount: int) -> GameState:
    """Change production, clamped to the minimum. Gains fire `on_production_gain`."""
    if amount == 0:
        return state
    p = state.player(pid)
    new = max(PRODUCTION_MINIMUMS[resource], p.production.get(resource) + amount)
    state = state.with_player(replace(p, production=p.production.set(resource, new)))
    if amount > 0:
        state = trigger_own(state, pid, "on_production_gain", resource, amount)
    return state


def add_production_units(state: GameState, pid: str, units: Units) -> GameState:
    for r, v in units.items():
        state = add_production(state, pid, r, v)
    return state


def spend(state: GameState, pid: str, resource: str, amount: int) -> GameState:
    p = state.player(pid)
    if p.stock.get(resource) < amount:
        raise ValueError(f"{pid} can't spend {amount} {resource}: has {p.stock.get(resource)}")
    return state.with_player(replace(p, stock=p.stock.add(resource, -amount)))


# ---- resources on cards --------------------------------------------------------------
def cards_with_resource(state: GameState, pid: str, resource_type: str | None,
                        tag: str | None = None, min_count: int = 0) -> list[str]:
    """Cards in `pid`'s tableau that hold `resource_type` (any type if None)."""
    out = []
    p = state.player(pid)
    for cid in p.tableau:
        c = card(cid)
        if c.resource_type is None:
            continue
        if resource_type is not None and c.resource_type != resource_type:
            continue
        if tag is not None and tag not in c.tags:
            continue
        if p.resources_on(cid) < min_count:
            continue
        out.append(cid)
    return out


def add_card_resources(state: GameState, pid: str, card_id: str, count: int) -> GameState:
    if count == 0:
        return state
    p = state.player(pid)
    new = max(0, p.resources_on(card_id) + count)
    state = state.with_player(replace(p, card_resources=p.card_resources.set(card_id, new)))
    if count > 0:
        state = trigger_own(state, pid, "on_resource_added", card_id, count)
    return state


def resource_owner(state: GameState, card_id: str) -> str | None:
    for p in state.players:
        if card_id in p.tableau:
            return p.id
    return None


# ---- cards ---------------------------------------------------------------------------
def draw(state: GameState, count: int) -> tuple[GameState, tuple[str, ...]]:
    """Take `count` cards off the deck, reshuffling the discard pile when it runs out."""
    drawn: list[str] = []
    deck, discard = list(state.deck), list(state.discard)
    for _ in range(count):
        if not deck:
            if not discard:
                break
            rng, state = state.rng()
            rng.shuffle(discard)
            deck, discard = discard, []
        drawn.append(deck.pop(0))
    return replace(state, deck=tuple(deck), discard=tuple(discard)), tuple(drawn)


def draw_cards(state: GameState, pid: str, count: int) -> GameState:
    state, drawn = draw(state, count)
    p = state.player(pid)
    state = state.with_player(replace(p, hand=p.hand + drawn))
    return log(state, f"{pid} drew {len(drawn)} card(s)") if drawn else state


def discard_cards(state: GameState, card_ids: Iterable[str]) -> GameState:
    return replace(state, discard=state.discard + tuple(card_ids))


def remove_from_hand(state: GameState, pid: str, card_ids: Iterable[str]) -> GameState:
    p = state.player(pid)
    hand = list(p.hand)
    for cid in card_ids:
        hand.remove(cid)
    return state.with_player(replace(p, hand=tuple(hand)))


# ---- terraform rating ----------------------------------------------------------------
def gain_tr(state: GameState, pid: str, steps: int = 1) -> GameState:
    if steps <= 0:
        return lose_tr(state, pid, -steps) if steps < 0 else state
    p = state.player(pid)
    state = state.with_player(replace(p, tr=p.tr + steps, tr_raised_this_generation=True))
    return trigger_all(state, "on_increase_terraform_rating_by_any_player", pid, steps)


def lose_tr(state: GameState, pid: str, steps: int = 1) -> GameState:
    p = state.player(pid)
    return state.with_player(replace(p, tr=p.tr - steps))


# ---- global parameters ---------------------------------------------------------------
def can_raise_temperature(state: GameState) -> bool:
    return state.temperature < MAX_TEMPERATURE


def raise_temperature(state: GameState, pid: str, steps: int = 1) -> GameState:
    """Raise the temperature `steps` steps (2 °C each), with TR and track bonuses."""
    if steps <= 0 or state.temperature >= MAX_TEMPERATURE:
        return state
    steps = min(steps, (MAX_TEMPERATURE - state.temperature) // 2)
    before = state.temperature
    after = before + 2 * steps
    state = trigger_own(state, pid, "on_global_parameter_increase", "temperature", steps)
    state = gain_tr(state, pid, steps)
    state = replace(state, temperature=after)
    state = log(state, f"{pid} raised the temperature to {after} °C")
    for threshold in (-24, -20):
        if before < threshold <= after:
            state = add_production(state, pid, "heat", 1)
    if before < 0 <= after:
        state = ask_place_ocean(state, pid)
    return state


def can_raise_oxygen(state: GameState) -> bool:
    return state.oxygen < MAX_OXYGEN


def raise_oxygen(state: GameState, pid: str, steps: int = 1) -> GameState:
    if steps <= 0 or state.oxygen >= MAX_OXYGEN:
        return state
    steps = min(steps, MAX_OXYGEN - state.oxygen)
    before = state.oxygen
    after = before + steps
    state = trigger_own(state, pid, "on_global_parameter_increase", "oxygen", steps)
    state = gain_tr(state, pid, steps)
    state = replace(state, oxygen=after)
    state = log(state, f"{pid} raised oxygen to {after}%")
    if before < 8 <= after:
        state = raise_temperature(state, pid, 1)
    return state


def raise_venus(state: GameState, pid: str, steps: int = 1) -> GameState:
    """Venus Next isn't modelled beyond the track itself: 2 % per step and TR."""
    if steps <= 0 or state.venus >= MAX_VENUS:
        return state
    steps = min(steps, (MAX_VENUS - state.venus) // 2)
    state = trigger_own(state, pid, "on_global_parameter_increase", "venus", steps)
    state = gain_tr(state, pid, steps)
    return replace(state, venus=state.venus + 2 * steps)


def can_place_ocean(state: GameState) -> bool:
    return state.oceans < MAX_OCEANS


# ---- tiles ---------------------------------------------------------------------------
def place_tile(state: GameState, pid: str, space_id: str, tile: Tile) -> GameState:
    """Put `tile` on `space_id`, collect placement bonuses and fire `on_tile_placed`.

    This is the bare placement. Use `place_ocean`, `place_greenery` and `place_city`, which
    also move the global parameters.
    """
    if space_id in state.tiles:
        raise ValueError(f"space {space_id} is occupied")
    owner = state.reserved.get(space_id)
    if owner is not None and owner != pid:
        raise ValueError(f"space {space_id} is reserved by {owner}")
    if tile.type in B.OCEAN_TILES:
        tile = replace(tile, owner=None)
    state = replace(state, tiles=state.tiles.set(space_id, tile),
                    reserved=state.reserved.without(space_id))
    state = log(state, f"{pid} placed {tile.type} on {space_id}")

    space = B.SPACES[space_id]
    for bonus in sorted(set(space.bonus)):
        n = space.bonus.count(bonus)
        if bonus == "draw_card":
            state = draw_cards(state, pid, n)
        else:
            state = add_stock(state, pid, {"plant": "plants"}.get(bonus, bonus), n)
    adjacent_oceans = len(B.adjacent_with(state, space_id, B.is_ocean))
    if adjacent_oceans:
        state = add_stock(state, pid, "megacredits", OCEAN_ADJACENCY_BONUS * adjacent_oceans)

    return trigger_all(state, "on_tile_placed", pid, space_id, "mars")


def place_ocean(state: GameState, pid: str, space_id: str) -> GameState:
    if not can_place_ocean(state):
        return state
    state = place_tile(state, pid, space_id, Tile("ocean"))
    state = replace(state, oceans=state.oceans + 1)
    state = trigger_own(state, pid, "on_global_parameter_increase", "oceans", 1)
    return gain_tr(state, pid, 1)


def place_greenery(state: GameState, pid: str, space_id: str, raise_o2: bool = True) -> GameState:
    state = place_tile(state, pid, space_id, Tile("greenery", pid))
    return raise_oxygen(state, pid, 1) if raise_o2 else state


def place_city(state: GameState, pid: str, space_id: str, card_id: str | None = None) -> GameState:
    return place_tile(state, pid, space_id, Tile("city", pid, card_id))


def place_any(state: GameState, pid: str, space_id: str, tile_type: str, card_id: str | None = None) -> GameState:
    if tile_type == "ocean":
        return place_ocean(state, pid, space_id)
    if tile_type == "greenery":
        return place_greenery(state, pid, space_id)
    if tile_type == "city":
        return place_city(state, pid, space_id, card_id)
    return place_tile(state, pid, space_id, Tile(tile_type, pid, card_id))


def ask_place_tile(state: GameState, pid: str, tile_type: str, spaces: Iterable[str] | None = None,
                   rule: str | None = None, card_id: str | None = None, title: str = "",
                   priority: int = Priority.DEFAULT) -> GameState:
    """Queue a choice of space for `tile_type`, then place it.

    The spaces are worked out when the question is reached, not now, so that tiles placed in
    between are taken into account. Pass `spaces` only for a fixed list.
    """
    ctx = {"tile_type": tile_type, "card_id": card_id, "rule": rule,
           "spaces": tuple(spaces) if spaces is not None else None, "title": title}
    return defer(state, pid, "place.ask", ctx, priority=priority)


def ask_place_ocean(state: GameState, pid: str, title: str = "Select space for ocean") -> GameState:
    return ask_place_tile(state, pid, "ocean", rule="ocean", title=title, priority=Priority.PLACE_OCEAN_TILE)


def default_rule(tile_type: str) -> str:
    return {"ocean": "ocean", "greenery": "greenery", "city": "city"}.get(tile_type, "land")


@continuation("place.ask")
def _place_ask(state, pid, _choice, tile_type, card_id, rule, spaces, title):
    if tile_type == "ocean" and not can_place_ocean(state):
        return state
    if spaces is None:
        spaces = B.spaces_for(state, pid, rule or default_rule(tile_type))
    else:
        spaces = [s for s in spaces if s not in state.tiles]
    return ask(state, pid, kind="space", options=spaces, then="place.tile",
               ctx={"tile_type": tile_type, "card_id": card_id},
               title=title or f"Select space for {tile_type}", priority=Priority.COST)


@continuation("place.tile")
def _place_tile(state, pid, space_id, tile_type, card_id):
    return place_any(state, pid, space_id, tile_type, card_id)


# ---- paying --------------------------------------------------------------------------
def payment_sources(state: GameState, pid: str, tags: Iterable[str] = (),
                    steel: bool = False, titanium: bool = False) -> dict[str, tuple[int, int]]:
    """What `pid` can pay with: resource -> (units available, M€ value per unit).

    Steel pays for building tags and titanium for space tags; cards can add more sources
    through the `can_pay_with` hook (Helion's heat, Psychrophiles' microbes).
    """
    tags = set(tags)
    p = state.player(pid)
    out = {"megacredits": (p.stock.megacredits, 1)}
    if steel or "building" in tags:
        out["steel"] = (p.stock.steel, p.steel_value)
    if titanium or "space" in tags:
        out["titanium"] = (p.stock.titanium, p.titanium_value)
    if p.can_use_heat_as_mc:
        out["heat"] = (p.stock.heat, 1)
    if "plant" in tags and "PSYCHROPHILES" in p.tableau:
        # Psychrophiles: microbes on it pay 2 M€ each towards plant-tag cards.
        out["PSYCHROPHILES"] = (p.resources_on("PSYCHROPHILES"), 2)
    for extra in query_own(state, pid, "can_pay_with", frozenset(tags)):
        for key, (units, value) in (extra or {}).items():
            out[key] = (units, value)
    return out


def can_afford(state: GameState, pid: str, cost: int, **kwargs) -> bool:
    if cost <= 0:
        return True
    return sum(n * v for n, v in payment_sources(state, pid, **kwargs).values()) >= cost


def auto_payment(state: GameState, pid: str, cost: int, **kwargs) -> dict[str, int] | None:
    """Choose how to pay `cost`: alloys and card resources first, then M€, then heat.

    Diverges: the original asks the player how to pay. This picks for them, spending the
    resources that can only be used for payment before M€, and never wasting more than one
    alloy's worth of overpayment.
    """
    if cost <= 0:
        return {}
    sources = payment_sources(state, pid, **kwargs)
    order = [k for k in ("titanium", "steel") if k in sources]
    order += [k for k in sources if k not in ("titanium", "steel", "megacredits", "heat")]
    order += ["megacredits"] + (["heat"] if "heat" in sources else [])
    remaining, pay = cost, {}
    for key in order:
        units, value = sources[key]
        use = min(units, remaining // value)
        if use:
            pay[key] = use
            remaining -= use * value
    if remaining > 0:
        # Overpay with one more unit of the most valuable source still available.
        for key in order:
            units, value = sources[key]
            if units > pay.get(key, 0):
                pay[key] = pay.get(key, 0) + 1
                remaining -= value
                if remaining <= 0:
                    break
    if remaining > 0:
        return None
    return pay


def pay(state: GameState, pid: str, cost: int, **kwargs) -> GameState:
    payment = auto_payment(state, pid, cost, **kwargs)
    if payment is None:
        raise ValueError(f"{pid} can't afford {cost}")
    for key, units in payment.items():
        if key in RESOURCES:
            state = spend(state, pid, key, units)
        else:
            # A card resource, keyed by the card holding it.
            state = add_card_resources(state, pid, key, -units)
    return state


# ---- misc ----------------------------------------------------------------------------
def card_cost(state: GameState, pid: str, card_id: str) -> int:
    """A project card's cost after every discount in play."""
    c = card(card_id)
    discount = 0
    for cid in state.player(pid).tableau:
        d = CARDS[cid].card_discount
        if d:
            for entry in (d if isinstance(d, list) else [d]):
                if entry.get("tag") is None or entry["tag"].lower() in c.tags:
                    discount += entry.get("amount", 0)
    discount += sum(query_own(state, pid, "get_card_discount", card_id))
    # An event isn't in the tableau, but its discount still applies to the very next card
    # (Indentured Workers), as in the original's Player.getCardCost.
    last = state.player(pid).last_card_played
    if last is not None and card(last).type == "event":
        fn = get_hook(last, "get_card_discount")
        if fn is not None:
            discount += fn(state, pid, card_id)
    return max(0, c.cost - discount)


def set_context(state: GameState, **values) -> GameState:
    ctx = state.context
    for k, v in values.items():
        ctx = ctx.without(k) if v is None else ctx.set(k, v)
    return replace(state, context=ctx)


def set_card_data(state: GameState, pid: str, card_id: str, value) -> GameState:
    p = state.player(pid)
    return state.with_player(replace(p, card_data=p.card_data.set(card_id, value)))


__all__ = [name for name in dir() if not name.startswith("_")] + ["FMap"]
