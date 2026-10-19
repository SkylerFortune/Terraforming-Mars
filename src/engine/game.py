"""Setting up a game and moving it through its phases.

The whole game is a sequence of questions. `new_game` returns a state that is waiting for
the first one; each answer goes through `engine.pending.resume`, which runs everything up to
the next question. The flow of turns and phases is itself made of queued steps (with
`Priority.FLOW`), so it always runs after every effect of the current action has resolved.

    state = new_game(["p1", "p2"], seed=1)
    while not is_over(state):
        question = state.pending[0]
        state = resume(state, agent_for(question.player).choose(state, question))
"""
from __future__ import annotations

from dataclasses import replace
from typing import Sequence

from engine import actions as A
from engine import board as B
from engine import primitives as P
from engine import scoring as S
from engine.cards import CARDS, card, cards_for
from engine.game_state import FMap, GameOptions, GameState, PlayerState, Units
from engine.pending import Priority, advance, ask, continuation, defer
import engine.hooks  # noqa: F401  (registers every hook and its continuations)

STARTING_PROJECT_CARDS = 10
CORPORATIONS_DEALT = 2
PRELUDES_DEALT = 4
PRELUDES_KEPT = 2
RESEARCH_CARDS = 4
CARD_PRICE = 3
STARTING_TR = 20

EXCLUDED_CORPORATIONS = frozenset({"BEGINNER_CORPORATION"})


def is_over(state: GameState) -> bool:
    return state.phase == "end"


def globals_maxed(state: GameState) -> bool:
    return (state.temperature >= P.MAX_TEMPERATURE and state.oxygen >= P.MAX_OXYGEN
            and state.oceans >= P.MAX_OCEANS)


# ---- setup ---------------------------------------------------------------------------
def new_game(player_ids: Sequence[str] = ("p1", "p2"), seed: int = 0,
             options: GameOptions | None = None) -> GameState:
    """Shuffle, deal, and return a state waiting for the first player's setup choices."""
    options = options or GameOptions()
    if not 2 <= len(player_ids) <= 5:
        raise ValueError("2 to 5 players are supported (solo rules aren't modelled yet)")
    prelude = "prelude" in options.modules
    players = tuple(PlayerState(id=pid, tr=STARTING_TR) for pid in player_ids)
    state = GameState(players=players, options=options, seed=seed,
                      milestones=tuple(S.THARSIS_MILESTONES), awards=tuple(S.THARSIS_AWARDS))

    projects = cards_for(options.modules, {"automated", "active", "event"})
    corporations = [c for c in cards_for(options.modules, {"corporation"}) if c not in EXCLUDED_CORPORATIONS]
    preludes = cards_for(options.modules, {"prelude"}) if prelude else []
    rng, state = state.rng()
    for deck in (projects, corporations, preludes):
        rng.shuffle(deck)
    rng2, state = state.rng()
    state = replace(state, deck=tuple(projects), corporation_deck=tuple(corporations),
                    prelude_deck=tuple(preludes), first_player=rng2.randrange(len(players)))

    for p in state.players:
        corps, rest = state.corporation_deck[:CORPORATIONS_DEALT], state.corporation_deck[CORPORATIONS_DEALT:]
        state = replace(state, corporation_deck=rest)
        dealt_preludes: tuple[str, ...] = ()
        if prelude:
            dealt_preludes, rest_p = state.prelude_deck[:PRELUDES_DEALT], state.prelude_deck[PRELUDES_DEALT:]
            state = replace(state, prelude_deck=rest_p)
        state, hand = P.draw(state, STARTING_PROJECT_CARDS)
        state = state.update_player(p.id, dealt_corporations=corps, dealt_preludes=dealt_preludes,
                                    research=hand, first_action_done=False)

    for p in state.players_in_generation_order():
        state = ask(state, p.id, kind="card", options=state.player(p.id).dealt_corporations,
                    then="setup.corporation", title="Choose your corporation")
    state = defer(state, state.players[state.first_player].id, "flow.play_corporations", priority=Priority.FLOW)
    return advance(state)


