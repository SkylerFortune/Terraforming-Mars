"""Hooks for cards whose `module` is "base": the base game, Corporate Era project cards,
and the base standard projects and standard actions.

Original: src/server/cards/base/ (and base/standardProjects, base/standardActions).

Rules these hooks assume:
  * Tharsis is the only board, so "energy coverage" for city cards (an Ares/other-map
    placement bonus that grants energy production) reduces to "has energy production".
  * Solo mode isn't modelled, so the solo branches of attack cards are left out.
  * Turmoil isn't modelled, so Reds costs are ignored.
"""
from __future__ import annotations

from engine import actions as A
from engine import board as B
from engine import primitives as P
from engine.behavior import count as count_countable, resources_protected
from engine.cards import CARDS, card
from engine.game_state import Units
from engine.pending import Priority, ask, continuation, defer

from ._helpers import card_tag_count
from .registry import hook

BIO_TAGS = ("animal", "plant", "microbe")


# ======================================================================================
# Tile triggers
# ======================================================================================
@hook("ARCTIC_ALGAE", name="on_tile_placed")
def arctic_algae_tile(state, owner, active, space_id, board_type):
    """Arctic Algae (023): when anyone places an ocean tile, gain 2 plants.

    Original: base/ArcticAlgae.ts  (onTilePlaced)
    """
    if B.is_ocean(state.tiles.get(space_id)):
        prio = Priority.OPPONENT_TRIGGER if owner != active else Priority.DEFAULT
        state = defer(state, owner, "gain.stock", {"resource": "plants", "n": 2}, priority=prio)
    return state


@continuation("gain.stock")
def _gain_stock(state, pid, _choice, resource, n):
    return P.add_stock(state, pid, resource, n)


@continuation("gain.production")
def _gain_production(state, pid, _choice, resource, n):
    return P.add_production(state, pid, resource, n)


@continuation("gain.card_resource")
def _gain_card_resource(state, pid, _choice, card_id, n):
    return P.add_card_resources(state, pid, card_id, n)


@hook("HERBIVORES", name="on_tile_placed")
def herbivores_tile(state, owner, active, space_id, board_type):
    """Herbivores (147): when you place a greenery tile, add an animal to this card.

    Original: base/Herbivores.ts  (onTilePlaced)
    """
    if owner == active and B.is_greenery(state.tiles.get(space_id)):
        state = defer(state, owner, "gain.card_resource", {"card_id": "HERBIVORES", "n": 1})
    return state


@hook("PETS", name="on_tile_placed")
def pets_tile(state, owner, active, space_id, board_type):
    """Pets (172): when any city tile is placed, add an animal to this card.

    Original: base/Pets.ts  (onTilePlaced)
    """
    if B.is_city(state.tiles.get(space_id)):
        prio = Priority.OPPONENT_TRIGGER if owner != active else Priority.DEFAULT
        state = defer(state, owner, "gain.card_resource", {"card_id": "PETS", "n": 1}, priority=prio)
    return state


@hook("ROVER_CONSTRUCTION", name="on_tile_placed")
def rover_construction_tile(state, owner, active, space_id, board_type):
    """Rover Construction (038): when any city tile is placed, gain 2 M€.

    Original: base/RoverConstruction.ts  (onTilePlaced)
    """
    if B.is_city(state.tiles.get(space_id)):
        prio = Priority.OPPONENT_TRIGGER if owner != active else Priority.DEFAULT
        state = defer(state, owner, "gain.stock", {"resource": "megacredits", "n": 2}, priority=prio)
    return state


# ======================================================================================
# City cards
# ======================================================================================
def _has_energy_production(state, owner) -> bool:
    return state.player(owner).production.energy >= 1


@hook("IMMIGRANT_CITY", name="bespoke_can_play")
def immigrant_city_can_play(state, owner):
    """Immigrant City (200): needs a city space, energy production, and room to lose 2 M€
    production (Tharsis Republic's +1 covers it)."""
    p = state.player(owner)
    can_lose_mc = p.production.megacredits >= -3 or "THARSIS_REPUBLIC" in p.tableau
    return bool(B.city_spaces(state, owner)) and _has_energy_production(state, owner) and can_lose_mc


@hook("IMMIGRANT_CITY", name="bespoke_play")
def immigrant_city_play(state, owner):
    """Immigrant City (200): place a city, then lose 1 energy and 2 M€ production.

    Original: base/ImmigrantCity.ts  (bespokePlay, bespokeCanPlay, onTilePlaced, productionBox)
    Asks:     place.ask (city) then the production loss is deferred.
    The production loss comes after the city, so this card's own trigger (+1 M€ production
    for the new city) counts first, exactly as in the original.
    """
    state = P.ask_place_tile(state, owner, "city", rule="city")
    return defer(state, owner, "immigrant_city.lose_production", priority=Priority.LOSE_RESOURCE_OR_PRODUCTION)


@continuation("immigrant_city.lose_production")
def _immigrant_city_lose(state, owner, _choice):
    state = P.add_production(state, owner, "energy", -1)
    return P.add_production(state, owner, "megacredits", -2)


@hook("IMMIGRANT_CITY", name="on_tile_placed")
def immigrant_city_tile(state, owner, active, space_id, board_type):
    """Immigrant City: when any city tile is placed, increase your M€ production 1 step."""
    if B.is_city(state.tiles.get(space_id)):
        prio = Priority.OPPONENT_TRIGGER if owner != active else Priority.DEFAULT
        state = defer(state, owner, "gain.production", {"resource": "megacredits", "n": 1}, priority=prio)
    return state


@hook("IMMIGRANT_CITY", name="production_box")
def immigrant_city_box(state, owner):
    return Units(energy=-1, megacredits=-2)


