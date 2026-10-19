"""Whole games with random agents: every seed must reach the end without an error."""
import pytest

from engine.main import run_game
from engine.scoring import final_scores


@pytest.mark.parametrize("players,seed", [(2, 1), (3, 2), (4, 3), (5, 4)])
def test_random_game_finishes(players, seed):
    state = run_game(players, seed)
    assert state.phase == "end"
    assert len(final_scores(state)) == players


def test_same_seed_same_game():
    a, b = run_game(3, 42), run_game(3, 42)
    assert a == b
