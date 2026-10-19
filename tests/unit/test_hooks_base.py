"""Hooks for base-game and Corporate Era project cards (engine/hooks/base.py)."""
from engine import actions as A
from engine import board as B
from engine.scoring import card_vp
from helpers import act, answer, give, make_state, play, question, tile


def ocean_space():
    return B.OCEAN_SPACES[0]


def test_arctic_algae_gains_plants_when_anyone_places_an_ocean():
    s = give(make_state(), "p1", tableau=["ARCTIC_ALGAE"])
    from engine import primitives as P
    s = P.ask_place_ocean(s, "p2")
    s = answer(play_nothing(s), ocean_space())
    assert s.player("p1").stock.plants == 2


def play_nothing(s):
    from engine.pending import advance
    return advance(s)


def test_herbivores_only_counts_own_greenery():
    s = give(make_state(), "p1", tableau=["HERBIVORES"])
    land = B.land_spaces(s, "p1")
    from engine import primitives as P
    s = play_nothing(P.place_greenery(s, "p2", land[0]))
    assert s.player("p1").resources_on("HERBIVORES") == 0
    s = play_nothing(P.place_greenery(s, "p1", land[5]))
    assert s.player("p1").resources_on("HERBIVORES") == 1


def test_pets_and_rover_construction_trigger_on_any_city():
    from engine import primitives as P
    s = give(make_state(), "p1", tableau=["PETS", "ROVER_CONSTRUCTION"])
    s = play_nothing(P.place_city(s, "p2", B.city_spaces(s, "p2")[0]))
    p1 = s.player("p1")
    assert p1.resources_on("PETS") == 1
    assert p1.stock.megacredits == 2


def test_immigrant_city_needs_energy_production():
    s = make_state()
    assert not A.can_play_card(s, "p1", "IMMIGRANT_CITY", check_cost=False)
    s = give(s, "p1", production={"energy": 1})
    assert A.can_play_card(s, "p1", "IMMIGRANT_CITY", check_cost=False)


def test_immigrant_city_counts_its_own_city_before_losing_production():
    s = give(make_state(), "p1", production={"energy": 1})
    s = play(s, "p1", "IMMIGRANT_CITY")
    s = answer(s, question(s).options[0])
    p = s.player("p1")
    assert p.production.energy == 0
    assert p.production.megacredits == -1      # +1 for its own city, then -2


def test_noctis_city_goes_on_the_reserved_space():
    s = give(make_state(), "p1", production={"energy": 1})
    s = play(s, "p1", "NOCTIS_CITY")
    assert s.tiles[B.NOCTIS_CITY].owner == "p1"
    assert s.player("p1").production.megacredits == 3


def test_urbanized_area_needs_two_adjacent_cities():
    s = give(make_state(), "p1", production={"energy": 1})
    assert not A.can_play_card(s, "p1", "URBANIZED_AREA", check_cost=False)
    target = next(sp for sp in B.land_spaces(s, "p1")
                  if len([a for a in B.ADJACENT[sp] if B.SPACES[a].type != "ocean"]) >= 2)
    a, b = [x for x in B.ADJACENT[target] if B.SPACES[x].type != "ocean"][:2]
    s = tile(tile(s, a, "city", "p2"), b, "city", "p2")
    assert A.can_play_card(s, "p1", "URBANIZED_AREA", check_cost=False)
    s = play(s, "p1", "URBANIZED_AREA")
    assert target in question(s).options


def test_mining_rights_raises_the_production_of_the_bonus():
    s = make_state()
    s = play(s, "p1", "MINING_RIGHTS")
    space = next(sp for sp in question(s).options if B.SPACES[sp].bonus == ("titanium",)) \
        if any(B.SPACES[sp].bonus == ("titanium",) for sp in question(s).options) else question(s).options[0]
    s = answer(s, space)
    resource = "titanium" if "titanium" in B.SPACES[space].bonus else "steel"
    assert s.player("p1").production.get(resource) == 1
    assert s.tiles[space].type == "MINING_RIGHTS"


def test_mining_area_must_be_next_to_own_tile():
    s = make_state()
    assert not A.can_play_card(s, "p1", "MINING_AREA", check_cost=False)


def test_decomposers_counts_its_own_microbe_tag():
    s = make_state()
    s = play(s, "p1", "DECOMPOSERS")
    assert s.player("p1").resources_on("DECOMPOSERS") == 1


def test_ecological_zone_needs_a_greenery_and_counts_its_tags():
    s = make_state()
    assert not A.can_play_card(s, "p1", "ECOLOGICAL_ZONE", check_cost=False, ignore_global=True)
    g = B.land_spaces(s, "p1")[10]
    s = tile(s, g, "greenery", "p2")
    s = play(s, "p1", "ECOLOGICAL_ZONE")
    s = answer(s, question(s).options[0])
    assert s.player("p1").resources_on("ECOLOGICAL_ZONE") == 2   # animal + plant tags