@hook("NOCTIS_CITY", name="bespoke_can_play")
def noctis_city_can_play(state, owner):
    """Noctis City (017): Tharsis reserves the Noctis space, so only energy production matters."""
    return _has_energy_production(state, owner) and B.NOCTIS_CITY not in state.tiles


@hook("NOCTIS_CITY", name="bespoke_play")
def noctis_city_play(state, owner):
    """Noctis City (017): place a city on the reserved Noctis City space, lose 1 energy production.

    Original: base/NoctisCity.ts  (bespokePlay, bespokeCanPlay, productionBox)
    """
    state = P.place_city(state, owner, B.NOCTIS_CITY, "NOCTIS_CITY")
    return P.add_production(state, owner, "energy", -1)


@hook("NOCTIS_CITY", name="production_box")
def noctis_city_box(state, owner):
    return Units(energy=-1, megacredits=3)


def _urbanized_spaces(state, owner):
    return [s for s in B.land_spaces(state, owner) if len(B.adjacent_with(state, s, B.is_city)) >= 2]


@hook("URBANIZED_AREA", name="bespoke_can_play")
def urbanized_area_can_play(state, owner):
    return bool(_urbanized_spaces(state, owner)) and _has_energy_production(state, owner)


@hook("URBANIZED_AREA", name="bespoke_play")
def urbanized_area_play(state, owner):
    """Urbanized Area (120): place a city next to at least 2 other cities; lose 1 energy production.

    Original: base/UrbanizedArea.ts  (bespokePlay, bespokeCanPlay, productionBox)
    """
    state = P.ask_place_tile(state, owner, "city", spaces=_urbanized_spaces(state, owner),
                             title="Select space next to at least 2 other city tiles")
    return defer(state, owner, "lose.production", {"resource": "energy", "n": 1},
                 priority=Priority.LOSE_RESOURCE_OR_PRODUCTION)


@continuation("lose.production")
def _lose_production(state, pid, _choice, resource, n):
    return P.add_production(state, pid, resource, -n)


@hook("URBANIZED_AREA", name="production_box")
def urbanized_area_box(state, owner):
    return Units(energy=-1, megacredits=2)


# ======================================================================================
# Special tiles
# ======================================================================================
def _mining_spaces(state, owner, card_id):
    spaces = [s for s in B.land_spaces(state, owner)
              if "steel" in B.SPACES[s].bonus or "titanium" in B.SPACES[s].bonus]
    if card_id == "MINING_AREA":
        spaces = [s for s in spaces if B.adjacent_with(
            state, s, lambda t: t is not None and t.owner == owner and not B.is_ocean(t))]
    return spaces


@hook("MINING_RIGHTS", name="bespoke_can_play")
def mining_rights_can_play(state, owner):
    return bool(_mining_spaces(state, owner, "MINING_RIGHTS"))


@hook("MINING_AREA", name="bespoke_can_play")
def mining_area_can_play(state, owner):
    return bool(_mining_spaces(state, owner, "MINING_AREA"))


@hook("MINING_RIGHTS", name="bespoke_play")
def mining_rights_play(state, owner):
    """Mining Rights (067): place this tile on a space with a steel or titanium bonus and raise
    that production 1 step.

    Original: base/MiningRights.ts, base/MiningCard.ts  (bespokePlay, bespokeCanPlay, productionBox)
    Asks:     space -> "mining.space", then (if the space has both) resource -> "mining.resource"
    """
    return ask(state, owner, kind="space", options=_mining_spaces(state, owner, "MINING_RIGHTS"),
               then="mining.space", ctx={"card_id": "MINING_RIGHTS"},
               title="Select a space with a steel or titanium bonus")


@hook("MINING_AREA", name="bespoke_play")
def mining_area_play(state, owner):
    """Mining Area (064): as Mining Rights, but the space must be next to one of your tiles.

    Original: base/MiningArea.ts, base/MiningCard.ts  (bespokePlay, bespokeCanPlay, productionBox)
    """
    return ask(state, owner, kind="space", options=_mining_spaces(state, owner, "MINING_AREA"),
               then="mining.space", ctx={"card_id": "MINING_AREA"},
               title="Select a space with a steel or titanium bonus adjacent to one of your tiles")


@continuation("mining.space")
def _mining_space(state, owner, space_id, card_id):
    resources = tuple(r for r in ("steel", "titanium") if r in B.SPACES[space_id].bonus)
    return ask(state, owner, kind="option", options=resources, then="mining.resource",
               ctx={"card_id": card_id, "space_id": space_id},
               title="Select a resource to gain 1 unit of production", priority=Priority.COST)


@continuation("mining.resource")
def _mining_resource(state, owner, resource, card_id, space_id):
    state = P.add_production(state, owner, resource, 1)
    state = P.set_card_data(state, owner, card_id, resource)
    return P.place_any(state, owner, space_id, card_id, card_id)


@hook("MINING_RIGHTS", "MINING_AREA", name="production_box")
def mining_box(state, owner):
    """The production the tile gave, once it's on the board (for Robotic Workforce)."""
    p = state.player(owner)
    resource = p.card_data.get("MINING_AREA") or p.card_data.get("MINING_RIGHTS")
    return Units.of({resource: 1}) if resource else Units()


def _greenery_neighbour_spaces(state, owner):
    return [s for s in B.land_spaces(state, owner) if B.adjacent_with(state, s, B.is_greenery)]


@hook("ECOLOGICAL_ZONE", name="bespoke_can_play")
def ecological_zone_can_play(state, owner):
    return bool(_greenery_neighbour_spaces(state, owner))


