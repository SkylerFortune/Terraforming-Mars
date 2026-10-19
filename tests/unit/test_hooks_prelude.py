"""Hooks for the Prelude expansion (engine/hooks/prelude.py)."""
from engine import actions as A
from engine import board as B
from engine import primitives as P
from engine.pending import advance
from helpers import answer, give, make_state, play, question


def test_point_luna_draws_for_earth_tags():
    s = give(make_state(), "p1", tableau=["POINT_LUNA"])
    s = play(s, "p1", "LUNA_GOVERNOR")             # two Earth tags
    assert len(s.player("p1").hand) == 2


def test_robinson_industries_raises_a_lowest_production():
    s = give(make_state(), "p1", tableau=["ROBINSON_INDUSTRIES"], stock={"megacredits": 4},
             production={"megacredits": 1, "steel": 1, "titanium": 1, "plants": 1, "energy": 1})
    s = advance(A.use_action(s, "p1", "ROBINSON_INDUSTRIES"))
    p = s.player("p1")
    assert (p.stock.megacredits, p.production.heat) == (0, 1)


def test_valley_trust_plays_one_of_three_preludes():
    s = make_state(prelude_deck=("BUSINESS_EMPIRE", "GALILEAN_MINING", "HUGE_ASTEROID", "DONATION"))
    s = give(s, "p1", tableau=["VALLEY_TRUST"], corporation="VALLEY_TRUST", first_action_done=False,
             stock={"megacredits": 6})
    s = advance(A.first_action(s, "p1"))
    assert set(question(s).options) == {"BUSINESS_EMPIRE", "GALILEAN_MINING", "HUGE_ASTEROID"}
    s = answer(s, "BUSINESS_EMPIRE")
    p = s.player("p1")
    assert p.production.megacredits == 6 and p.stock.megacredits == 0
    assert s.prelude_deck == ("DONATION",)
    assert {"GALILEAN_MINING", "HUGE_ASTEROID"} <= set(s.discard)


def test_vitor_funds_an_award_for_free_and_rewards_vp_cards():
    s = give(make_state(), "p1", tableau=["VITOR"], corporation="VITOR", first_action_done=False)
    s = answer(advance(A.first_action(s, "p1")), "Banker")
    assert s.funded_awards == (("Banker", "p1"),)
    s = play(s, "p1", "TREES")                     # 1 VP
    assert s.player("p1").stock.megacredits == 3
    s = play(s, "p1", "ASTEROID")                  # no VP
    assert s.player("p1").stock.megacredits == 3


def test_lava_tube_settlement_needs_a_volcanic_space_and_energy():
    s = make_state()
    assert not A.can_play_card(s, "p1", "LAVA_TUBE_SETTLEMENT", check_cost=False)
    s = give(s, "p1", production={"energy": 1})
    s = play(s, "p1", "LAVA_TUBE_SETTLEMENT")
    assert all(B.SPACES[sp].volcanic for sp in question(s).options)


def test_aquifer_turbines_counts_ocean_adjacency_towards_its_cost():
    s = make_state()
    assert not A.can_play_card(s, "p1", "AQUIFER_TURBINES", check_cost=False)
    s = give(s, "p1", stock={"megacredits": 3})
    s = play(s, "p1", "AQUIFER_TURBINES")
    s = answer(s, question(s).options[0])
    p = s.player("p1")
    assert p.production.energy == 2 and s.oceans == 1


def test_paying_preludes_fizzle_without_money():
    s = make_state()
    for prelude in ("BUSINESS_EMPIRE", "GALILEAN_MINING", "HUGE_ASTEROID"):
        assert not A.can_play_card(s, "p1", prelude, check_cost=False)
    s = give(s, "p1", stock={"megacredits": 5})
    assert A.can_play_card(s, "p1", "HUGE_ASTEROID", check_cost=False)
    s = play(s, "p1", "HUGE_ASTEROID")
    assert s.temperature == -24 and s.player("p1").stock.megacredits == 0


def test_eccentric_sponsor_discounts_the_card_it_plays():
    s = give(make_state(phase="preludes"), "p1", hand=["GIANT_ICE_ASTEROID"], stock={"megacredits": 11})
    s = play(s, "p1", "ECCENTRIC_SPONSOR")
    assert question(s).options == ("GIANT_ICE_ASTEROID",)
    s = answer(s, "GIANT_ICE_ASTEROID")
    assert "GIANT_ICE_ASTEROID" in s.player("p1").events


def test_eccentric_sponsor_fizzles_with_nothing_playable():
    s = give(make_state(phase="preludes"), "p1", preludes_in_hand=["ECCENTRIC_SPONSOR"])
    s = play(s, "p1", "ECCENTRIC_SPONSOR")
    p = s.player("p1")
    assert p.stock.megacredits == 15 and "ECCENTRIC_SPONSOR" not in p.tableau


def test_ecology_experts_ignores_global_requirements():
    s = give(make_state(phase="preludes"), "p1", hand=["GRASS"], stock={"megacredits": 11})
    assert not A.can_play_card(s, "p1", "GRASS")
    assert A.can_play_card(s, "p1", "ECOLOGY_EXPERTS", check_cost=False)
    s = play(s, "p1", "ECOLOGY_EXPERTS")
    s = answer(s, "GRASS")
    assert "GRASS" in s.player("p1").tableau


def test_ecology_experts_then_decomposers_gets_the_bonus_microbes():
    s = give(make_state(phase="preludes"), "p1", hand=["DECOMPOSERS"], stock={"megacredits": 5})
    s = play(s, "p1", "ECOLOGY_EXPERTS")
    s = answer(s, "DECOMPOSERS")
    assert s.player("p1").resources_on("DECOMPOSERS") == 3