def test_optimal_aerobraking_pays_out_for_space_events():
    s = give(make_state(), "p1", tableau=["OPTIMAL_AEROBRAKING"])
    s = play(s, "p1", "ASTEROID")
    p = s.player("p1")
    assert p.stock.megacredits == 3
    assert p.stock.heat == 3


def test_media_group_pays_for_events():
    s = give(make_state(), "p1", tableau=["MEDIA_GROUP"])
    s = play(s, "p1", "ASTEROID")
    assert s.player("p1").stock.megacredits == 3


def test_mars_university_offers_a_discard_per_science_tag():
    s = give(make_state(), "p1", hand=["ASTEROID"])
    s = play(s, "p1", "MARS_UNIVERSITY")
    assert question(s).then == "mars_university.discard"
    s = answer(s, "ASTEROID")
    p = s.player("p1")
    assert "ASTEROID" not in p.hand and len(p.hand) == 1


def test_olympus_conference_adds_then_offers_a_draw():
    s = make_state()
    s = play(s, "p1", "OLYMPUS_CONFERENCE")
    assert s.player("p1").resources_on("OLYMPUS_CONFERENCE") == 1
    s = play(s, "p1", "RESEARCH")     # two science tags
    hand = len(s.player("p1").hand)
    s = answer(s, "draw")           # the card is then empty, so the second tag just adds
    p = s.player("p1")
    assert p.resources_on("OLYMPUS_CONFERENCE") == 1
    assert len(p.hand) == hand + 1


def test_viral_enhancers_gains_plants_for_plain_plant_cards():
    s = give(make_state(), "p1", tableau=["VIRAL_ENHANCERS"])
    s = play(s, "p1", "TREES")      # Trees itself gives 1 plant
    assert s.player("p1").stock.plants == 2


def test_standard_technology_skips_sell_patents():
    s = give(make_state(), "p1", tableau=["STANDARD_TECHNOLOGY"], stock={"megacredits": 11}, hand=["TREES"])
    s = A.take_action(s, "p1", ("standard_project", "POWER_PLANT_STANDARD_PROJECT"))
    assert s.player("p1").stock.megacredits == 3
    s = A.take_action(s, "p1", ("standard_project", "SELL_PATENTS_STANDARD_PROJECT"))
    s = answer(play_nothing(s), ("TREES",))
    assert s.player("p1").stock.megacredits == 4


def test_extreme_cold_fungus_gains_a_plant_without_microbe_cards():
    s = give(make_state(), "p1", tableau=["EXTREME_COLD_FUNGUS"])
    s = act(s, "p1", "EXTREME_COLD_FUNGUS")
    assert s.player("p1").stock.plants == 1


def test_search_for_life_scores_three_with_any_resource():
    s = give(make_state(), "p1", tableau=["SEARCH_FOR_LIFE"])
    assert card_vp(s, "p1", "SEARCH_FOR_LIFE") == 0
    s = give(s, "p1", card_resources={"SEARCH_FOR_LIFE": 2})
    assert card_vp(s, "p1", "SEARCH_FOR_LIFE") == 3


def test_power_infrastructure_converts_energy():
    s = give(make_state(), "p1", tableau=["POWER_INFRASTRUCTURE"], stock={"energy": 4})
    s = act(s, "p1", "POWER_INFRASTRUCTURE")
    s = answer(s, 3)
    p = s.player("p1")
    assert (p.stock.energy, p.stock.megacredits) == (1, 3)


def test_insulation_moves_heat_production_to_megacredits():
    s = give(make_state(), "p1", production={"heat": 3})
    s = play(s, "p1", "INSULATION")
    s = answer(s, 2)
    p = s.player("p1")
    assert (p.production.heat, p.production.megacredits) == (1, 2)


def test_moss_can_use_viral_enhancers_plant():
    s = make_state()
    assert not A.can_play_card(s, "p1", "MOSS", check_cost=False, ignore_global=True)
    s = give(s, "p1", tableau=["VIRAL_ENHANCERS"])
    assert A.can_play_card(s, "p1", "MOSS", check_cost=False, ignore_global=True)
    s = play(s, "p1", "MOSS")
    assert s.player("p1").stock.plants == 0


def test_nitrophilic_moss_with_viral_enhancers_needs_one_plant():
    s = give(make_state(), "p1", tableau=["VIRAL_ENHANCERS"], stock={"plants": 1})
    assert A.can_play_card(s, "p1", "NITROPHILIC_MOSS", check_cost=False, ignore_global=True)
    s = play(s, "p1", "NITROPHILIC_MOSS")
    assert s.player("p1").stock.plants == 0


def test_nitrogen_rich_asteroid_rewards_three_plant_tags():
    s = make_state()
    assert play(s, "p1", "NITROGEN_RICH_ASTEROID").player("p1").production.plants == 1
    s = give(s, "p1", tableau=["TREES", "GRASS", "LICHEN"])
    assert play(s, "p1", "NITROGEN_RICH_ASTEROID").player("p1").production.plants == 4


