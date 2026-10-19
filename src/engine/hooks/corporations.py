"""Hooks for the base-game and Corporate Era corporations (`module` "corporation").

Original: src/server/cards/corporation/

A corporation's starting M€, production and stock come from its data, and its first action
from `firstAction`. These hooks cover only what the data can't say.
"""
from __future__ import annotations

from engine import board as B
from engine import primitives as P
from engine.cards import card
from engine.pending import Priority, defer

from ._helpers import card_tag_count
from .registry import hook

CREDICOR_THRESHOLD = 20


@hook("CREDICOR", name="on_card_played")
def credicor_card_played(state, owner, card_id):
    """CrediCor: after you pay for a card with a basic cost of 20 M€ or more, gain 4 M€.

    Original: corporation/CrediCor.ts  (onCardPlayed, onStandardProject)
    """
    c = card(card_id)
    if c.is_project and c.cost >= CREDICOR_THRESHOLD:
        state = P.add_stock(state, owner, "megacredits", 4)
    return state


@hook("CREDICOR", name="on_standard_project")
def credicor_standard_project(state, owner, project_id):
    """CrediCor: ...or for a standard project with a basic cost of 20 M€ or more."""
    if card(project_id).cost >= CREDICOR_THRESHOLD:
        state = P.add_stock(state, owner, "megacredits", 4)
    return state


@hook("HELION", name="bespoke_play")
def helion_play(state, owner):
    """Helion: you may use heat as M€.

    Original: corporation/Helion.ts  (bespokePlay)
    Diverges: payment is automatic, so heat is spent only after every other source (see
              `primitives.auto_payment`).
    """
    return state.update_player(owner, can_use_heat_as_mc=True)


@hook("INTERPLANETARY_CINEMATICS", name="on_card_played")
def interplanetary_cinematics_card_played(state, owner, card_id):
    """Interplanetary Cinematics: each time you play an event, gain 2 M€.

    Original: corporation/InterplanetaryCinematics.ts  (onCardPlayed)
    """
    if card(card_id).type == "event":
        state = P.add_stock(state, owner, "megacredits", 2)
    return state


@hook("MINING_GUILD", name="on_tile_placed")
def mining_guild_tile(state, owner, active, space_id, board_type):
    """Mining Guild: each time you get any steel or titanium as a placement bonus on the map,
    increase your steel production 1 step.

    Original: corporation/MiningGuild.ts  (onTilePlaced, givesSteelOrTitanium, applies)
    Ocean tiles have no owner, so as in the original an ocean on a steel space doesn't count.
    """
    tile = state.tiles.get(space_id)
    if board_type != "mars" or tile is None or tile.owner != owner or owner != active:
        return state
    bonus = B.SPACES[space_id].bonus
    if "steel" in bonus or "titanium" in bonus:
        state = P.add_production(state, owner, "steel", 1)
    return state


@hook("THARSIS_REPUBLIC", name="on_tile_placed")
def tharsis_republic_tile(state, owner, active, space_id, board_type):
    """Tharsis Republic: when any city tile is placed on Mars, increase your M€ production 1
    step. When you place a city tile, gain 3 M€.

    Original: corporation/TharsisRepublic.ts  (onTilePlaced, bespokePlay)
    Diverges: the solo-only neutral cities of `bespokePlay` aren't modelled.
    """
    if not B.is_city(state.tiles.get(space_id)):
        return state
    if owner == active:
        state = P.add_stock(state, owner, "megacredits", 3)
    if board_type == "mars" and space_id in B.MARS_SPACES:
        prio = Priority.OPPONENT_TRIGGER if owner != active else Priority.DEFAULT
        state = defer(state, owner, "gain.production", {"resource": "megacredits", "n": 1}, priority=prio)
    return state


@hook("THORGATE", name="get_standard_project_discount")
def thorgate_sp_discount(state, owner, project_id):
    """Thorgate: the power plant standard project costs 3 M€ less (cards are in `cardDiscount`).

    Original: corporation/Thorgate.ts  (getStandardProjectDiscount)
    """
    return 3 if project_id == "POWER_PLANT_STANDARD_PROJECT" else 0


UNMI_COST = 3


@hook("UNITED_NATIONS_MARS_INITIATIVE", name="can_act")
def unmi_can_act(state, owner):
    p = state.player(owner)
    return p.tr_raised_this_generation and P.can_afford(state, owner, UNMI_COST)


@hook("UNITED_NATIONS_MARS_INITIATIVE", name="action")
def unmi_action(state, owner):
    """UNMI: if your TR was raised this generation, you may pay 3 M€ to raise it 1 step more.

    Original: corporation/UnitedNationsMarsInitiative.ts  (action, canAct)
    """
    state = P.pay(state, owner, UNMI_COST)
    return P.gain_tr(state, owner, 1)


@hook("SATURN_SYSTEMS", name="on_card_played_by_any_player")
def saturn_systems_any_card(state, owner, card_id, active):
    """Saturn Systems: each time any Jovian tag is put into play, including this, increase
    your M€ production 1 step.

    Original: corporation/SaturnSystems.ts  (onCardPlayedByAnyPlayer, onNonCardTagAddedByAnyPlayer)
    """
    n = card_tag_count(card_id, "jovian")
    return P.add_production(state, owner, "megacredits", n) if n else state


@hook("SATURN_SYSTEMS", name="on_non_card_tag_added_by_any_player")
def saturn_systems_tag(state, owner, tag):
    return P.add_production(state, owner, "megacredits", 1) if tag == "jovian" else state


@hook("THARSIS_REPUBLIC", name="bespoke_play")
def tharsis_republic_play(state, owner):
    """Tharsis Republic: the original places two neutral cities here in solo games only.

    Diverges: solo mode isn't modelled, so this does nothing.
    """
    return state
