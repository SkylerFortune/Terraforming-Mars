"""The interpreter for the data-driven part of cards: `behavior`, `action` and `firstAction`.

See `src/data/behavior_spec.md` for what each clause means in the original engine. Clauses
run in the fixed order `CLAUSE_ORDER`, not in JSON key order. Clauses the original defers
(tile placement, adding resources to cards, attacks, choices) are queued with
`engine.pending.defer` / `ask`, so they resolve after the current step.

Clauses from expansions this engine doesn't model yet (colonies, turmoil, moon, underworld)
make `can_execute` return False, so a card that needs them is simply never playable.
"""
from __future__ import annotations

import json
from typing import Any, Mapping

from engine import board as B
from engine.cards import CARDS, card
from engine.game_state import RESOURCES, GameState, Units
from engine.pending import Priority, ask, continuation, defer
from engine import primitives as P

CLAUSE_ORDER = (
    "or", "spend", "removeResourcesFromAnyCard", "lose", "production", "stock",
    "standardResource", "steelValue", "titaniumValue", "greeneryDiscount", "drawCard",
    "global", "tr", "addResources", "addResourcesToAnyCard", "decreaseAnyProduction",
    "removeAnyPlants", "colonies", "ocean", "city", "greenery", "tile", "turmoil", "moon",
    "underworld", "log",
)
IGNORED = frozenset({"title", "text", "log"})
UNSUPPORTED = frozenset({"colonies", "turmoil", "moon", "underworld"})

FIXED_SPACES = {"GANYMEDE_COLONY": B.GANYMEDE_COLONY, "PHOBOS_SPACE_HAVEN": B.PHOBOS_SPACE_HAVEN}


class UnsupportedBehavior(NotImplementedError):
    """A clause or countable from an expansion this engine doesn't model yet."""


# ---- counting ------------------------------------------------------------------------
def count(state: GameState, pid: str, card_id: str | None, c: Any) -> int:
    """Evaluate a Countable: a plain number, or an object describing what to count."""
    if isinstance(c, (int, float)):
        return int(c)
    if not isinstance(c, Mapping):
        raise UnsupportedBehavior(f"countable {c!r}")
    p = state.player(pid)
    total = 0
    in_tableau = card_id is not None and card_id in p.tableau

    def near(spaces: list[str]) -> list[str]:
        if "nextToThis" not in c:
            return spaces
        mine = [sid for sid, t in state.tiles.items() if t.card == card_id]
        if not mine:
            return []
        return [s for s in spaces if s in B.ADJACENT[mine[0]]]

    if "cities" in c:
        where = (c["cities"] or {}).get("where", "everywhere") if isinstance(c["cities"], Mapping) else "everywhere"
        owner = pid if c.get("all") is False else None
        total += len(near(B.cities(state, owner, where)))
    if "greeneries" in c:
        owner = pid if c.get("all") is False else None
        total += len(near(B.greeneries(state, owner)))
    if "oceans" in c:
        total += len(near(B.oceans(state)))
    if "tag" in c:
        tags = c["tag"] if isinstance(c["tag"], list) else [c["tag"]]
        tags = [t.lower() for t in tags]
        if not c.get("others"):
            total += sum(P.tag_count(state, pid, t) for t in tags)
            if card_id is not None and not in_tableau:
                total += sum(card(card_id).tags.count(t) for t in tags)
        if c.get("all") is True or c.get("others") is True:
            total += sum(P.tag_count(state, o.id, t) for o in state.opponents(pid) for t in tags)
    if "resourcesHere" in c:
        total += p.resources_on(card_id) if card_id else 0
    if "floaters" in c:
        total += sum(p.resources_on(cid) for cid in P.cards_with_resource(state, pid, "floater"))
    if "eventsPlayed" in c:
        if c.get("all") is True:
            total += sum(len(o.events) for o in state.players)
        else:
            total += len(p.events)
    for key in ("colonies", "moon", "underworld", "turmoil"):
        if key in c:
            raise UnsupportedBehavior(f"countable {key!r}")
    if "each" in c:
        total *= c["each"]
    if "per" in c:
        total //= c["per"]
    return total