@hook("ECOLOGICAL_ZONE", name="bespoke_play")
def ecological_zone_play(state, owner):
    """Ecological Zone (128): place this tile next to any greenery.

    Original: base/EcologicalZone.ts  (bespokePlay, bespokeCanPlay, onCardPlayed, onNonCardTagAdded)
    Played straight after Ecology Experts in the prelude phase it gets one extra animal, as in
    the original (the original's "including these" counting is off by one there).
    """
    p = state.player(owner)
    if state.phase == "preludes" and p.last_card_played == "ECOLOGY_EXPERTS":
        state = defer(state, owner, "gain.card_resource", {"card_id": "ECOLOGICAL_ZONE", "n": 1})
    return P.ask_place_tile(state, owner, "ECOLOGICAL_ZONE", spaces=_greenery_neighbour_spaces(state, owner),
                            card_id="ECOLOGICAL_ZONE", title="Select space next to greenery for special tile")


@hook("ECOLOGICAL_ZONE", name="on_card_played")
def ecological_zone_card_played(state, owner, card_id):
    """When you play an animal or plant tag, including these, add an animal here."""
    n = card_tag_count(card_id, "animal", "plant")
    return P.add_card_resources(state, owner, "ECOLOGICAL_ZONE", n) if n else state


@hook("ECOLOGICAL_ZONE", name="on_non_card_tag_added")
def ecological_zone_tag(state, owner, tag):
    return P.add_card_resources(state, owner, "ECOLOGICAL_ZONE", 1) if tag == "plant" else state


def _next_to_city_spaces(state, owner):
    return [s for s in B.land_spaces(state, owner) if B.adjacent_with(state, s, B.is_city)]


@hook("INDUSTRIAL_CENTER", name="bespoke_can_play")
def industrial_center_can_play(state, owner):
    return bool(_next_to_city_spaces(state, owner))


@hook("INDUSTRIAL_CENTER", name="bespoke_play")
def industrial_center_play(state, owner):
    """Industrial Center (123): place this tile next to a city tile.

    Original: base/IndustrialCenter.ts  (bespokePlay, bespokeCanPlay)
    """
    return P.ask_place_tile(state, owner, "INDUSTRIAL_CENTER", spaces=_next_to_city_spaces(state, owner),
                            card_id="INDUSTRIAL_CENTER", title="Select space adjacent to a city tile")


# ======================================================================================
# Card-played triggers
# ======================================================================================
@hook("DECOMPOSERS", name="bespoke_play")
def decomposers_play(state, owner):
    """Decomposers (131): two extra microbes when played right after Ecology Experts."""
    if state.phase == "preludes" and state.player(owner).last_card_played == "ECOLOGY_EXPERTS":
        state = defer(state, owner, "gain.card_resource", {"card_id": "DECOMPOSERS", "n": 2})
    return state


@hook("DECOMPOSERS", name="on_card_played")
def decomposers_card_played(state, owner, card_id):
    """Decomposers: when you play an animal, plant or microbe tag, including this, add a microbe.

    Original: base/Decomposers.ts  (onCardPlayed, onNonCardTagAdded, bespokePlay)
    """
    n = card_tag_count(card_id, *BIO_TAGS)
    return P.add_card_resources(state, owner, "DECOMPOSERS", n) if n else state


@hook("DECOMPOSERS", name="on_non_card_tag_added")
def decomposers_tag(state, owner, tag):
    return P.add_card_resources(state, owner, "DECOMPOSERS", 1) if tag == "plant" else state


@hook("OPTIMAL_AEROBRAKING", name="on_card_played")
def optimal_aerobraking_card_played(state, owner, card_id):
    """Optimal Aerobraking (031): when you play a space event, gain 3 M€ and 3 heat."""
    c = card(card_id)
    if c.type == "event" and "space" in c.tags:
        state = P.add_stock(state, owner, "megacredits", 3)
        state = P.add_stock(state, owner, "heat", 3)
    return state


@hook("MEDIA_GROUP", name="on_card_played")
def media_group_card_played(state, owner, card_id):
    """Media Group (109): after you play an event card, gain 3 M€."""
    if card(card_id).type == "event":
        state = defer(state, owner, "gain.stock", {"resource": "megacredits", "n": 3})
    return state


def _science_triggers(card_name, then):
    def on_card_played(state, owner, card_id):
        n = card_tag_count(card_id, "science")
        return P.get_hook(card_name, "on_science_tag_added")(state, owner, n) if n else state

    def on_non_card_tag_added(state, owner, tag):
        return P.get_hook(card_name, "on_science_tag_added")(state, owner, 1) if tag == "science" else state

    def on_science_tag_added(state, owner, count):
        prio = Priority.OLYMPUS_CONFERENCE if card_name == "OLYMPUS_CONFERENCE" else Priority.DISCARD_AND_DRAW
        for _ in range(count):
            state = defer(state, owner, then, priority=prio)
        return state

    return on_card_played, on_non_card_tag_added, on_science_tag_added


_mu = _science_triggers("MARS_UNIVERSITY", "mars_university.offer")
hook("MARS_UNIVERSITY", name="on_card_played")(_mu[0])
hook("MARS_UNIVERSITY", name="on_non_card_tag_added")(_mu[1])
hook("MARS_UNIVERSITY", name="on_science_tag_added")(_mu[2])


@continuation("mars_university.offer")
def _mars_university_offer(state, owner, _choice):
    """Mars University (073): when you play a science tag, including this, you may discard a
    card from hand to draw a card.

    Original: base/MarsUniversity.ts  (onCardPlayed, onNonCardTagAdded, onScienceTagAdded)
    Asks:     card (or pass) -> "mars_university.discard"
    """
    return ask(state, owner, kind="card", options=state.player(owner).hand, allow_pass=True,
               then="mars_university.discard", title="Mars University: discard a card to draw a card",
               priority=Priority.COST)