@continuation("setup.corporation")
def _choose_corporation(state, pid, corp):
    p = state.player(pid)
    unused = tuple(c for c in p.dealt_corporations if c != corp)
    state = state.update_player(pid, corporation=corp, dealt_corporations=())
    state = replace(state, corporation_deck=state.corporation_deck + unused)
    if p.dealt_preludes:
        state = ask(state, pid, kind="cards", options=p.dealt_preludes, min=PRELUDES_KEPT, max=PRELUDES_KEPT,
                    then="setup.preludes", title=f"Choose {PRELUDES_KEPT} preludes")
    budget = card(corp).starting_megacredits // CARD_PRICE
    return ask(state, pid, kind="cards", options=p.research, min=0, max=min(budget, len(p.research)),
               then="setup.buy_cards", title=f"Choose project cards to buy ({CARD_PRICE} M€ each)")


@continuation("setup.preludes")
def _choose_preludes(state, pid, chosen):
    return state.update_player(pid, preludes_in_hand=tuple(chosen), dealt_preludes=())


@continuation("setup.buy_cards")
def _buy_initial(state, pid, chosen):
    # Payment happens when the corporation is played (its starting M€ pays for them).
    p = state.player(pid)
    rejected = tuple(c for c in p.research if c not in chosen)
    state = state.update_player(pid, research=tuple(chosen))
    return P.discard_cards(state, rejected)


@continuation("flow.play_corporations")
def _play_corporations(state, pid, _choice):
    for p in state.players_in_generation_order():
        state = play_corporation(state, p.id)
    state = replace(state, phase="preludes")
    return defer(state, pid, "flow.preludes", priority=Priority.FLOW)


def play_corporation(state: GameState, pid: str) -> GameState:
    p = state.player(pid)
    corp = card(p.corporation)
    bought = p.research
    state = state.update_player(pid, stock=p.stock.add("megacredits", corp.starting_megacredits),
                                tableau=(corp.id,) + p.tableau, research=(),
                                first_action_done=not (corp.first_action or P.get_hook(corp.id, "initial_action")))
    state = P.spend(state, pid, "megacredits", CARD_PRICE * len(bought))
    state = state.update_player(pid, hand=state.player(pid).hand + bought)
    state = P.log(state, f"{pid} chose {corp.name} and bought {len(bought)} card(s)")
    if corp.behavior:
        from engine.behavior import execute
        state = execute(state, pid, corp.id, "behavior")
    hook = P.get_hook(corp.id, "bespoke_play")
    if hook is not None:
        state = hook(state, pid)
    return A.card_played_triggers(state, pid, corp.id)


@continuation("flow.preludes")
def _preludes(state, pid, _choice):
    order = [p.id for p in state.players_in_generation_order() if state.player(p.id).preludes_in_hand]
    if not order:
        return start_action_phase(state)
    return _next_prelude(state, order[0])


def _next_prelude(state: GameState, pid: str) -> GameState:
    preludes = state.player(pid).preludes_in_hand
    return ask(state, pid, kind="card", options=preludes, then="flow.play_prelude",
               title="Choose a prelude to play", priority=Priority.FLOW)


@continuation("flow.play_prelude")
def _play_prelude(state, pid, prelude):
    p = state.player(pid)
    if A.can_play_card(state, pid, prelude, check_cost=False):
        state = A.play_card(state, pid, prelude)
    else:
        state = A.fizzle(state, pid, prelude)
    return defer(state, pid, "flow.preludes", priority=Priority.FLOW)


# ---- the action phase ----------------------------------------------------------------
def start_action_phase(state: GameState) -> GameState:
    state = replace(state, phase="action", active=state.first_player, actions_this_turn=0)
    return ask_for_action(state, state.players[state.active].id)


def ask_for_action(state: GameState, pid: str) -> GameState:
    return ask(state, pid, kind="action", options=A.legal_actions(state, pid), then="turn.action",
               title=f"Generation {state.generation}: take an action", priority=Priority.FLOW)