def count_units(state: GameState, pid: str, card_id: str | None, units: Mapping) -> Units:
    return Units.of({r.lower(): count(state, pid, card_id, v) for r, v in units.items()})


# ---- locating behaviors (continuations store a path, not the dict) -------------------
def locate(card_id: str | None, field: str, branch: int | None, raw: str | None) -> Mapping:
    if raw is not None:
        b = json.loads(raw)
    else:
        b = card(card_id).raw[field]
    if branch is not None:
        b = b["or"]["behaviors"][branch]
    return b


# ---- can_execute ---------------------------------------------------------------------
def _target_cards_for_removal(state: GameState, pid: str, spec: Mapping) -> list[str]:
    rtype = spec["type"].lower()
    source = spec.get("source", "self")
    count_needed = 1
    out = []
    for p in state.players:
        if source == "self" and p.id != pid or source == "opponents" and p.id == pid:
            continue
        for cid in P.cards_with_resource(state, p.id, rtype, min_count=count_needed):
            if p.id != pid and (resources_protected(state, p.id, rtype) or CARDS[cid].protected_resources):
                continue
            out.append(cid)
    return out


def resources_protected(state: GameState, owner: str, resource_type: str) -> bool:
    """Protected Habitats shields its owner's plants, animals and microbes from opponents."""
    return "PROTECTED_HABITATS" in state.player(owner).tableau and resource_type in ("plants", "animal", "microbe")


def _players_for_decrease(state: GameState, pid: str, spec: Mapping) -> list[str]:
    resource = spec["type"].lower()
    n = spec.get("count", 1)
    out = []
    for p in state.players:
        if p.production.get(resource) - n >= (-5 if resource == "megacredits" else 0):
            out.append(p.id)
    return out


def can_execute(state: GameState, pid: str, card_id: str | None, behavior: Mapping) -> bool:
    try:
        return _can_execute(state, pid, card_id, behavior)
    except UnsupportedBehavior:
        return False


def _can_execute(state: GameState, pid: str, card_id: str | None, b: Mapping) -> bool:
    p = state.player(pid)
    for key in b:
        if key in UNSUPPORTED or (key not in CLAUSE_ORDER and key not in IGNORED):
            raise UnsupportedBehavior(f"clause {key!r}")
    if "or" in b:
        if not any(_safe(state, pid, card_id, sub) for sub in b["or"]["behaviors"]):
            return False
    if "spend" in b:
        s = b["spend"]
        if "megacredits" in s:
            if not P.can_afford(state, pid, s["megacredits"], steel=bool(s.get("canUseSteel")),
                                titanium=bool(s.get("canUseTitanium"))):
                return False
        for r in ("steel", "titanium", "plants", "energy", "heat"):
            if r in s and p.stock.get(r) < s[r]:
                return False
        if "resourcesHere" in s and p.resources_on(card_id) < s["resourcesHere"]:
            return False
        if "resourceFromAnyCard" in s:
            if not P.cards_with_resource(state, pid, s["resourceFromAnyCard"]["type"].lower(), min_count=1):
                return False
        if "cards" in s and len([c for c in p.hand if c != card_id]) < s["cards"]:
            return False
        if "corruption" in s:
            raise UnsupportedBehavior("corruption")
    if "removeResourcesFromAnyCard" in b:
        if not _target_cards_for_removal(state, pid, b["removeResourcesFromAnyCard"]) and not state.is_solo:
            return False
    if "production" in b:
        if not P.can_adjust_production(state, pid, count_units(state, pid, card_id, b["production"])):
            return False
    if "stock" in b:
        count_units(state, pid, card_id, b["stock"])
    if "decreaseAnyProduction" in b and not state.is_solo:
        if not _players_for_decrease(state, pid, b["decreaseAnyProduction"]):
            return False
    if "addResourcesToAnyCard" in b:
        spec = b["addResourcesToAnyCard"]
        if isinstance(spec, Mapping) and spec.get("mustHaveCard"):
            if not _cards_for_adding(state, pid, card_id, spec):
                return False
    if "city" in b:
        c = b["city"]
        if "space" in c:
            if FIXED_SPACES[c["space"]] in state.tiles:
                return False
        elif not B.spaces_for(state, pid, c.get("on", "city")):
            return False
    if "greenery" in b and not B.spaces_for(state, pid, b["greenery"].get("on", "greenery")):
        return False
    if "tile" in b and not B.spaces_for(state, pid, b["tile"].get("on", "land")):
        return False
    return True