@continuation("mars_university.discard")
def _mars_university_discard(state, owner, card_id):
    if card_id is None:
        return state
    state = P.remove_from_hand(state, owner, [card_id])
    state = P.discard_cards(state, [card_id])
    return P.draw_cards(state, owner, 1)


_oc = _science_triggers("OLYMPUS_CONFERENCE", "olympus_conference.offer")
hook("OLYMPUS_CONFERENCE", name="on_card_played")(_oc[0])
hook("OLYMPUS_CONFERENCE", name="on_non_card_tag_added")(_oc[1])
hook("OLYMPUS_CONFERENCE", name="on_science_tag_added")(_oc[2])


@continuation("olympus_conference.offer")
def _olympus_offer(state, owner, _choice):
    """Olympus Conference (185): when you play a science tag, including this, either add a
    science resource here, or remove one to draw a card.

    Original: base/OlympusConference.ts  (onCardPlayed, onNonCardTagAdded, onScienceTagAdded)
    Asks:     option -> "olympus_conference.choice" (skipped when the card is empty)
    """
    if state.player(owner).resources_on("OLYMPUS_CONFERENCE") == 0:
        return P.add_card_resources(state, owner, "OLYMPUS_CONFERENCE", 1)
    return ask(state, owner, kind="option", options=("draw", "add"), then="olympus_conference.choice",
               title="Olympus Conference: remove a science resource to draw a card, or add one",
               priority=Priority.COST)


@continuation("olympus_conference.choice")
def _olympus_choice(state, owner, choice):
    if choice == "draw":
        state = P.add_card_resources(state, owner, "OLYMPUS_CONFERENCE", -1)
        return P.draw_cards(state, owner, 1)
    return P.add_card_resources(state, owner, "OLYMPUS_CONFERENCE", 1)


@hook("VIRAL_ENHANCERS", name="on_card_played")
def viral_enhancers_card_played(state, owner, card_id):
    """Viral Enhancers (074): when you play a plant, microbe or animal tag, including this,
    gain 1 plant or add 1 resource to that card.

    Original: base/ViralEnhancers.ts  (onCardPlayed, onNonCardTagAdded)
    Asks:     option per tag -> "viral_enhancers.choice" (only for animal/microbe cards)
    """
    n = card_tag_count(card_id, *BIO_TAGS)
    if n == 0:
        return state
    if card(card_id).resource_type not in ("animal", "microbe"):
        return P.add_stock(state, owner, "plants", n)
    for _ in range(n):
        state = ask(state, owner, kind="option", options=("add resource", "gain plant"),
                    then="viral_enhancers.choice", ctx={"card_id": card_id},
                    title=f"Viral Enhancers: add a resource to {card(card_id).name} or gain a plant")
    return state


@continuation("viral_enhancers.choice")
def _viral_enhancers_choice(state, owner, choice, card_id):
    if choice == "add resource":
        return P.add_card_resources(state, owner, card_id, 1)
    return P.add_stock(state, owner, "plants", 1)


@hook("VIRAL_ENHANCERS", name="on_non_card_tag_added")
def viral_enhancers_tag(state, owner, tag):
    return P.add_stock(state, owner, "plants", 1) if tag == "plant" else state


@hook("STANDARD_TECHNOLOGY", name="on_standard_project")
def standard_technology_sp(state, owner, project_id):
    """Standard Technology (156): after you pay for a standard project, except selling
    patents, gain 3 M€."""
    if project_id != "SELL_PATENTS_STANDARD_PROJECT":
        state = P.add_stock(state, owner, "megacredits", 3)
    return state


# ======================================================================================
# Actions
# ======================================================================================
@hook("EXTREME_COLD_FUNGUS", name="can_act")
def extreme_cold_fungus_can_act(state, owner):
    return True


@hook("EXTREME_COLD_FUNGUS", name="action")
def extreme_cold_fungus_action(state, owner):
    """Extreme-Cold Fungus (134): gain 1 plant, or add 2 microbes to another card.

    Original: base/ExtremeColdFungus.ts  (action, canAct)
    Asks:     card (pass = gain the plant) -> "extreme_cold_fungus.choice"
    """
    targets = P.cards_with_resource(state, owner, "microbe")
    if not targets:
        return P.add_stock(state, owner, "plants", 1)
    return ask(state, owner, kind="card", options=targets, allow_pass=True, then="extreme_cold_fungus.choice",
               title="Add 2 microbes to a card (or pass to gain 1 plant)")


@continuation("extreme_cold_fungus.choice")
def _ecf_choice(state, owner, card_id):
    if card_id is None:
        return P.add_stock(state, owner, "plants", 1)
    return P.add_card_resources(state, owner, card_id, 2)


@hook("SEARCH_FOR_LIFE", name="can_act")
def search_for_life_can_act(state, owner):
    return P.can_afford(state, owner, 1) and bool(state.deck or state.discard)


@hook("SEARCH_FOR_LIFE", name="action")
def search_for_life_action(state, owner):
    """Search for Life (005): pay 1 M€ to reveal the top card; if it has a microbe tag, add a
    science resource here. The revealed card is discarded.

    Original: base/SearchForLife.ts  (action, canAct, getVictoryPoints)
    """
    state = P.pay(state, owner, 1)
    state, drawn = P.draw(state, 1)
    if drawn:
        if "microbe" in card(drawn[0]).tags:
            state = P.add_card_resources(state, owner, "SEARCH_FOR_LIFE", 1)
            state = P.log(state, f"{owner} found life!")
        state = P.discard_cards(state, drawn)
    return state


