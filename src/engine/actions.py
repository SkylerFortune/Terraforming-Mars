"""What a player can do on their turn, and how each of those things is carried out.

An action is a small tuple, so it can be listed, compared and stored:

    ("play", card_id)                 play a project card from hand
    ("action", card_id)               use a blue card's action (or the corporation's)
    ("first_action", corp_id)         the corporation's mandatory first action
    ("standard_project", sp_id)       a standard project (sell patents, power plant, ...)
    ("convert_plants",)               plants -> greenery
    ("convert_heat",)                 8 heat -> temperature
    ("claim_milestone", name)
    ("fund_award", name)
    ("end_turn",)                     skip the second action
    ("pass",)                         pass for the rest of the generation

`legal_actions` lists them; `take_action` performs one.
"""
from __future__ import annotations

from dataclasses import replace

from engine import behavior as BH
from engine import board as B
from engine import primitives as P
from engine import scoring as S
from engine.cards import CARDS, card
from engine.game_state import GameState
from engine.pending import CONTINUATIONS, Priority, ask, continuation, defer
from engine.requirements import UnsupportedRequirement, requirements_met

EXCLUDED_STANDARD_PROJECTS = frozenset({"BUFFER_GAS_STANDARD_PROJECT"})   # solo / 2-player variant only
HEAT_FOR_TEMPERATURE = 8


# ---- playing cards -------------------------------------------------------------------
def card_payment_kwargs(card_id: str) -> dict:
    return {"tags": card(card_id).tags}


def can_play_card(state: GameState, pid: str, card_id: str, discount: int = 0,
                  ignore_global: bool = False, check_cost: bool = True) -> bool:
    c = card(card_id)
    if check_cost:
        cost = max(0, P.card_cost(state, pid, card_id) - discount)
        if not P.can_afford(state, pid, cost, **card_payment_kwargs(card_id)):
            return False
    try:
        if not requirements_met(state, pid, card_id, ignore_global=ignore_global):
            return False
    except UnsupportedRequirement:
        return False
    if c.behavior and not BH.can_execute(state, pid, card_id, c.behavior):
        return False
    for name in ("bespoke_can_play", "can_play"):
        hook = P.get_hook(card_id, name)
        if hook is not None and not hook(state, pid):
            return False
    return True


def play_card(state: GameState, pid: str, card_id: str, discount: int = 0,
              from_hand: bool = True, pay: bool = True) -> GameState:
    """Play a project card (or a prelude): pay, run its behavior and hooks, fire triggers."""
    c = card(card_id)
    if pay and c.is_project:
        cost = max(0, P.card_cost(state, pid, card_id) - discount)
        state = P.pay(state, pid, cost, **card_payment_kwargs(card_id))
    if from_hand:
        p = state.player(pid)
        if card_id in p.hand:
            state = P.remove_from_hand(state, pid, [card_id])
        elif card_id in p.preludes_in_hand:
            state = state.update_player(pid, preludes_in_hand=tuple(x for x in p.preludes_in_hand if x != card_id))
    state = P.set_context(state, playing=card_id)
    state = P.log(state, f"{pid} played {c.name}")

    hook = P.get_hook(card_id, "bespoke_play_before")
    if hook is not None:
        state = hook(state, pid)
    play_hook = P.get_hook(card_id, "play")
    if play_hook is not None:
        state = play_hook(state, pid)
    else:
        if c.behavior:
            state = BH.execute(state, pid, card_id, "behavior")
        hook = P.get_hook(card_id, "bespoke_play")
        if hook is not None:
            state = hook(state, pid)

    p = state.player(pid)
    if c.type == "event":
        state = state.update_player(pid, events=p.events + (card_id,))
    else:
        state = state.update_player(pid, tableau=p.tableau + (card_id,))
    state = state.update_player(pid, last_card_played=card_id)
    state = P.set_context(state, playing=None)
    return card_played_triggers(state, pid, card_id)


def card_played_triggers(state: GameState, pid: str, card_id: str) -> GameState:
    state = P.trigger_own(state, pid, "on_card_played", card_id)
    for p in state.players_in_generation_order():
        for cid in state.player(p.id).tableau:
            hook = P.get_hook(cid, "on_card_played_by_any_player")
            if hook is not None:
                state = hook(state, p.id, card_id, pid)
    return state


