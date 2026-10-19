"""Run a full game from the command line with random agents.

    cd src
    python -m engine.main --players 4 --seed 1
    python -m engine.main --players 3 --seed 7 --modules base corpera --log
    python -m engine.main --games 200 --players 4          # smoke test: many seeds, summary only

Any agent with a `choose(state, pending)` method can play; see `agents/base_agent.py`.
"""
from __future__ import annotations

import argparse
import sys
import time
from collections.abc import Mapping

from agents.base_agent import BaseAgent
from agents.random_agent import RandomAgent
from engine.game import is_over, new_game
from engine.game_state import GameOptions, GameState
from engine.pending import advance, resume
from engine.scoring import final_scores, ranking

DEFAULT_MODULES = ("base", "corpera", "prelude")
MAX_STEPS = 200_000     # guards against a rule bug looping forever


class GameStuck(RuntimeError):
    pass


def play(state: GameState, agents: Mapping[str, BaseAgent], max_steps: int = MAX_STEPS) -> GameState:
    """Answer questions until the game ends. Returns the final state."""
    state = advance(state)
    for _ in range(max_steps):
        if is_over(state):
            return state
        if not state.pending:
            raise GameStuck(f"nothing pending in phase {state.phase!r} but the game isn't over")
        question = state.pending[0]
        state = resume(state, agents[question.player].choose(state, question))
    raise GameStuck(f"no result after {max_steps} answers")


def run_game(n_players: int, seed: int, modules=DEFAULT_MODULES, log: bool = False,
             max_generations: int = 100) -> GameState:
    ids = [f"p{i + 1}" for i in range(n_players)]
    options = GameOptions(modules=tuple(modules), log=log, max_generations=max_generations)
    state = new_game(ids, seed=seed, options=options)
    agents = {pid: RandomAgent(seed=f"{seed}:{pid}") for pid in ids}
    return play(state, agents)


def print_result(state: GameState) -> None:
    scores = final_scores(state)
    print(f"Game over after {state.generation} generations "
          f"(temperature {state.temperature}, oxygen {state.oxygen}%, oceans {state.oceans}).")
    for place, pid in enumerate(ranking(state), start=1):
        s = scores[pid]
        parts = ", ".join(f"{k} {v}" for k, v in s.items() if k != "total" and v)
        corp = state.player(pid).corporation
        print(f"  {place}. {pid} ({corp}): {s['total']} VP  [{parts}]")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--players", type=int, default=2, help="number of players, 2 to 5")
    ap.add_argument("--seed", type=int, default=0, help="seed for the first game")
    ap.add_argument("--games", type=int, default=1, help="play this many games with seeds seed, seed+1, ...")
    ap.add_argument("--modules", nargs="+", default=list(DEFAULT_MODULES),
                    help="card modules to use (default: base corpera prelude)")
    ap.add_argument("--max-generations", type=int, default=100)
    ap.add_argument("--log", action="store_true", help="print the game log")
    args = ap.parse_args(argv)

    failures = 0
    started = time.perf_counter()
    for seed in range(args.seed, args.seed + args.games):
        try:
            state = run_game(args.players, seed, args.modules, log=args.log, max_generations=args.max_generations)
        except Exception as e:     # report and carry on, so one bad seed doesn't hide the rest
            failures += 1
            print(f"seed {seed}: {type(e).__name__}: {e}", file=sys.stderr)
            if args.games == 1:
                raise
            continue
        if args.games == 1:
            if args.log:
                print("\n".join(state.log))
            print_result(state)
    if args.games > 1:
        elapsed = time.perf_counter() - started
        print(f"{args.games - failures}/{args.games} games finished, {failures} failed, {elapsed:.1f}s")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
