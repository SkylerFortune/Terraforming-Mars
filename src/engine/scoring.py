"""Victory points, milestones and awards.

Only the Tharsis milestones and awards are modelled so far:

Milestones (8 M€ each, at most 3 claimed per game)
  Terraformer  35 TR
  Mayor        3 cities
  Gardener     3 greeneries
  Builder      8 building tags
  Planner      16 cards in hand

Awards (8, 14 then 20 M€; at most 3 funded; 5 VP to the winner, 2 VP to second place)
  Landlord     most tiles
  Banker       highest M€ production
  Scientist    most science tags
  Thermalist   most heat
  Miner        most steel and titanium
"""
from __future__ import annotations

from typing import Callable

from engine import board as B
from engine.behavior import count
from engine.cards import CARDS
from engine.game_state import GameState
from engine.primitives import get_hook, tag_count

MILESTONE_COST = 8
MAX_MILESTONES = 3
AWARD_COSTS = (8, 14, 20)
MAX_AWARDS = 3
MILESTONE_VP = 5
AWARD_VP = (5, 2)

THARSIS_MILESTONES: dict[str, tuple[Callable[[GameState, str], int], int]] = {
    "Terraformer": (lambda s, pid: s.player(pid).tr, 35),
    "Mayor": (lambda s, pid: len(B.cities(s, pid)), 3),
    "Gardener": (lambda s, pid: len(B.greeneries(s, pid)), 3),
    "Builder": (lambda s, pid: tag_count(s, pid, "building"), 8),
    "Planner": (lambda s, pid: len(s.player(pid).hand), 16),
}

THARSIS_AWARDS: dict[str, Callable[[GameState, str], int]] = {
    "Landlord": lambda s, pid: len(B.owned_tiles(s, pid)),
    "Banker": lambda s, pid: s.player(pid).production.megacredits,
    "Scientist": lambda s, pid: tag_count(s, pid, "science"),
    "Thermalist": lambda s, pid: s.player(pid).stock.heat,
    "Miner": lambda s, pid: s.player(pid).stock.steel + s.player(pid).stock.titanium,
}


# ---- milestones and awards -------------------------------------------------------------
def can_claim_milestone(state: GameState, pid: str, name: str) -> bool:
    if name not in state.milestones or len(state.claimed_milestones) >= MAX_MILESTONES:
        return False
    if any(m == name for m, _ in state.claimed_milestones):
        return False
    if state.player(pid).stock.megacredits < MILESTONE_COST:
        return False
    score, target = THARSIS_MILESTONES[name]
    return score(state, pid) >= target


def award_cost(state: GameState) -> int | None:
    n = len(state.funded_awards)
    return AWARD_COSTS[n] if n < MAX_AWARDS else None


def can_fund_award(state: GameState, pid: str, name: str) -> bool:
    cost = award_cost(state)
    if cost is None or name not in state.awards or any(a == name for a, _ in state.funded_awards):
        return False
    return state.player(pid).stock.megacredits >= cost


def award_winners(state: GameState, name: str) -> tuple[list[str], list[str]]:
    """(first place, second place). Ties share a place; there's no second place after a tie
    for first, and none at all in a two-player game."""
    score = THARSIS_AWARDS[name]
    scores = {p.id: score(state, p.id) for p in state.players}
    best = max(scores.values())
    first = [pid for pid, v in scores.items() if v == best]
    if len(first) > 1 or len(state.players) <= 2:
        return first, []
    rest = [v for v in scores.values() if v < best]
    if not rest:
        return first, []
    second_best = max(rest)
    return first, [pid for pid, v in scores.items() if v == second_best]


# ---- victory points ------------------------------------------------------------------
def card_vp(state: GameState, pid: str, card_id: str) -> int:
    hook = get_hook(card_id, "get_victory_points")
    if hook is not None:
        return hook(state, pid)
    vp = CARDS[card_id].victory_points
    if vp is None or vp == "special":
        return 0
    return count(state, pid, card_id, vp)


def score(state: GameState, pid: str) -> dict[str, int]:
    """A breakdown of `pid`'s victory points."""
    p = state.player(pid)
    cards = sum(card_vp(state, pid, cid) for cid in p.tableau + p.events)
    greenery = len(B.greeneries(state, pid))
    city = sum(len(B.adjacent_with(state, sid, B.is_greenery)) for sid in B.cities(state, pid))
    milestones = MILESTONE_VP * sum(1 for _, owner in state.claimed_milestones if owner == pid)
    awards = 0
    for name, _ in state.funded_awards:
        first, second = award_winners(state, name)
        if pid in first:
            awards += AWARD_VP[0]
        elif pid in second:
            awards += AWARD_VP[1]
    breakdown = {"tr": p.tr, "cards": cards, "greenery": greenery, "city": city,
                 "milestones": milestones, "awards": awards}
    breakdown["total"] = sum(breakdown.values())
    return breakdown


def final_scores(state: GameState) -> dict[str, dict[str, int]]:
    return {p.id: score(state, p.id) for p in state.players}


def ranking(state: GameState) -> list[str]:
    """Player ids, winner first. Ties are broken by M€ left, as in the rules."""
    scores = final_scores(state)
    return sorted(scores, key=lambda pid: (-scores[pid]["total"], -state.player(pid).stock.megacredits))
