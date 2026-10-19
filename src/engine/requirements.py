"""Card requirements ("requires 5% oxygen", "requires 2 science tags", ...).

Global requirements can be relaxed by `globalParameterRequirementBonus` in the card data
(Adaptation Technology, Inventrix) and by the `get_global_parameter_requirement_bonus` hook.
The bonus is in steps: one step is 2 °C, 1 % oxygen, 1 ocean or 2 % Venus.
"""
from __future__ import annotations

from typing import Mapping

from engine import board as B
from engine.cards import CARDS
from engine.game_state import GameState
from engine.primitives import query_own, tag_count

STEP_SIZE = {"temperature": 2, "oxygen": 1, "oceans": 1, "venus": 2}
GLOBAL_PARAMETERS = tuple(STEP_SIZE)


class UnsupportedRequirement(NotImplementedError):
    """A requirement from an expansion this engine doesn't model yet."""


def requirement_bonus(state: GameState, pid: str, parameter: str) -> int:
    """How many steps `pid` may ignore on `parameter`'s requirements."""
    steps = 0
    for cid in state.player(pid).tableau:
        bonus = CARDS[cid].global_parameter_requirement_bonus
        if bonus and (bonus.get("parameter") is None or bonus["parameter"].lower() == parameter):
            steps += bonus.get("steps", 0)
    steps += sum(query_own(state, pid, "get_global_parameter_requirement_bonus", parameter))
    return steps


def global_value(state: GameState, parameter: str) -> int:
    return {"temperature": state.temperature, "oxygen": state.oxygen,
            "oceans": state.oceans, "venus": state.venus}[parameter]


def _compare(value: int, target: int, is_max: bool) -> bool:
    return value <= target if is_max else value >= target


def meets(state: GameState, pid: str, req: Mapping, ignore_global: bool = False) -> bool:
    is_max = bool(req.get("max"))
    for parameter in GLOBAL_PARAMETERS:
        if parameter in req:
            if ignore_global:
                return True
            slack = requirement_bonus(state, pid, parameter) * STEP_SIZE[parameter]
            value = global_value(state, parameter) + (-slack if is_max else slack)
            return _compare(value, req[parameter], is_max)
    if "tag" in req:
        tag = req["tag"].lower()
        count = req.get("count", 1)
        if req.get("all"):
            have = sum(tag_count(state, p.id, tag) for p in state.players)
        else:
            have = tag_count(state, pid, tag)
        return _compare(have, count, is_max)
    if "production" in req:
        resource = req["production"].lower()
        resource = "megacredits" if resource == "megacredits" else resource
        return _compare(state.player(pid).production.get(resource), req.get("count", 1), is_max)
    if "cities" in req:
        owner = None if req.get("all") else pid
        return _compare(len(B.cities(state, owner)), req["cities"], is_max)
    if "greeneries" in req:
        owner = None if req.get("all") else pid
        return _compare(len(B.greeneries(state, owner)), req["greeneries"], is_max)
    if "tr" in req:
        return _compare(state.player(pid).tr, req["tr"], is_max)
    raise UnsupportedRequirement(f"requirement not supported yet: {dict(req)}")


def requirements_met(state: GameState, pid: str, card_id: str, ignore_global: bool = False) -> bool:
    for req in CARDS[card_id].requirements:
        if not meets(state, pid, req, ignore_global):
            return False
    return True