def _safe(state, pid, card_id, b) -> bool:
    try:
        return _can_execute(state, pid, card_id, b)
    except UnsupportedBehavior:
        return False


def _cards_for_adding(state: GameState, pid: str, card_id: str | None, spec: Mapping) -> list[str]:
    rtype = spec.get("type")
    out = P.cards_with_resource(state, pid, rtype.lower() if rtype else None,
                                tag=spec["tag"].lower() if spec.get("tag") else None,
                                min_count=spec.get("min", 0))
    if spec.get("excludeThis"):
        out = [c for c in out if c != card_id]
    # The card being played is not in the tableau yet but is a valid target for its own resources.
    if (card_id and card_id not in out and not spec.get("excludeThis")
            and card_id in CARDS and CARDS[card_id].resource_type
            and (rtype is None or CARDS[card_id].resource_type == rtype.lower())
            and spec.get("min", 0) == 0 and card_id not in state.player(pid).tableau
            and CARDS[card_id].type != "event"):
        out.append(card_id)
    return out


# ---- execute -------------------------------------------------------------------------
def execute(state: GameState, pid: str, card_id: str | None, field: str = "behavior",
            branch: int | None = None, raw: str | None = None, done: tuple[str, ...] = ()) -> GameState:
    """Run the behavior found at (card_id, field[, branch]), skipping clauses in `done`.

    `raw` is a JSON string for a behavior that isn't stored on a card.
    """
    b = locate(card_id, field, branch, raw)
    where = {"card_id": card_id, "field": field, "branch": branch, "raw": raw}
    done = set(done)
    for key in CLAUSE_ORDER:
        if key not in b or key in done:
            continue
        done.add(key)
        state, stop = _CLAUSES[key](state, pid, card_id, b[key], where, tuple(sorted(done)))
        if stop:
            return state
    return state


def execute_dict(state: GameState, pid: str, card_id: str | None, behavior: Mapping) -> GameState:
    """Run a behavior given as a dict (for hooks that build one on the fly)."""
    return execute(state, pid, card_id, raw=json.dumps(behavior, sort_keys=True))


def _resume_later(state, pid, where, done, priority=Priority.DEFAULT):
    return defer(state, pid, "behavior.remainder", {**where, "done": done}, priority=priority)


@continuation("behavior.remainder")
def _remainder(state, pid, _choice, card_id, field, branch, raw, done):
    return execute(state, pid, card_id, field, branch, raw, done)


def _or(state, pid, card_id, spec, where, done):
    if where["branch"] is not None:
        raise UnsupportedBehavior("nested or")
    options = [i for i, sub in enumerate(spec["behaviors"]) if _safe(state, pid, card_id, sub)]
    if len(options) == 1 and spec.get("autoSelect"):
        state = execute(state, pid, card_id, where["field"], options[0], where["raw"])
    else:
        titles = tuple(spec["behaviors"][i].get("title", f"Option {i + 1}") for i in options)
        state = ask(state, pid, kind="option", options=titles, then="behavior.or",
                    ctx={**where, "indexes": tuple(options), "titles": titles},
                    title=spec.get("title", "Select one option"))
    return state, False


@continuation("behavior.or")
def _or_chosen(state, pid, choice, card_id, field, branch, raw, indexes, titles):
    return execute(state, pid, card_id, field, indexes[titles.index(choice)], raw)


