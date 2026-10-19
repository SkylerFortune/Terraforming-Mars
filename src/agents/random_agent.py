"""An agent that answers every question at random (seeded, so games are reproducible)."""
from __future__ import annotations

import random
from typing import Any

from agents.base_agent import BaseAgent
from engine.game_state import GameState, Pending

PASS_CHANCE = 0.1


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
            return self._choose_action(options)
        return self.rng.choice(options)

    def _choose_action(self, actions: list[tuple]) -> tuple:
        # Passing at random would end most games in a handful of generations, so prefer doing
        # something whenever anything else is possible.
        useful = [a for a in actions if a[0] not in ("pass", "end_turn")]
        if useful and self.rng.random() > PASS_CHANCE:
            return self.rng.choice(useful)
        return self.rng.choice(actions)