def playable_cards(state: GameState, pid: str) -> list[str]:
    return [cid for cid in state.player(pid).hand if can_play_card(state, pid, cid)]


# ---- card actions --------------------------------------------------------------------
def can_use_action(state: GameState, pid: str, card_id: str) -> bool:
    p = state.player(pid)
    if card_id in p.actions_used or card_id not in p.tableau:
        return False
    c = card(card_id)
    hook = P.get_hook(card_id, "can_act")
    if hook is not None:
        return bool(hook(state, pid))
    if c.action is None:
        return False
    if not BH.can_execute(state, pid, card_id, c.action):
        return False
    hook = P.get_hook(card_id, "bespoke_can_act")
    return hook is None or bool(hook(state, pid))


def use_action(state: GameState, pid: str, card_id: str) -> GameState:
    p = state.player(pid)
    state = state.update_player(pid, actions_used=p.actions_used | {card_id})
    state = P.log(state, f"{pid} used the action of {card(card_id).name}")
    hook = P.get_hook(card_id, "action")
    if hook is not None:
        return hook(state, pid)
    return BH.execute(state, pid, card_id, "action")


def can_first_action(state: GameState, pid: str) -> bool:
    p = state.player(pid)
    return not p.first_action_done and p.corporation is not None


def first_action(state: GameState, pid: str) -> GameState:
    corp = state.player(pid).corporation
    state = state.update_player(pid, first_action_done=True)
    hook = P.get_hook(corp, "initial_action")
    if hook is not None:
        return hook(state, pid)
    if card(corp).first_action:
        return BH.execute(state, pid, corp, "firstAction")
    return state


# ---- standard projects ---------------------------------------------------------------
def standard_projects(state: GameState) -> list[str]:
    return [cid for cid, c in sorted(CARDS.items(), key=lambda kv: kv[1].number)
            if c.type == "standard_project" and c.game_module in state.options.modules
            and cid not in EXCLUDED_STANDARD_PROJECTS]


def standard_project_cost(state: GameState, pid: str, sp_id: str) -> int:
    discount = sum(P.query_own(state, pid, "get_standard_project_discount", sp_id))
    return max(0, card(sp_id).cost - discount)


def _sp_payment_kwargs(state: GameState, pid: str, sp_id: str) -> dict:
    hook = P.get_hook(sp_id, "can_pay_with")
    extra = hook(state, pid) if hook else {}
    return {"steel": bool(extra.get("steel")), "titanium": bool(extra.get("titanium"))}


def can_standard_project(state: GameState, pid: str, sp_id: str) -> bool:
    hook = P.get_hook(sp_id, "can_act")
    if hook is not None:
        return bool(hook(state, pid))
    return P.can_afford(state, pid, standard_project_cost(state, pid, sp_id), **_sp_payment_kwargs(state, pid, sp_id))


def do_standard_project(state: GameState, pid: str, sp_id: str) -> GameState:
    hook = P.get_hook(sp_id, "action")
    if hook is not None:              # Sell Patents asks which cards first
        return hook(state, pid)
    state = P.pay(state, pid, standard_project_cost(state, pid, sp_id), **_sp_payment_kwargs(state, pid, sp_id))
    return finish_standard_project(state, pid, sp_id)


def finish_standard_project(state: GameState, pid: str, sp_id: str) -> GameState:
    state = P.log(state, f"{pid} used the {card(sp_id).name}")
    state = P.trigger_own(state, pid, "on_standard_project", sp_id)
    return P.get_hook(sp_id, "action_essence")(state, pid)


# ---- conversions ---------------------------------------------------------------------
def sp_affordable(state: GameState, pid: str, sp_id: str) -> bool:
    return P.can_afford(state, pid, standard_project_cost(state, pid, sp_id), **_sp_payment_kwargs(state, pid, sp_id))


def can_convert_plants(state: GameState, pid: str) -> bool:
    p = state.player(pid)
    return p.stock.plants >= p.plants_per_greenery and bool(B.greenery_spaces(state, pid))


def convert_plants(state: GameState, pid: str) -> GameState:
    state = P.spend(state, pid, "plants", state.player(pid).plants_per_greenery)
    return P.ask_place_tile(state, pid, "greenery", rule="greenery")