@continuation("turn.action")
def _take_action(state, pid, action):
    state = replace(state, actions_this_turn=state.actions_this_turn + 1)
    if action[0] == "pass":
        state = state.update_player(pid, passed=True)
        state = P.log(state, f"{pid} passed")
    state = A.take_action(state, pid, action)
    return defer(state, pid, "turn.after_action", {"action": action}, priority=Priority.FLOW)


@continuation("turn.after_action")
def _after_action(state, pid, _choice, action):
    p = state.player(pid)
    if not p.passed and action[0] != "end_turn" and state.actions_this_turn < 2:
        return ask_for_action(state, pid)
    return next_turn(state)


def next_turn(state: GameState) -> GameState:
    n = len(state.players)
    for step in range(1, n + 1):
        idx = (state.active + step) % n
        if not state.players[idx].passed:
            state = replace(state, active=idx, actions_this_turn=0)
            return ask_for_action(state, state.players[idx].id)
    return production_phase(state)


# ---- production and research ---------------------------------------------------------
def production_phase(state: GameState) -> GameState:
    state = replace(state, phase="production")
    for p in state.players:
        p = state.player(p.id)
        stock = p.stock.add("heat", p.stock.energy).set("energy", 0)
        income = p.production.add("megacredits", p.tr)
        stock = stock + income
        state = state.update_player(p.id, stock=stock)
        state = P.trigger_own(state, p.id, "on_production_phase")
    state = P.log(state, f"production phase of generation {state.generation}")
    pid = state.players[state.first_player].id
    return defer(state, pid, "flow.end_generation", priority=Priority.FLOW)


@continuation("flow.end_generation")
def _end_generation(state, pid, _choice):
    if globals_maxed(state) or state.generation >= state.options.max_generations:
        return final_greenery(state)
    n = len(state.players)
    players = tuple(replace(p, passed=False, actions_used=frozenset(), tr_raised_this_generation=False,
                            last_card_played=None)
                    for p in state.players)
    state = replace(state, players=players, generation=state.generation + 1,
                    first_player=(state.first_player + 1) % n, phase="research")
    for p in state.players_in_generation_order():
        state, drawn = P.draw(state, RESEARCH_CARDS)
        state = state.update_player(p.id, research=drawn)
        budget = state.player(p.id).stock.megacredits // CARD_PRICE
        state = ask(state, p.id, kind="cards", options=drawn, min=0, max=min(budget, len(drawn)),
                    then="flow.research", title=f"Choose cards to buy ({CARD_PRICE} M€ each)",
                    priority=Priority.FLOW)
    return defer(state, pid, "flow.start_generation", priority=Priority.FLOW)


@continuation("flow.research")
def _research(state, pid, chosen):
    p = state.player(pid)
    chosen = tuple(chosen)
    affordable = chosen[: p.stock.megacredits // CARD_PRICE]
    state = P.spend(state, pid, "megacredits", CARD_PRICE * len(affordable))
    state = state.update_player(pid, hand=state.player(pid).hand + affordable, research=())
    return P.discard_cards(state, [c for c in p.research if c not in affordable])


@continuation("flow.start_generation")
def _start_generation(state, pid, _choice):
    return start_action_phase(state)


# ---- the end -------------------------------------------------------------------------
def final_greenery(state: GameState) -> GameState:
    state = replace(state, phase="final_greenery")
    order = [p.id for p in state.players_in_generation_order()]
    return defer(state, order[0], "flow.final_greenery", {"order": tuple(order)}, priority=Priority.FLOW)


@continuation("flow.final_greenery")
def _final_greenery(state, pid, _choice, order):
    for i, who in enumerate(order):
        if A.can_convert_plants(state, who):
            return ask(state, who, kind="option", options=("convert", "done"), then="flow.final_greenery_choice",
                       ctx={"order": order[i:]}, title="Convert plants into a greenery?", priority=Priority.FLOW)
    return replace(P.log(state, "game over"), phase="end")


@continuation("flow.final_greenery_choice")
def _final_greenery_choice(state, pid, choice, order):
    if choice == "convert":
        state = A.convert_plants(state, pid)
    else:
        order = order[1:]
    if not order:
        return replace(state, phase="end")
    return defer(state, order[0], "flow.final_greenery", {"order": order}, priority=Priority.FLOW)
