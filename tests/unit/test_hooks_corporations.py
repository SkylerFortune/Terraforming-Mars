"""Hooks for the base and Corporate Era corporations (engine/hooks/corporations.py)."""
from engine import actions as A
from engine import board as B
from engine import primitives as P
from engine.pending import advance
from helpers import answer, give, make_state, play


def test_credicor_rewards_expensive_cards_and_projects():
    s = give(make_state(), "p1", tableau=["CREDICOR"], stock={"megacredits": 25})
    s = play(s, "p1", "TREES")                      # costs 13
    assert s.player("p1").stock.megacredits == 25
    s = play(s, "p1", "GIANT_ICE_ASTEROID")         # costs 36
    assert s.player("p1").stock.megacredits == 29
    s = A.take_action(s, "p1", ("standard_project", "GREENERY_STANDARD_PROJECT"))
    assert s.player("p1").stock.megacredits == 29 - 23 + 4


def test_helion_can_pay_with_heat():
    s = give(make_state(), "p1", tableau=["HELION"], stock={"heat": 13})
    s = P.get_hook("HELION", "bespoke_play")(s, "p1")
    assert A.can_play_card(s, "p1", "TREES", ignore_global=True)


def test_interplanetary_cinematics_gains_on_events():
    s = give(make_state(), "p1", tableau=["INTERPLANETARY_CINEMATICS"])
    s = play(s, "p1", "ASTEROID")
    assert s.player("p1").stock.megacredits == 2


def test_mining_guild_gains_on_steel_bonus_spaces():
    s = give(make_state(), "p1", tableau=["MINING_GUILD"])
    steel = next(sp for sp in B.land_spaces(s, "p1") if "steel" in B.SPACES[sp].bonus)
    plain = next(sp for sp in B.land_spaces(s, "p1") if not B.SPACES[sp].bonus)
    s = advance(P.place_city(s, "p1", plain))
    assert s.player("p1").production.steel == 0
    s = advance(P.place_greenery(s, "p1", steel))
    assert s.player("p1").production.steel == 1


def test_tharsis_republic_city_triggers():
    s = give(make_state(), "p1", tableau=["THARSIS_REPUBLIC"])
    s = advance(P.place_city(s, "p1", B.city_spaces(s, "p1")[0]))
    p = s.player("p1")
    assert (p.stock.megacredits, p.production.megacredits) == (3, 1)
    s = advance(P.place_city(s, "p2", B.city_spaces(s, "p2")[0]))
    p = s.player("p1")
    assert (p.stock.megacredits, p.production.megacredits) == (3, 2)


def test_tharsis_republic_ignores_cities_off_mars():
    s = give(make_state(), "p1", tableau=["THARSIS_REPUBLIC"])
    s = advance(P.place_city(s, "p2", B.GANYMEDE_COLONY))
    assert s.player("p1").production.megacredits == 0


def test_thorgate_discounts_power_plant():
    s = give(make_state(), "p1", tableau=["THORGATE"])
    assert A.standard_project_cost(s, "p1", "POWER_PLANT_STANDARD_PROJECT") == 8
    assert A.standard_project_cost(s, "p1", "ASTEROID_STANDARD_PROJECT") == 14


def test_united_nations_mars_initiative_needs_a_tr_raise_this_generation():
    s = give(make_state(), "p1", tableau=["UNITED_NATIONS_MARS_INITIATIVE"], stock={"megacredits": 3}, tr=20)
    assert not A.can_use_action(s, "p1", "UNITED_NATIONS_MARS_INITIATIVE")
    s = P.gain_tr(s, "p1", 1)
    assert A.can_use_action(s, "p1", "UNITED_NATIONS_MARS_INITIATIVE")
    s = advance(A.use_action(s, "p1", "UNITED_NATIONS_MARS_INITIATIVE"))
    assert s.player("p1").tr == 22


def test_saturn_systems_counts_any_players_jovian_tags():
    s = give(make_state(), "p1", tableau=["SATURN_SYSTEMS"])
    s = play(s, "p2", "IO_MINING_INDUSTRIES")
    assert s.player("p1").production.megacredits == 1