def can_convert_heat(state: GameState, pid: str) -> bool:
    return state.player(pid).stock.heat >= HEAT_FOR_TEMPERATURE and P.can_raise_temperature(state)


def convert_heat(state: GameState, pid: str) -> GameState:
    state = P.spend(state, pid, "heat", HEAT_FOR_TEMPERATURE)
    return P.raise_temperature(state, pid, 1)


# ---- the action list -----------------------------------------------------------------
def legal_actions(state: GameState, pid: str) -> list[tuple]:
    if can_first_action(state, pid):
        return [("first_action", state.player(pid).corporation)]
    out: list[tuple] = []
    out += [("play", cid) for cid in playable_cards(state, pid)]
    out += [("action", cid) for cid in state.player(pid).tableau
            if card(cid).has_action and can_use_action(state, pid, cid)]
    out += [("standard_project", sp) for sp in standard_projects(state) if can_standard_project(state, pid, sp)]
    if can_convert_plants(state, pid):
        out.append(("convert_plants",))
    if can_convert_heat(state, pid):
        out.append(("convert_heat",))
    out += [("claim_milestone", m) for m in state.milestones if S.can_claim_milestone(state, pid, m)]
    out += [("fund_award", a) for a in state.awards if S.can_fund_award(state, pid, a)]
    if state.actions_this_turn == 1:
        out.append(("end_turn",))
    out.append(("pass",))
    return out


def take_action(state: GameState, pid: str, action: tuple) -> GameState:
    kind = action[0]
    if kind == "play":
        return play_card(state, pid, action[1])
    if kind == "action":
        return use_action(state, pid, action[1])
    if kind == "first_action":
        return first_action(state, pid)
    if kind == "standard_project":
        return do_standard_project(state, pid, action[1])
    if kind == "convert_plants":
        return convert_plants(state, pid)
    if kind == "convert_heat":
        return convert_heat(state, pid)
    if kind == "claim_milestone":
        state = P.spend(state, pid, "megacredits", S.MILESTONE_COST)
        state = replace(state, claimed_milestones=state.claimed_milestones + ((action[1], pid),))
        return P.log(state, f"{pid} claimed {action[1]}")
    if kind == "fund_award":
        state = P.spend(state, pid, "megacredits", S.award_cost(state))
        state = replace(state, funded_awards=state.funded_awards + ((action[1], pid),))
        return P.log(state, f"{pid} funded {action[1]}")
    if kind in ("pass", "end_turn"):
        return state
    raise ValueError(f"unknown action {action!r}")


def fizzle(state: GameState, pid: str, prelude_id: str) -> GameState:
    """A prelude that can't do its job is discarded and its owner gains 15 M€ instead."""
    p = state.player(pid)
    state = state.update_player(pid, tableau=tuple(c for c in p.tableau if c != prelude_id),
                                preludes_in_hand=tuple(c for c in p.preludes_in_hand if c != prelude_id))
    state = P.add_stock(state, pid, "megacredits", 15)
    return P.log(state, f"{card(prelude_id).name} fizzled; {pid} gained 15 M€")


def ask_play_from_hand(state: GameState, pid: str, then: str | None = None, ctx=(),
                       title: str = "Play a card from hand") -> GameState:
    """Queue a choice of card to play from hand (worked out when reached), then play it.

    `then`, if given, is called afterwards as `then(state, pid, card_id_or_None, **ctx)`.
    """
    return defer(state, pid, "actions.ask_play_from_hand", {"then": then, "ctx": tuple(dict(ctx).items()),
                                                             "title": title})


@continuation("actions.ask_play_from_hand")
def _ask_play_from_hand(state, pid, _choice, then, ctx, title):
    options = playable_cards(state, pid)
    if not options:
        return _played_from_hand(state, pid, None, then, ctx)
    return ask(state, pid, kind="card", options=options, allow_pass=True, then="actions.played_from_hand",
               ctx={"then": then, "ctx": ctx}, title=title, priority=Priority.COST)


@continuation("actions.played_from_hand")
def _played_from_hand(state, pid, card_id, then, ctx):
    if card_id is not None:
        state = play_card(state, pid, card_id)
    if then is not None:
        state = CONTINUATIONS[then](state, pid, card_id, **dict(ctx))
    return state
