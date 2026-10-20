"""An agent that answers every question at random (seeded, so games are reproducible)."""
from __future__ import annotations

import random
from typing import Any

from agents.base_agent import BaseAgent
from engine.game_state import GameState, Pending
from engine.primitives import MAX_OCEANS, MAX_TEMPERATURE

PASS_CHANCE = 0.1
SELL_PATENTS = "SELL_PATENTS_STANDARD_PROJECT"
# Relative chance of each kind of action, when any of that kind is legal.
KIND_WEIGHTS = {"play": 4.0, "action": 2.0, "first_action": 1.0, "standard_project": 1.0,
                "sell_patents": 0.25, "convert_plants": 2.0, "convert_heat": 2.0,
                "claim_milestone": 2.0, "fund_award": 0.5}


class RandomAgent(BaseAgent):
    def __init__(self, seed: int | str | None = None) -> None:
        self.rng = random.Random(seed)

    def choose(self, state: GameState, pending: Pending) -> Any:
        options = list(pending.options)
        if pending.multi:
            hi = min(pending.max, len(options))
            k = self.rng.randint(min(pending.min, hi), hi)
            return tuple(self.rng.sample(options, k))
        if pending.allow_pass and (not options or self.rng.random() < PASS_CHANCE):
            return None
        if pending.kind == "action":
            return self._choose_action(state, options)
        return self.rng.choice(options)

    def _choose_action(self, state: GameState, actions: list[tuple]) -> tuple:
        """Pick a kind of action first, then one action of that kind.

        Choosing uniformly from the whole list would mostly pick standard projects, which are
        nearly always legal (Sell Patents above all), so cards would rarely be played. Projects
        that would do nothing (an asteroid at max temperature) are skipped, as a player would.
        """
        groups: dict[str, list[tuple]] = {}
        for a in actions:
            if a[0] in ("pass", "end_turn") or self._wasted(state, a):
                continue
            key = "sell_patents" if a == ("standard_project", SELL_PATENTS) else a[0]
            groups.setdefault(key, []).append(a)
        if not groups or self.rng.random() < PASS_CHANCE:
            return self.rng.choice(actions)
        kinds = sorted(groups)
        weights = [KIND_WEIGHTS.get(k, 1.0) for k in kinds]
        kind = self.rng.choices(kinds, weights)[0]
        return self.rng.choice(groups[kind])

    @staticmethod
    def _wasted(state: GameState, action: tuple) -> bool:
        if action[0] != "standard_project":
            return False
        if action[1] == "ASTEROID_STANDARD_PROJECT":
            return state.temperature >= MAX_TEMPERATURE
        if action[1] == "AQUIFER_STANDARD_PROJECT":
            return state.oceans >= MAX_OCEANS
        return False