def _spend(state, pid, card_id, spec, where, done):
    if "megacredits" in spec:
        state = P.pay(state, pid, spec["megacredits"], steel=bool(spec.get("canUseSteel")),
                      titanium=bool(spec.get("canUseTitanium")))
    for r in ("steel", "titanium", "plants", "energy", "heat"):
        if r in spec:
            state = P.spend(state, pid, r, spec[r])
    if "resourcesHere" in spec:
        state = P.add_card_resources(state, pid, card_id, -spec["resourcesHere"])
    if "resourceFromAnyCard" in spec:
        rtype = spec["resourceFromAnyCard"]["type"].lower()
        state = ask(state, pid, kind="card", options=P.cards_with_resource(state, pid, rtype, min_count=1),
                    then="behavior.spend_card_resource", ctx={**where, "done": done},
                    title=f"Remove 1 {rtype} from a card", priority=Priority.COST)
        return state, True
    if "cards" in spec:
        hand = tuple(c for c in state.player(pid).hand if c != card_id)
        state = ask(state, pid, kind="cards", options=hand, min=spec["cards"], max=spec["cards"],
                    then="behavior.spend_cards", ctx={**where, "done": done},
                    title=f"Discard {spec['cards']} card(s)", priority=Priority.COST)
        return state, True
    return state, False


@continuation("behavior.spend_card_resource")
def _spend_card_resource(state, pid, chosen, card_id, field, branch, raw, done):
    state = P.add_card_resources(state, pid, chosen, -1)
    return execute(state, pid, card_id, field, branch, raw, done)


@continuation("behavior.spend_cards")
def _spend_cards(state, pid, chosen, card_id, field, branch, raw, done):
    state = P.remove_from_hand(state, pid, chosen)
    state = P.discard_cards(state, chosen)
    return execute(state, pid, card_id, field, branch, raw, done)


def _remove_resources(state, pid, card_id, spec, where, done):
    targets = _target_cards_for_removal(state, pid, spec)
    n = count(state, pid, card_id, spec.get("count", 1))
    state = ask(state, pid, kind="card", options=targets, then="behavior.remove_from_card",
                ctx={**where, "done": done, "n": n},
                title=f"Remove {n} {spec['type'].lower()} from a card")
    if not targets:
        return _resume_later(state, pid, where, done), True
    return state, True


@continuation("behavior.remove_from_card")
def _remove_from_card(state, pid, target, card_id, field, branch, raw, done, n):
    owner = P.resource_owner(state, target)
    state = P.add_card_resources(state, owner, target, -n)
    return execute(state, pid, card_id, field, branch, raw, done)


def _lose(state, pid, card_id, spec, where, done):
    for kind in ("stock", "production"):
        if kind in spec:
            units = count_units(state, pid, card_id, spec[kind])
            for r, v in units.items():
                if v > 0:
                    state = (P.add_stock if kind == "stock" else P.add_production)(state, pid, r, -v)
    return state, False


def _production(state, pid, card_id, spec, where, done):
    return P.add_production_units(state, pid, count_units(state, pid, card_id, spec)), False


def _stock(state, pid, card_id, spec, where, done):
    return P.add_stock_units(state, pid, count_units(state, pid, card_id, spec)), False


def _standard_resource(state, pid, card_id, spec, where, done):
    n = spec if isinstance(spec, int) else spec.get("count", 1)
    state = ask(state, pid, kind="option", options=RESOURCES, then="behavior.standard_resource",
                ctx={"n": n}, title=f"Gain {n} of a standard resource")
    return state, False


@continuation("behavior.standard_resource")
def _standard_resource_chosen(state, pid, resource, n):
    return P.add_stock(state, pid, resource, n)


def _modifier(attr, sign=1):
    def run(state, pid, card_id, spec, where, done):
        p = state.player(pid)
        return state.update_player(pid, **{attr: getattr(p, attr) + sign * spec}), False
    return run