@hook("SEARCH_FOR_LIFE", name="get_victory_points")
def search_for_life_vp(state, owner):
    return 3 if state.player(owner).resources_on("SEARCH_FOR_LIFE") > 0 else 0


@hook("WATER_SPLITTING_PLANT", name="bespoke_can_act")
def water_splitting_plant_can_act(state, owner):
    """Water Splitting Plant (177): the original only checks the Reds tax here.

    Diverges: always True, because Turmoil isn't modelled.
    """
    return True


@hook("POWER_INFRASTRUCTURE", name="can_act")
def power_infrastructure_can_act(state, owner):
    return state.player(owner).stock.energy > 0


@hook("POWER_INFRASTRUCTURE", name="action")
def power_infrastructure_action(state, owner):
    """Power Infrastructure (194): spend any amount of energy to gain that many M€.

    Original: base/PowerInfrastructure.ts  (action, canAct)
    Asks:     amount -> "power_infrastructure.amount"
    """
    energy = state.player(owner).stock.energy
    return ask(state, owner, kind="amount", options=tuple(range(1, energy + 1)),
               then="power_infrastructure.amount", title="Select amount of energy to spend")


@continuation("power_infrastructure.amount")
def _power_infrastructure_amount(state, owner, amount):
    state = P.spend(state, owner, "energy", amount)
    return P.add_stock(state, owner, "megacredits", amount)


# ======================================================================================
# Play-time effects
# ======================================================================================
@hook("ARTIFICIAL_LAKE", name="bespoke_can_play")
def artificial_lake_can_play(state, owner):
    """Artificial Lake (116): playable with no effect once the oceans are all placed."""
    if not P.can_place_ocean(state):
        return True
    return bool(B.land_spaces(state, owner))


@hook("INSULATION", name="bespoke_can_play")
def insulation_can_play(state, owner):
    return state.player(owner).production.heat >= 1


@hook("INSULATION", name="bespoke_play")
def insulation_play(state, owner):
    """Insulation (152): decrease heat production any number of steps and increase M€
    production the same number.

    Original: base/Insulation.ts  (bespokePlay, bespokeCanPlay)
    Asks:     amount -> "insulation.amount"
    """
    heat = state.player(owner).production.heat
    return ask(state, owner, kind="amount", options=tuple(range(1, heat + 1)), then="insulation.amount",
               title="Select amount of heat production to decrease")


@continuation("insulation.amount")
def _insulation_amount(state, owner, amount):
    state = P.add_production(state, owner, "heat", -amount)
    return P.add_production(state, owner, "megacredits", amount)


def _plants_after(state, owner, needed: int) -> bool:
    p = state.player(owner)
    viral = "VIRAL_ENHANCERS" in p.tableau
    return p.stock.plants >= needed or (viral and p.stock.plants >= needed - 1)


def _lose_plants_allow_negative(state, owner, n):
    # Viral Enhancers' plant arrives after this, so the stock may dip below zero for a moment.
    p = state.player(owner)
    return state.update_player(owner, stock=p.stock.add("plants", -n))


@hook("MOSS", name="bespoke_can_play")
def moss_can_play(state, owner):
    return _plants_after(state, owner, 1)


@hook("MOSS", name="bespoke_play")
def moss_play(state, owner):
    """Moss (122): lose 1 plant (Viral Enhancers' plant may pay for it).

    Original: base/Moss.ts  (bespokePlay, bespokeCanPlay)
    """
    return _lose_plants_allow_negative(state, owner, 1)


@hook("NITROPHILIC_MOSS", name="bespoke_can_play")
def nitrophilic_moss_can_play(state, owner):
    return _plants_after(state, owner, 2)


@hook("NITROPHILIC_MOSS", name="bespoke_play")
def nitrophilic_moss_play(state, owner):
    """Nitrophilic Moss (146): lose 2 plants (Viral Enhancers' plant may pay for one).

    Original: base/NitrophilicMoss.ts  (bespokePlay, bespokeCanPlay)
    """
    return _lose_plants_allow_negative(state, owner, 2)


@hook("NITROGEN_RICH_ASTEROID", name="bespoke_play")
def nitrogen_rich_asteroid_play(state, owner):
    """Nitrogen-Rich Asteroid (037): raise plant production 1 step, or 4 if you have 3 plant tags."""
    steps = 4 if P.tag_count(state, owner, "plant") >= 3 else 1
    return P.add_production(state, owner, "plants", steps)


@hook("TERRAFORMING_GANYMEDE", name="bespoke_play")
def terraforming_ganymede_play(state, owner):
    """Terraforming Ganymede (197): raise your TR 1 step per Jovian tag you have, including this."""
    return P.gain_tr(state, owner, 1 + P.tag_count(state, owner, "jovian"))


@hook("FLOODING", name="bespoke_play")
def flooding_play(state, owner):
    """Flooding (188): place an ocean; you may then remove 4 M€ from an owner of an adjacent tile.

    Original: base/Flooding.ts  (bespokePlay)
    Asks:     space -> "flooding.space", then player (or pass) -> "flooding.target"
    """
    if not P.can_place_ocean(state):
        return state
    return ask(state, owner, kind="space", options=B.ocean_spaces_available(state, owner),
               then="flooding.space", title="Select space for ocean tile", priority=Priority.PLACE_OCEAN_TILE)


@continuation("flooding.space")
def _flooding_space(state, owner, space_id):
    state = P.place_ocean(state, owner, space_id)
    targets = sorted({state.tiles[s].owner for s in B.ADJACENT[space_id]
                      if s in state.tiles and state.tiles[s].owner not in (None, owner)})
    return ask(state, owner, kind="player", options=targets, allow_pass=True, then="flooding.target",
               title="Select adjacent player to remove 4 M€ from", priority=Priority.BEFORE_OPPONENT_TRIGGER)


