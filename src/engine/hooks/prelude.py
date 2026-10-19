"""Hooks for the Prelude expansion: its corporations and prelude cards (`module` "prelude").

Original: src/server/cards/prelude/

A prelude that can't be played when its turn comes is discarded for 15 M€ ("fizzles"); see
`engine.actions.fizzle`. Several preludes below check in `bespoke_can_play` that they can pay
their cost, so that the game fizzles them instead of leaving the player in debt.
"""
from __future__ import annotations

from dataclasses import replace

from engine import actions as A
from engine import board as B
from engine import primitives as P
from engine import scoring as S
from engine.pending import Priority, ask, continuation, defer

from ._helpers import card_tag_count, has_positive_vp
from .registry import hook

# ======================================================================================
# Corporations
# ======================================================================================
@hook("POINT_LUNA", name="on_card_played")
def point_luna_card_played(state, owner, card_id):
    """Point Luna: when you play an Earth tag, including this, draw a card.

    Original: prelude/PointLuna.ts  (onCardPlayed)
    """
    n = card_tag_count(card_id, "earth")
    return P.draw_cards(state, owner, n) if n else state


ROBINSON_COST = 4
PRODUCTIONS = ("megacredits", "steel", "titanium", "plants", "energy", "heat")


@hook("ROBINSON_INDUSTRIES", name="can_act")
def robinson_can_act(state, owner):
    return P.can_afford(state, owner, ROBINSON_COST)


@hook("ROBINSON_INDUSTRIES", name="action")
def robinson_action(state, owner):
    """Robinson Industries: spend 4 M€ to increase (one of) your lowest production 1 step.

    Original: prelude/RobinsonIndustries.ts  (action, canAct)
    Asks:     option -> "robinson.choice" (skipped when one production is lowest)
    """
    state = P.pay(state, owner, ROBINSON_COST)
    prod = state.player(owner).production
    lowest = min(prod.get(r) for r in PRODUCTIONS)
    options = tuple(r for r in PRODUCTIONS if prod.get(r) == lowest)
    return ask(state, owner, kind="option", options=options, then="gain.production.choice",
               title="Select production to increase")


@continuation("gain.production.choice")
def _gain_production_choice(state, owner, resource):
    return P.add_production(state, owner, resource, 1)


@hook("VALLEY_TRUST", name="initial_action")
def valley_trust_first_action(state, owner):
    """Valley Trust: as your first action, draw 3 prelude cards and play one of them. Discard
    the other two.

    Original: prelude/ValleyTrust.ts  (initialAction)
    Asks:     card -> "valley_trust.play"
    """
    drawn, rest = state.prelude_deck[:3], state.prelude_deck[3:]
    state = replace(state, prelude_deck=rest)
    if not drawn:
        return state
    return ask(state, owner, kind="card", options=drawn, then="valley_trust.play", ctx={"drawn": drawn},
               title="Select prelude card to play")


@continuation("valley_trust.play")
def _valley_trust_play(state, owner, prelude, drawn):
    state = P.discard_cards(state, [c for c in drawn if c != prelude])
    if A.can_play_card(state, owner, prelude, check_cost=False):
        return A.play_card(state, owner, prelude, from_hand=False)
    return P.add_stock(state, owner, "megacredits", 15)     # it fizzles


@hook("VITOR", name="initial_action")
def vitor_first_action(state, owner):
    """Vitor: as your first action, fund an award for free.

    Original: prelude/Vitor.ts  (initialAction, selectAwardToFund)
    Asks:     award -> "vitor.fund"
    """
    if S.award_cost(state) is None:
        return state
    funded = {a for a, _ in state.funded_awards}
    options = tuple(a for a in state.awards if a not in funded)
    return ask(state, owner, kind="award", options=options, then="vitor.fund", title="Select award to fund")


@continuation("vitor.fund")
def _vitor_fund(state, owner, award):
    state = replace(state, funded_awards=state.funded_awards + ((award, owner),))
    return P.log(state, f"{owner} funded {award} for free")


@hook("VITOR", name="on_card_played")
def vitor_card_played(state, owner, card_id):
    """Vitor: when you play a card with a non-negative VP icon (including events), gain 3 M€."""
    return P.add_stock(state, owner, "megacredits", 3) if has_positive_vp(card_id) else state


# ======================================================================================
# Prelude cards
# ======================================================================================
def _has_energy_production(state, owner) -> bool:
    return state.player(owner).production.energy >= 1


@hook("LAVA_TUBE_SETTLEMENT", name="bespoke_can_play")
def lava_tube_can_play(state, owner):
    return bool(B.volcanic_spaces(state, owner)) and _has_energy_production(state, owner)


@hook("LAVA_TUBE_SETTLEMENT", name="bespoke_play")
def lava_tube_play(state, owner):
    """Lava Tube Settlement: place a city tile on a volcanic area (production is in the data).

    Original: prelude/LavaTubeSettlement.ts  (bespokePlay, bespokeCanPlay, getSpacesForCity)
    """
    return P.ask_place_tile(state, owner, "city", rule="volcanic", title="Select space for city tile")


AQUIFER_TURBINES_COST = 3


def _aquifer_turbine_spaces(state, owner):
    mc = state.player(owner).stock.megacredits
    return [s for s in B.ocean_spaces_available(state, owner)
            if mc + P.OCEAN_ADJACENCY_BONUS * len(B.adjacent_with(state, s, B.is_ocean)) >= AQUIFER_TURBINES_COST]