def _draw(state, pid, card_id, spec, where, done):
    if isinstance(spec, int):
        return P.draw_cards(state, pid, spec), False
    n = spec.get("count", 1)
    if spec.get("tag") or spec.get("type") or spec.get("resource"):
        return draw_matching(state, pid, n, tag=spec.get("tag"), card_type=spec.get("type")), False
    state, drawn = P.draw(state, n)
    if spec.get("pay"):
        return ask(state, pid, kind="cards", options=drawn, min=0, max=len(drawn),
                   then="behavior.buy_drawn", ctx={"drawn": drawn},
                   title="Buy the drawn card(s) for 3 M€ each"), False
    keep = spec.get("keep", n)
    return ask(state, pid, kind="cards", options=drawn, min=keep, max=keep,
               then="behavior.keep_drawn", ctx={"drawn": drawn},
               title=f"Keep {keep} of the drawn cards"), False


def draw_matching(state: GameState, pid: str, n: int, tag: str | None = None,
                  card_type: str | None = None) -> GameState:
    """Reveal cards until `n` match, keep those and discard the rest."""
    kept: list[str] = []
    for _ in range(200):
        if len(kept) >= n:
            break
        state, drawn = P.draw(state, 1)
        if not drawn:
            break
        c = card(drawn[0])
        if (tag is None or tag.lower() in c.tags) and (card_type is None or c.type == card_type.lower()):
            kept.append(drawn[0])
        else:
            state = P.discard_cards(state, drawn)
    return state.update_player(pid, hand=state.player(pid).hand + tuple(kept))


@continuation("behavior.keep_drawn")
def _keep_drawn(state, pid, kept, drawn):
    kept = tuple(kept)
    p = state.player(pid)
    state = state.update_player(pid, hand=p.hand + kept)
    return P.discard_cards(state, [c for c in drawn if c not in kept])


@continuation("behavior.buy_drawn")
def _buy_drawn(state, pid, bought, drawn):
    bought = tuple(bought or ())
    affordable = []
    for cid in bought:
        if state.player(pid).stock.megacredits >= 3:
            state = P.spend(state, pid, "megacredits", 3)
            affordable.append(cid)
    p = state.player(pid)
    state = state.update_player(pid, hand=p.hand + tuple(affordable))
    return P.discard_cards(state, [c for c in drawn if c not in affordable])


def _global(state, pid, card_id, spec, where, done):
    if "temperature" in spec:
        state = P.raise_temperature(state, pid, spec["temperature"])
    if "oxygen" in spec:
        state = P.raise_oxygen(state, pid, spec["oxygen"])
    if "venus" in spec:
        state = P.raise_venus(state, pid, spec["venus"])
    return state, False


def _tr(state, pid, card_id, spec, where, done):
    return P.gain_tr(state, pid, count(state, pid, card_id, spec)), False


def _add_resources(state, pid, card_id, spec, where, done):
    n = count(state, pid, card_id, spec)
    return defer(state, pid, "behavior.add_here", {"card_id": card_id, "n": n}), False


@continuation("behavior.add_here")
def _add_here(state, pid, _choice, card_id, n):
    return P.add_card_resources(state, pid, card_id, n)


def _add_to_any(state, pid, card_id, spec, where, done):
    for entry in (spec if isinstance(spec, list) else [spec]):
        n = count(state, pid, card_id, entry.get("count", 1))
        if n > 0:
            state = defer(state, pid, "behavior.add_to_any",
                          {"card_id": card_id, "n": n, "spec": json.dumps(entry, sort_keys=True)})
    return state, False


@continuation("behavior.add_to_any")
def _add_to_any_run(state, pid, _choice, card_id, n, spec):
    entry = json.loads(spec)
    targets = _cards_for_adding(state, pid, card_id, entry)
    rtype = (entry.get("type") or "resource").lower()
    return ask(state, pid, kind="card", options=targets, then="behavior.add_to_card",
               ctx={"n": n}, title=f"Add {n} {rtype}(s) to a card", priority=Priority.COST)


@continuation("behavior.add_to_card")
def _add_to_card(state, pid, target, n):
    return P.add_card_resources(state, pid, target, n)


