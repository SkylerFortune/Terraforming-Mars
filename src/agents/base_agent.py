"""The interface every player agent implements."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from engine.game_state import GameState, Pending


class BaseAgent(ABC):
    """Answers the engine's questions for one player.

    `choose` gets the whole state and the question at the front of `state.pending`, and
    returns a valid answer for it:

      * one of `pending.options` for a single choice,
      * a tuple of distinct options, `pending.min` to `pending.max` long, when `pending.multi`,
      * `None` to pass, when `pending.allow_pass` is set.
    """

    @abstractmethod
    def choose(self, state: GameState, pending: Pending) -> Any:
        ...