@hook("AQUIFER_TURBINES", name="bespoke_can_play")
def aquifer_turbines_can_play(state, owner):
    if not P.can_place_ocean(state):
        return P.can_afford(state, owner, AQUIFER_TURBINES_COST)
    return bool(_aquifer_turbine_spaces(state, owner))


@hook("AQUIFER_TURBINES", name="bespoke_play")
def aquifer_turbines_play(state, owner):
    """Aquifer Turbines: place an ocean tile, then pay 3 M€ (the ocean's bonus may cover it).

    Original: prelude/AquiferTurbines.ts  (bespokePlay, bespokeCanPlay, availableSpaces)
    """
    if P.can_place_ocean(state):
        state = P.ask_place_tile(state, owner, "ocean", spaces=_aquifer_turbine_spaces(state, owner),
                                 title="Select space for ocean tile", priority=Priority.PLACE_OCEAN_TILE)
    return defer(state, owner, "prelude.pay", {"amount": AQUIFER_TURBINES_COST},
                 priority=Priority.LOSE_RESOURCE_OR_PRODUCTION)


@continuation("prelude.pay")
def _prelude_pay(state, owner, _choice, amount):
    return P.pay(state, owner, amount)


def _pay_prelude(card_id, amount):
    """A prelude whose effect is in the data and that costs `amount` M€ on top."""
    @hook(card_id, name="bespoke_can_play")
    def can_play(state, owner):
        return P.can_afford(state, owner, amount)

    @hook(card_id, name="bespoke_play")
    def play(state, owner):
        return P.pay(state, owner, amount)

    can_play.__doc__ = f"{card_id}: needs {amount} M€ to pay with."
    play.__doc__ = f"{card_id}: pay {amount} M€. Original: prelude/*.ts (bespokePlay, bespokeCanPlay)"


_pay_prelude("BUSINESS_EMPIRE", 6)       # +6 M€ production
_pay_prelude("GALILEAN_MINING", 5)       # +2 titanium production
_pay_prelude("HUGE_ASTEROID", 5)         # +3 temperature steps


ECCENTRIC_SPONSOR_DISCOUNT = 25


@hook("ECCENTRIC_SPONSOR", name="get_card_discount")
def eccentric_sponsor_discount(state, owner, card_id):
    """Eccentric Sponsor: the card played with it costs 25 M€ less."""
    if state.player(owner).last_card_played == "ECCENTRIC_SPONSOR":
        return ECCENTRIC_SPONSOR_DISCOUNT
    return 0


@hook("ECCENTRIC_SPONSOR", name="bespoke_play")
def eccentric_sponsor_play(state, owner):
    """Eccentric Sponsor: play a card from hand, reducing its cost by 25 M€.

    Original: prelude/EccentricSponsor.ts  (bespokePlay, getCardDiscount)
    Asks:     card (or pass) -> "eccentric_sponsor.played"
    The question comes after this card is in play, so `last_card_played` is this card while
    the player chooses and the discount applies. With nothing playable, the card fizzles.
    """
    return defer(state, owner, "eccentric_sponsor.ask")


@continuation("eccentric_sponsor.ask")
def _eccentric_sponsor_ask(state, owner, _choice):
    options = A.playable_cards(state, owner)
    if not options:
        state = A.fizzle(state, owner, "ECCENTRIC_SPONSOR")
        return state.update_player(owner, last_card_played=None)
    return ask(state, owner, kind="card", options=options, allow_pass=True, then="eccentric_sponsor.played",
               title="Select a card to play with a 25 M€ discount", priority=Priority.COST)


@continuation("eccentric_sponsor.played")
def _eccentric_sponsor_played(state, owner, card_id):
    if card_id is None:
        return state.update_player(owner, last_card_played=None)
    return A.play_card(state, owner, card_id)


ECOLOGY_EXPERTS_BONUS = 50


@hook("ECOLOGY_EXPERTS", name="get_global_parameter_requirement_bonus")
def ecology_experts_bonus(state, owner, parameter):
    """Ecology Experts: the card played with it ignores global requirements."""
    return ECOLOGY_EXPERTS_BONUS if state.player(owner).last_card_played == "ECOLOGY_EXPERTS" else 0


@hook("ECOLOGY_EXPERTS", name="can_play")
def ecology_experts_can_play(state, owner):
    """Playable only if some card in hand could then be played (with the +1 plant production
    and the requirement bonus already applied)."""
    p = state.player(owner)
    trial = state.update_player(owner, production=p.production.add("plants", 1))
    return any(A.can_play_card(trial, owner, cid, ignore_global=True) for cid in p.hand)


@hook("ECOLOGY_EXPERTS", name="bespoke_play")
def ecology_experts_play(state, owner):
    """Ecology Experts: +1 plant production (data), then play a card from hand ignoring global
    requirements.

    Original: prelude/EcologyExperts.ts  (bespokePlay, canPlay, getGlobalParameterRequirementBonus)
    Asks:     card (or pass) -> "actions.played_from_hand"
    """
    return A.ask_play_from_hand(state, owner, then="ecology_experts.done",
                                title="Select a card to play, ignoring global requirements")


@continuation("ecology_experts.done")
def _ecology_experts_done(state, owner, card_id):
    if card_id is None:
        state = state.update_player(owner, last_card_played=None)
    return state


@hook("BUFFER_GAS_STANDARD_PROJECT", name="action_essence")
def buffer_gas_essence(state, owner):
    """Buffer Gas (SP, solo/2-player TR-63 variant): raise your TR 1 step.

    Original: prelude/BufferGasStandardProject.ts  (actionEssence)
    Not offered by `actions.standard_projects`, since that variant isn't modelled.
    """
    return P.gain_tr(state, owner, 1)