def _decrease_any(state, pid, card_id, spec, where, done):
    resource = spec["type"].lower()
    n = spec.get("count", 1)
    targets = _players_for_decrease(state, pid, spec)
    # Reducing your own production is allowed, but only as a last resort.
    others = [t for t in targets if t != pid]
    return ask(state, pid, kind="player", options=others or targets, then="behavior.decrease_production",
               ctx={"resource": resource, "n": n}, title=f"Decrease {resource} production {n} step(s)",
               priority=Priority.ATTACK_OPPONENT), False


@continuation("behavior.decrease_production")
def _decrease_production(state, pid, target, resource, n):
    return P.add_production(state, target, resource, -n)


def _remove_plants(state, pid, card_id, spec, where, done):
    n = count(state, pid, card_id, spec)
    targets = [o.id for o in state.opponents(pid)
               if o.stock.plants > 0 and not resources_protected(state, o.id, "plants")]
    return ask(state, pid, kind="player", options=targets, allow_pass=True, then="behavior.remove_plants",
               ctx={"n": n}, title=f"Remove up to {n} plants from a player",
               priority=Priority.ATTACK_OPPONENT), False


@continuation("behavior.remove_plants")
def _remove_plants_chosen(state, pid, target, n):
    if target is None:
        return state
    return P.add_stock(state, target, "plants", -n)


def _ocean(state, pid, card_id, spec, where, done):
    rule = spec.get("on", "ocean")
    for i in range(spec.get("count", 1)):
        state = P.ask_place_tile(state, pid, "ocean", rule=rule, priority=Priority.PLACE_OCEAN_TILE,
                                 title="Select space for ocean" + (f" ({i + 1})" if spec.get("count") else ""))
    return state, False


def _city(state, pid, card_id, spec, where, done):
    if "space" in spec:
        return P.place_city(state, pid, FIXED_SPACES[spec["space"]], card_id), False
    return P.ask_place_tile(state, pid, "city", rule=spec.get("on", "city"), card_id=card_id), False


def _greenery(state, pid, card_id, spec, where, done):
    return P.ask_place_tile(state, pid, "greenery", rule=spec.get("on", "greenery")), False


def _tile(state, pid, card_id, spec, where, done):
    return P.ask_place_tile(state, pid, spec["type"], rule=spec.get("on", "land"), card_id=card_id,
                            title=spec.get("title", "")), False


def _unsupported(state, pid, card_id, spec, where, done):
    raise UnsupportedBehavior("clause from an expansion that isn't modelled")


def _noop(state, pid, card_id, spec, where, done):
    return state, False


_CLAUSES = {
    "or": _or, "spend": _spend, "removeResourcesFromAnyCard": _remove_resources, "lose": _lose,
    "production": _production, "stock": _stock, "standardResource": _standard_resource,
    "steelValue": _modifier("steel_value"), "titaniumValue": _modifier("titanium_value"),
    "greeneryDiscount": _modifier("plants_per_greenery", -1), "drawCard": _draw,
    "global": _global, "tr": _tr, "addResources": _add_resources,
    "addResourcesToAnyCard": _add_to_any, "decreaseAnyProduction": _decrease_any,
    "removeAnyPlants": _remove_plants, "colonies": _unsupported, "ocean": _ocean,
    "city": _city, "greenery": _greenery, "tile": _tile, "turmoil": _unsupported,
    "moon": _unsupported, "underworld": _unsupported, "log": _noop,
}


def on_discard(state: GameState, pid: str, card_id: str) -> GameState:
    """Undo a card's persistent modifiers when it leaves play."""
    b = card(card_id).behavior or {}
    p = state.player(pid)
    changes = {}
    if "steelValue" in b:
        changes["steel_value"] = p.steel_value - b["steelValue"]
    if "titaniumValue" in b:
        changes["titanium_value"] = p.titanium_value - b["titaniumValue"]
    if "greeneryDiscount" in b:
        changes["plants_per_greenery"] = p.plants_per_greenery + b["greeneryDiscount"]
    return state.update_player(pid, **changes) if changes else state