def test_terraforming_ganymede_counts_itself():
    s = give(make_state(), "p1", tableau=["IO_MINING_INDUSTRIES"], tr=20)
    s = play(s, "p1", "TERRAFORMING_GANYMEDE")
    assert s.player("p1").tr == 22     # Io Mining Industries plus this card


def test_flooding_takes_four_from_an_adjacent_owner():
    s = make_state()
    sp = ocean_space()
    land = next(a for a in B.ADJACENT[sp] if B.SPACES[a].type == "land")
    s = tile(s, land, "city", "p2")
    s = give(s, "p2", stock={"megacredits": 10})
    s = play(s, "p1", "FLOODING")
    s = answer(s, sp, "p2")
    assert s.player("p2").stock.megacredits == 6


def test_imported_hydrogen_without_targets_gives_plants():
    s = play(make_state(), "p1", "IMPORTED_HYDROGEN")
    s = answer(s, question(s).options[0]) if question(s) else s
    assert s.player("p1").stock.plants == 3


def test_large_convoy_can_feed_an_animal_card():
    s = give(make_state(), "p1", tableau=["PETS"])
    s = play(s, "p1", "LARGE_CONVOY")
    q = question(s)
    while q.then != "add_or_plants.choice":     # the ocean comes first
        s = answer(s, q.options[0])
        q = question(s)
    s = answer(s, "add 4 animal to PETS")
    assert s.player("p1").resources_on("PETS") == 4


def test_local_heat_trapping_needs_five_heat():
    s = give(make_state(), "p1", stock={"heat": 4, "megacredits": 1})
    assert not A.can_play_card(s, "p1", "LOCAL_HEAT_TRAPPING")
    s = give(s, "p1", stock={"heat": 1})
    assert A.can_play_card(s, "p1", "LOCAL_HEAT_TRAPPING")


def test_asteroid_mining_consortium_prefers_opponents():
    s = give(make_state(), "p1", production={"titanium": 1})
    s = give(s, "p2", production={"titanium": 1})
    s = play(s, "p1", "ASTEROID_MINING_CONSORTIUM")
    assert s.player("p2").production.titanium == 0
    assert s.player("p1").production.titanium == 2


def test_energy_tapping_with_no_energy_anywhere_steals_back_its_own_gain():
    s = play(make_state(), "p1", "ENERGY_TAPPING")
    assert s.player("p1").production.energy == 0


def test_hackers_hits_opponent_megacredit_production():
    s = give(make_state(), "p1", production={"energy": 1})
    s = play(s, "p1", "HACKERS")
    assert s.player("p2").production.megacredits == -2
    assert s.player("p1").production.megacredits == 2


def test_sabotage_and_hired_raiders():
    s = give(make_state(), "p2", stock={"megacredits": 5, "steel": 1})
    s = play(s, "p1", "SABOTAGE")
    s = answer(s, "remove 7 megacredits from p2")
    assert s.player("p2").stock.megacredits == 0
    s = play(s, "p1", "HIRED_RAIDERS")
    s = answer(s, "steal 2 steel from p2")
    assert s.player("p1").stock.steel == 1


def test_virus_respects_protected_habitats():
    s = give(make_state(), "p2", tableau=["PETS", "PROTECTED_HABITATS"], card_resources={"PETS": 3},
             stock={"plants": 6})
    s = play(s, "p1", "VIRUS")
    assert question(s) is None or not question(s).options


def test_land_claim_reserves_a_space():
    s = play(make_state(), "p1", "LAND_CLAIM")
    sp = B.land_spaces(s, "p1")[0]
    s = answer(s, sp)
    assert s.reserved[sp] == "p1"
    assert sp not in B.land_spaces(s, "p2")


def test_indentured_workers_discounts_only_the_next_card():
    s = play(make_state(), "p1", "INDENTURED_WORKERS")
    from engine import primitives as P
    assert P.card_cost(s, "p1", "TREES") == 13 - 8


def test_robotic_workforce_copies_a_building_production_box():
    s = give(make_state(), "p1", tableau=["NOCTIS_CITY"], production={"energy": 2})
    s = play(s, "p1", "ROBOTIC_WORKFORCE")
    p = s.player("p1")
    assert (p.production.energy, p.production.megacredits) == (1, 3)


def test_city_standard_project_places_and_raises_production():
    s = give(make_state(), "p1", stock={"megacredits": 25})
    s = A.take_action(s, "p1", ("standard_project", "CITY_STANDARD_PROJECT"))
    s = answer(play_nothing(s), B.city_spaces(s, "p1")[0])
    p = s.player("p1")
    assert p.production.megacredits == 1
    assert len(B.cities(s, "p1")) == 1
