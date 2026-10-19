"""Pending choices, deferred steps and continuations.

The engine never pauses inside a function. When an effect needs a decision it records a
`Pending` question on the state and returns; when an effect must happen "later" (the
original engine's deferred actions) it records a `Pending` with `kind="auto"`. Both live in
one queue, `state.pending`, ordered by priority and then by insertion, exactly like the
original `DeferredActionsQueue`.

The continuation is a string key plus data, never a closure:

    return ask(state, owner, kind="space", options=spaces, then="flooding.space")

    @continuation("flooding.space")
    def flooding_space(state, owner, choice): ...

Driving the queue:

    state = advance(state)              # run auto steps until a question (or nothing) is left
    question = state.pending[0]         # what the engine is waiting for
    state = resume(state, choice)       # answer it, then advance again
"""
from __future__ import annotations

from dataclasses import replace
from enum import IntEnum
from typing import Any, Callable, Iterable

from engine.game_state import GameState, Pending

CONTINUATIONS: dict[str, Callable[..., GameState]] = {}


class Priority(IntEnum):
    """Order in which queued steps resolve (lower first). Mirrors the original's Priority."""

    DECLARE_CLONE_TAG = 0
    COST = 1
    MAYBE_BLOCK_ATTACK = 2
    BEFORE_PHARMACY_UNION = 3
    PHARMACY_UNION = 4
    BEFORE_OPPONENT_TRIGGER = 5
    OPPONENT_TRIGGER = 6
    HYPERSPACE_DRIVE_PROTOTYPE = 7
    OLYMPUS_CONFERENCE = 8
    SPONSORED_ACADEMIES = 9
    DRAW_CARDS = 10
    BUILD_COLONY = 11
    INCREASE_COLONY_TRACK = 12
    PLACE_OCEAN_TILE = 13
    IDENTIFY_UNDERGROUND_RESOURCE = 14
    EXCAVATE_UNDERGROUND_RESOURCE = 15
    DEFAULT = 16
    DISCARD_AND_DRAW = 17
    ATTACK_OPPONENT = 18
    GAIN_RESOURCE_OR_PRODUCTION = 19
    LOSE_RESOURCE_OR_PRODUCTION = 20
    DECREASE_COLONY_TRACK_AFTER_TRADE = 21
    DISCARD_CARDS = 22
    ROBOTIC_WORKFORCE = 23
    BACK_OF_THE_LINE = 24
    # Engine-only: the game flow (next turn, next phase) runs once everything else is done.
    FLOW = 100


class InvalidChoice(ValueError):
    """The answer given to a pending question is not one of its options."""


def continuation(key: str):
    """Register a function as the continuation for `key`.

    The function is called as `fn(state, player_id, choice, **ctx)` and returns a new state.
    """
    def deco(fn: Callable[..., GameState]) -> Callable[..., GameState]:
        if key in CONTINUATIONS:
            raise ValueError(f"duplicate continuation {key!r}")
        CONTINUATIONS[key] = fn
        return fn
    return deco


def _ctx(ctx: Any) -> tuple[tuple[str, Any], ...]:
    if isinstance(ctx, dict):
        return tuple(sorted(ctx.items()))
    return tuple(ctx)


def _enqueue(state: GameState, item: Pending) -> GameState:
    item = replace(item, seq=state.pending_seq)
    queue = state.pending + (item,)
    queue = tuple(sorted(queue, key=lambda p: (p.priority, p.seq)))
    return replace(state, pending=queue, pending_seq=state.pending_seq + 1)


def ask(state: GameState, player: str, *, kind: str, options: Iterable, then: str,
        ctx: Any = (), allow_pass: bool = False, min: int = 1, max: int = 1,
        title: str = "", priority: int = Priority.DEFAULT) -> GameState:
    """Queue a question for `player`. Returns the state unchanged if there is nothing to choose.

    With `min == max == 1` the answer is one of `options`. Otherwise it is a tuple of distinct
    options whose length is between `min` and `max`. `allow_pass` also accepts `None`.
    """
    if then not in CONTINUATIONS:       # fail fast on typos
        raise KeyError(f"no continuation registered for {then!r}")
    options = tuple(options)
    if not options and not allow_pass and min > 0:
        return state
    return _enqueue(state, Pending(player=player, kind=kind, then=then, options=options,
                                   ctx=_ctx(ctx), min=min, max=max, allow_pass=allow_pass,
                                   title=title, priority=int(priority)))


def defer(state: GameState, player: str, then: str, ctx: Any = (),
          priority: int = Priority.DEFAULT) -> GameState:
    """Queue a step that runs `then` later, without asking anyone anything."""
    if then not in CONTINUATIONS:
        raise KeyError(f"no continuation registered for {then!r}")
    return _enqueue(state, Pending(player=player, kind="auto", then=then, ctx=_ctx(ctx),
                                   priority=int(priority)))


def is_valid_choice(pending: Pending, choice: Any) -> bool:
    if choice is None:
        return pending.allow_pass or (pending.multi and pending.min == 0)
    if not pending.multi:
        return choice in pending.options
    if not isinstance(choice, tuple) or len(set(choice)) != len(choice):
        return False
    return pending.min <= len(choice) <= pending.max and all(c in pending.options for c in choice)


def _run(state: GameState, item: Pending, choice: Any) -> GameState:
    fn = CONTINUATIONS[item.then]
    return fn(state, item.player, choice, **item.context)


def advance(state: GameState, auto_single: bool = True) -> GameState:
    """Run queued steps until the front of the queue is a real question, or the queue is empty.

    With `auto_single`, a question with exactly one possible answer is answered automatically.
    """
    while state.pending:
        head = state.pending[0]
        if head.kind == "auto":
            state = _run(replace(state, pending=state.pending[1:]), head, None)
            continue
        if auto_single and not head.multi and not head.allow_pass and len(head.options) == 1:
            state = _run(replace(state, pending=state.pending[1:]), head, head.options[0])
            continue
        if head.multi and (head.max == 0 or not head.options) and head.min == 0:
            # Nothing can be picked, so the only answer is "none of them".
            state = _run(replace(state, pending=state.pending[1:]), head, ())
            continue
        break
    return state


def resume(state: GameState, choice: Any, auto_single: bool = True) -> GameState:
    """Answer the question at the front of the queue, then advance."""
    if not state.pending:
        raise InvalidChoice("nothing is pending")
    head = state.pending[0]
    if head.kind == "auto":
        raise InvalidChoice("the front of the queue is not a question; call advance() first")
    if head.multi and isinstance(choice, list):
        choice = tuple(choice)
    if not is_valid_choice(head, choice):
        raise InvalidChoice(f"{choice!r} is not a valid answer to {head.kind!r} ({head.title})")
    state = _run(replace(state, pending=state.pending[1:]), head, choice)
    return advance(state, auto_single)