@continuation("flooding.target")
def _flooding_target(state, owner, target):
    return state if target is None else P.add_stock(state, target, "megacredits", -4)


def _add_or_plants(state, owner, plants: int, options: list[tuple[str, int]], title: str):
    """Shared shape of Imported Hydrogen, Large Convoy and Local Heat Trapping: gain plants, or
    add resources to one of your cards of a given type."""
    choices = [("plants", None, plants)]
    for rtype, n in options:
        for cid in P.cards_with_resource(state, owner, rtype):
            choices.append((rtype, cid, n))
    if len(choices) == 1:
        return P.add_stock(state, owner, "plants", plants)
    labels = tuple(f"gain {plants} plants" if cid is None else f"add {n} {rtype} to {cid}" for rtype, cid, n in choices)
    return ask(state, owner, kind="option", options=labels, then="add_or_plants.choice",
               ctx={"labels": labels, "choices": tuple(choices)}, title=title)


@continuation("add_or_plants.choice")
def _add_or_plants_choice(state, owner, label, labels, choices):
    rtype, cid, n = choices[labels.index(label)]
    if cid is None:
        return P.add_stock(state, owner, "plants", n)
    return P.add_card_resources(state, owner, cid, n)


@hook("IMPORTED_HYDROGEN", name="bespoke_play")
def imported_hydrogen_play(state, owner):
    """Imported Hydrogen (019): gain 3 plants, or add 3 microbes or 2 animals to another card.

    Original: base/ImportedHydrogen.ts  (bespokePlay)
    """
    return _add_or_plants(state, owner, 3, [("microbe", 3), ("animal", 2)], "Imported Hydrogen")


@hook("LARGE_CONVOY", name="bespoke_play")
def large_convoy_play(state, owner):
    """Large Convoy (143): gain 5 plants or add 4 animals to another card.

    Original: base/LargeConvoy.ts  (bespokePlay)
    """
    return _add_or_plants(state, owner, 5, [("animal", 4)], "Large Convoy")


@hook("LOCAL_HEAT_TRAPPING", name="can_play")
def local_heat_trapping_can_play(state, owner):
    """Local Heat Trapping (190): needs 5 heat on top of its cost (Helion may pay the 1 M€ in heat)."""
    p = state.player(owner)
    heat = p.stock.heat
    if P.card_cost(state, owner, "LOCAL_HEAT_TRAPPING") >= 1 and p.stock.megacredits == 0:
        heat -= 1
    return heat >= 5


@hook("LOCAL_HEAT_TRAPPING", name="play")
def local_heat_trapping_play(state, owner):
    """Local Heat Trapping (190): spend 5 heat to gain 4 plants or add 2 animals to another card.

    Original: base/LocalHeatTrapping.ts  (play, canPlay)
    """
    state = P.spend(state, owner, "heat", 5)
    return _add_or_plants(state, owner, 4, [("animal", 2)], "Local Heat Trapping")


# ======================================================================================
# Production attacks
# ======================================================================================
def _decrease_then_gain(state, owner, resource, n_lose, gain_first=False):
    """Decrease any player's `resource` production, then increase your own 1 step."""
    if gain_first:
        state = P.add_production(state, owner, resource, 1)
    targets = [p.id for p in state.players if p.production.get(resource) >= n_lose
               or (resource == "megacredits" and p.production.megacredits - n_lose >= -5)]
    others = [t for t in targets if t != owner]
    state = ask(state, owner, kind="player", options=others or targets, then="attack.decrease_production",
                ctx={"resource": resource, "n": n_lose}, title=f"Decrease {resource} production",
                priority=Priority.ATTACK_OPPONENT)
    if not gain_first:
        state = defer(state, owner, "gain.production", {"resource": resource, "n": 1},
                      priority=Priority.GAIN_RESOURCE_OR_PRODUCTION)
    return state


@continuation("attack.decrease_production")
def _attack_decrease(state, owner, target, resource, n):
    return P.add_production(state, target, resource, -n)


@hook("ASTEROID_MINING_CONSORTIUM", name="bespoke_can_play")
def asteroid_mining_consortium_can_play(state, owner):
    return True     # the original only adds a "you are your own target" warning here


@hook("ASTEROID_MINING_CONSORTIUM", name="bespoke_play")
def asteroid_mining_consortium_play(state, owner):
    """Asteroid Mining Consortium (002): decrease any titanium production 1 step, increase yours."""
    return _decrease_then_gain(state, owner, "titanium", 1)


@hook("GREAT_ESCARPMENT_CONSORTIUM", name="bespoke_play")
def great_escarpment_play(state, owner):
    """Great Escarpment Consortium (061): decrease any steel production 1 step, increase yours."""
    return _decrease_then_gain(state, owner, "steel", 1)


@hook("ENERGY_TAPPING", "POWER_SUPPLY_CONSORTIUM", name="bespoke_play")
def energy_steal_play(state, owner):
    """Energy Tapping (201) / Power Supply Consortium (160): decrease any energy production 1
    step and increase yours. If nobody has any, you gain first and then lose it again."""
    nobody = all(p.production.energy == 0 for p in state.players)
    return _decrease_then_gain(state, owner, "energy", 1, gain_first=nobody)


@hook("HACKERS", name="bespoke_play")
def hackers_play(state, owner):
    """Hackers (125): decrease any M€ production 2 steps (the +2 for you is in the data)."""
    targets = [p.id for p in state.players if p.production.megacredits - 2 >= -5]
    others = [t for t in targets if t != owner]
    return ask(state, owner, kind="player", options=others or targets, then="attack.decrease_production",
               ctx={"resource": "megacredits", "n": 2}, title="Decrease M€ production 2 steps",
               priority=Priority.ATTACK_OPPONENT)


