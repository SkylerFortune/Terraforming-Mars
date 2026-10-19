"""Small builders for hook tests: a bare game state and ways to drive it."""
from __future__ import annotations

from dataclasses import replace

import engine.hooks  # noqa: F401  (registers hooks and continuations)
from engine import actions as A
from engine.cards import cards_for
from engine.game_state import FMap, GameOptions, GameState, PlayerState, Tile, Units
from engine.pending import advance, resume
from engine.scoring import THARSIS_AWARDS, THARSIS_MILESTONES


def make_state(n_players: int = 2, **kwargs) -> GameState:
    """An action-phase state with empty players and the full project deck, unshuffled."""
    players = tuple(PlayerState(id=f"p{i + 1}") for i in range(n_players))
    deck = tuple(cards_for(("base", "corpera", "prelude"), {"automated", "active", "event"}))
    state = GameState(players=players, options=GameOptions(log=False), phase="action", deck=deck,
                      milestones=tuple(THARSIS_MILESTONES), awards=tuple(THARSIS_AWARDS))
    return replace(state, **kwargs)


def give(state: GameState, pid: str, *, stock=None, production=None, tableau=(), hand=(),
         card_resources=None, **fields) -> GameState:
    """Add to a player's stock, production, tableau, hand and card resources."""
    p = state.player(pid)
    if stock:
        p = replace(p, stock=p.stock + Units(**stock))
    if production:
        p = replace(p, production=p.production + Units(**production))
    if card_resources:
        res = p.card_resources
        for cid, n in card_resources.items():
            res = res.set(cid, res.get(cid, 0) + n)
        p = replace(p, card_resources=res)
    p = replace(p, tableau=p.tableau + tuple(tableau), hand=p.hand + tuple(hand), **fields)
    return state.with_player(p)


def tile(state: GameState, space_id: str, type_: str, owner: str | None = None) -> GameState:
    """Put a tile on the board directly, with no bonuses or triggers."""
    return replace(state, tiles=state.tiles.set(space_id, Tile(type_, owner)))


def play(state: GameState, pid: str, card_id: str, pay: bool = False) -> GameState:
    """Play `card_id` (from hand if it's there) and run until the next question."""
    state = A.play_card(state, pid, card_id, pay=pay)
    return advance(state)


def act(state: GameState, pid: str, card_id: str) -> GameState:
    return advance(A.use_action(state, pid, card_id))


def answer(state: GameState, *choices) -> GameState:
    """Answer the next questions in order."""
    for c in choices:
        state = resume(state, c)
    return state


def question(state: GameState):
    return state.pending[0] if state.pending else None


__all__ = ["make_state", "give", "tile", "play", "act", "answer", "question", "FMap", "Units"]