# ======================================================================================
# Stealing and removing
# ======================================================================================
def _steal_options(state, owner, amounts: dict[str, int]):
    out = []
    for o in state.opponents(owner):
        for resource, n in amounts.items():
            if o.stock.get(resource) > 0:
                out.append((o.id, resource, n))
    return out


@hook("SABOTAGE", name="bespoke_play")
def sabotage_play(state, owner):
    """Sabotage (121): remove up to 3 titanium, 4 steel or 7 M€ from any player.

    Original: base/Sabotage.ts  (bespokePlay)
    Asks:     option (or pass) -> "attack.remove_stock"
    """
    options = _steal_options(state, owner, {"titanium": 3, "steel": 4, "megacredits": 7})
    labels = tuple(f"remove {n} {r} from {t}" for t, r, n in options)
    return ask(state, owner, kind="option", options=labels, allow_pass=True, then="attack.remove_stock",
               ctx={"labels": labels, "choices": tuple(options), "steal": False}, title="Sabotage")


@hook("HIRED_RAIDERS", name="bespoke_play")
def hired_raiders_play(state, owner):
    """Hired Raiders (124): steal up to 2 steel, or 3 M€, from any player.

    Original: base/HiredRaiders.ts  (bespokePlay)
    """
    options = _steal_options(state, owner, {"steel": 2, "megacredits": 3})
    labels = tuple(f"steal {n} {r} from {t}" for t, r, n in options)
    return ask(state, owner, kind="option", options=labels, allow_pass=True, then="attack.remove_stock",
               ctx={"labels": labels, "choices": tuple(options), "steal": True}, title="Hired Raiders")


@continuation("attack.remove_stock")
def _remove_stock(state, owner, label, labels, choices, steal):
    if label is None:
        return state
    target, resource, n = choices[labels.index(label)]
    taken = min(n, state.player(target).stock.get(resource))
    state = P.add_stock(state, target, resource, -taken)
    return P.add_stock(state, owner, resource, taken) if steal else state


@hook("VIRUS", name="bespoke_play")
def virus_play(state, owner):
    """Virus (050): remove up to 2 animals from any card, or 5 plants from any player.

    Original: base/Virus.ts  (bespokePlay)
    Asks:     option (or pass) -> "virus.choice"
    """
    choices = []
    for p in state.players:
        for cid in P.cards_with_resource(state, p.id, "animal", min_count=1):
            if p.id == owner or not (resources_protected(state, p.id, "animal") or CARDS[cid].protected_resources):
                choices.append(("card", cid))
    for o in state.opponents(owner):
        if o.stock.plants > 0 and not resources_protected(state, o.id, "plants"):
            choices.append(("plants", o.id))
    labels = tuple(f"remove 2 animals from {x}" if k == "card" else f"remove 5 plants from {x}" for k, x in choices)
    return ask(state, owner, kind="option", options=labels, allow_pass=True, then="virus.choice",
               ctx={"labels": labels, "choices": tuple(choices)}, title="Virus")


@continuation("virus.choice")
def _virus_choice(state, owner, label, labels, choices):
    if label is None:
        return state
    kind, target = choices[labels.index(label)]
    if kind == "card":
        return P.add_card_resources(state, P.resource_owner(state, target), target, -2)
    return P.add_stock(state, target, "plants", -5)


@hook("LAND_CLAIM", name="bespoke_can_play")
def land_claim_can_play(state, owner):
    return bool(_claimable(state))


def _claimable(state):
    return [s for s in B.MARS_SPACES if s not in state.tiles and s not in state.reserved]


@hook("LAND_CLAIM", name="bespoke_play")
def land_claim_play(state, owner):
    """Land Claim (066): reserve a non-reserved space; only you may place a tile there.

    Original: base/LandClaim.ts  (bespokePlay, bespokeCanPlay)
    """
    return ask(state, owner, kind="space", options=_claimable(state), then="land_claim.space",
               title="Select space for claim")


@continuation("land_claim.space")
def _land_claim_space(state, owner, space_id):
    from dataclasses import replace
    return replace(state, reserved=state.reserved.set(space_id, owner))


@hook("INDENTURED_WORKERS", name="get_card_discount")
def indentured_workers_discount(state, owner, card_id):
    # The next card you play this generation costs 8 M€ less.
    return 8 if state.player(owner).last_card_played == "INDENTURED_WORKERS" else 0


# ======================================================================================
# Robotic Workforce
# ======================================================================================
def production_box(state, owner, card_id) -> Units | None:
    """A card's production box: its hook if it has one, else the `production` in its data."""
    hook_fn = P.get_hook(card_id, "production_box")
    if hook_fn is not None:
        return hook_fn(state, owner)
    b = card(card_id).behavior or {}
    if "production" in b:
        return Units.of({r.lower(): count_countable(state, owner, card_id, v) for r, v in b["production"].items()})
    return None


def _robotic_targets(state, owner):
    out = []
    for cid in state.player(owner).tableau:
        c = card(cid)
        if "building" not in c.tags or c.type == "event":
            continue
        box = production_box(state, owner, cid)
        if box is not None and box != Units() and P.can_adjust_production(state, owner, box):
            out.append(cid)
    return out


@hook("ROBOTIC_WORKFORCE", name="bespoke_can_play")
def robotic_workforce_can_play(state, owner):
    return bool(_robotic_targets(state, owner))


@hook("ROBOTIC_WORKFORCE", name="bespoke_play")
def robotic_workforce_play(state, owner):
    """Robotic Workforce (086): duplicate the production box of one of your building cards.

    Original: base/RoboticWorkforce.ts, base/RoboticWorkforceBase.ts  (bespokePlay, bespokeCanPlay)
    Asks:     card -> "robotic_workforce.copy"
    Diverges: a copied `decreaseAnyProduction` attack is not repeated, only the owner's own
              production box.
    """
    return defer(state, owner, "robotic_workforce.ask", priority=Priority.ROBOTIC_WORKFORCE)


@continuation("robotic_workforce.ask")
def _robotic_ask(state, owner, _choice):
    return ask(state, owner, kind="card", options=_robotic_targets(state, owner), then="robotic_workforce.copy",
               title="Select builder card to copy", priority=Priority.COST)


@continuation("robotic_workforce.copy")
def _robotic_copy(state, owner, card_id):
    return P.add_production_units(state, owner, production_box(state, owner, card_id))


# ======================================================================================
# Standard projects and standard actions
# ======================================================================================
@hook("SELL_PATENTS_STANDARD_PROJECT", name="can_act")
def sell_patents_can_act(state, owner):
    return bool(state.player(owner).hand)


@hook("SELL_PATENTS_STANDARD_PROJECT", name="action")
def sell_patents_action(state, owner):
    """Sell Patents (SP8): discard any number of cards from hand for 1 M€ each.

    Original: base/standardProjects/SellPatentsStandardProject.ts  (action, actionEssence, canAct)
    Asks:     cards -> "sell_patents.sell"
    """
    hand = state.player(owner).hand
    return ask(state, owner, kind="cards", options=hand, min=1, max=len(hand), then="sell_patents.sell",
               title="Sell patents")


@continuation("sell_patents.sell")
def _sell_patents(state, owner, cards):
    cards = tuple(cards)
    state = P.remove_from_hand(state, owner, cards)
    state = P.discard_cards(state, cards)
    state = P.add_stock(state, owner, "megacredits", len(cards))
    return A.finish_standard_project(state, owner, "SELL_PATENTS_STANDARD_PROJECT")


@hook("SELL_PATENTS_STANDARD_PROJECT", name="action_essence")
def sell_patents_essence(state, owner):
    return state    # all the work happens in `action`


@hook("POWER_PLANT_STANDARD_PROJECT", name="action_essence")
def power_plant_essence(state, owner):
    """Power Plant (SP7): increase energy production 1 step."""
    return P.add_production(state, owner, "energy", 1)


@hook("ASTEROID_STANDARD_PROJECT", name="can_act")
def asteroid_sp_can_act(state, owner):
    # The original allows this at max temperature (with a warning), so this does too.
    return A.sp_affordable(state, owner, "ASTEROID_STANDARD_PROJECT")


@hook("ASTEROID_STANDARD_PROJECT", name="can_pay_with")
def asteroid_sp_pay_with(state, owner):
    return {}   # Kuiper Cooperative's asteroids (Pathfinders) aren't modelled


@hook("ASTEROID_STANDARD_PROJECT", name="action_essence")
def asteroid_sp_essence(state, owner):
    """Asteroid (SP1): raise the temperature 1 step."""
    return P.raise_temperature(state, owner, 1)


@hook("AQUIFER_STANDARD_PROJECT", name="can_act")
def aquifer_sp_can_act(state, owner):
    return A.sp_affordable(state, owner, "AQUIFER_STANDARD_PROJECT")


@hook("AQUIFER_STANDARD_PROJECT", name="can_pay_with")
def aquifer_sp_pay_with(state, owner):
    return {}


@hook("AQUIFER_STANDARD_PROJECT", name="action_essence")
def aquifer_sp_essence(state, owner):
    """Aquifer (SP2): place an ocean tile."""
    return P.ask_place_ocean(state, owner)


@hook("GREENERY_STANDARD_PROJECT", name="can_act")
def greenery_sp_can_act(state, owner):
    return bool(B.greenery_spaces(state, owner)) and A.sp_affordable(state, owner, "GREENERY_STANDARD_PROJECT")


@hook("GREENERY_STANDARD_PROJECT", name="can_pay_with")
def greenery_sp_pay_with(state, owner):
    return {}


@hook("GREENERY_STANDARD_PROJECT", name="action_essence")
def greenery_sp_essence(state, owner):
    """Greenery (SP5): place a greenery tile (and raise oxygen)."""
    return P.ask_place_tile(state, owner, "greenery", rule="greenery")


@hook("CITY_STANDARD_PROJECT", name="can_act")
def city_sp_can_act(state, owner):
    return bool(B.city_spaces(state, owner)) and A.sp_affordable(state, owner, "CITY_STANDARD_PROJECT")


@hook("CITY_STANDARD_PROJECT", name="can_pay_with")
def city_sp_pay_with(state, owner):
    return {}   # Prefabrication of Human Habitats (steel) is from another expansion


@hook("CITY_STANDARD_PROJECT", name="action_essence")
def city_sp_essence(state, owner):
    """City (SP4): place a city tile and increase M€ production 1 step."""
    state = P.ask_place_tile(state, owner, "city", rule="city")
    return P.add_production(state, owner, "megacredits", 1)


@hook("CONVERT_PLANTS", name="can_act")
def convert_plants_can_act(state, owner):
    return A.can_convert_plants(state, owner)


@hook("CONVERT_PLANTS", name="action")
def convert_plants_action(state, owner):
    """Convert plants (SA1): spend plants (8, or fewer with Ecoline) to place a greenery."""
    return A.convert_plants(state, owner)


@hook("CONVERT_HEAT", name="can_act")
def convert_heat_can_act(state, owner):
    return A.can_convert_heat(state, owner)


@hook("CONVERT_HEAT", name="action")
def convert_heat_action(state, owner):
    """Convert heat (SA2): spend 8 heat to raise the temperature 1 step."""
    return A.convert_heat(state, owner)

