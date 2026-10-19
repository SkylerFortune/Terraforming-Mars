# The game engine

`src/engine/` is a rules engine for Terraforming Mars written in Python. It plays complete
games of the base game with the Corporate Era and Prelude expansions on the Tharsis board,
for 2 to 5 players. Card rules come from two places: the card data in `src/data/*.json`, run
by a generic interpreter, and hand-written hooks for the rules the data can't express.

The rules follow the open-source [terraforming-mars](https://github.com/terraforming-mars/terraforming-mars)
server, which served as the reference. The Python is written from each card's rules; it is
not a line-by-line translation.

## Running a game

From `src/`:

```bash
python -m engine.main --players 4 --seed 1             # one game, final scores
python -m engine.main --players 4 --seed 1 --log       # the same game with its full log
python -m engine.main --players 3 --games 200          # 200 seeds, prints how many finished
python -m engine.main --modules base corpera           # without Prelude
```

| Option | Default | Meaning |
| --- | --- | --- |
| `--players` | 2 | Number of players, 2 to 5 |
| `--seed` | 0 | Seed of the first game. The same seed always gives the same game. |
| `--games` | 1 | Play this many games with consecutive seeds and print a summary |
| `--modules` | `base corpera prelude` | Which card sets to use |
| `--max-generations` | 100 | Stop after this generation even if Mars isn't terraformed |
| `--log` | off | Print the game log |

The players are `RandomAgent`s (`src/agents/random_agent.py`), which answer every question
at random from a seeded generator, so a game is reproducible from its seed.

Tests run from the repository root:

```bash
pip install pytest
python -m pytest            # pyproject.toml puts src/ on the path
```

## Playing from code

The whole game is a sequence of questions. The engine never blocks waiting for input: it
records the question on the state and returns.

```python
from engine.game import new_game, is_over
from engine.pending import advance, resume
from engine.scoring import final_scores

state = advance(new_game(["alice", "bob"], seed=7))
while not is_over(state):
    question = state.pending[0]           # a Pending
    choice = my_agent(question.player).choose(state, question)
    state = resume(state, choice)         # answer it and run up to the next question
print(final_scores(state))
```

A `Pending` question has:

| Field | Meaning |
| --- | --- |
| `player` | Who must answer |
| `kind` | What is being chosen: `action`, `card`, `cards`, `space`, `player`, `option`, `amount`, `award` |
| `options` | The valid answers |
| `min`, `max` | For multi-select questions (`multi` is true), how many options to pick |
| `allow_pass` | Whether `None` (decline) is a valid answer |
| `title` | A human-readable prompt |

The answer is one of `options`, or a tuple of distinct options for a multi-select question,
or `None` to pass where allowed. Anything else raises `InvalidChoice`. Questions with only
one possible answer are answered automatically, so agents only see real decisions.

An agent is any object with `choose(state, pending)`; subclass `agents.base_agent.BaseAgent`.

### Actions

On their turn a player answers a question of kind `action`. Its options are tuples:

| Action | Meaning |
| --- | --- |
| `("play", card_id)` | Play a card from hand |
| `("action", card_id)` | Use the action of a card in play |
| `("first_action", corporation_id)` | The corporation's first action (always the only option until it's done) |
| `("standard_project", project_id)` | Use a standard project |
| `("convert_plants",)` / `("convert_heat",)` | Plants to greenery, heat to temperature |
| `("claim_milestone", name)` / `("fund_award", name)` | Milestones and awards |
| `("end_turn",)` | Stop after one action this turn |
| `("pass",)` | Pass for the rest of the generation |

## How it works

### State

`GameState` (`game_state.py`) is immutable: frozen dataclasses, tuples, and `FMap`, a
hashable read-only mapping. Every function takes a state and returns a new one, so any state
can be kept, compared, hashed or saved, and an agent can explore moves without copying
anything. Randomness comes from the seed and a counter stored in the state (`state.rng()`),
never from a global generator.

### The pending queue

`state.pending` (`pending.py`) holds two kinds of entries, ordered by `Priority` and then by
insertion, like the original server's deferred-action queue:

- **questions** for a player, created with `ask(...)`, and
- **deferred steps** (`kind="auto"`), created with `defer(...)`, for effects that must
  happen after the current one finishes.

Each entry names its **continuation**: a string key registered with `@continuation(key)`,
plus keyword data. When the entry is reached, the engine calls
`CONTINUATIONS[key](state, player, choice, **data)`. Continuations are never closures, which
is what keeps the state copyable.

`advance(state)` runs deferred steps until a question is at the front. `resume(state,
choice)` answers that question and advances. The flow of the game (turns, phases,
generations) is also made of deferred steps, with `Priority.FLOW`, so it always waits until
every effect of the current action has resolved.

### Cards

`cards.py` loads every card from `src/data/*.json` into a `CardDef`. Playing a card
(`actions.play_card`) does, in order:

1. pay its cost (after discounts),
2. run the `bespoke_play_before` hook, if any,
3. run the `play` hook if the card has one; otherwise run its `behavior` data, then its
   `bespoke_play` hook,
4. put it in the player's tableau (or events), and
5. fire `on_card_played` for its owner and `on_card_played_by_any_player` for everyone.

Whether a card is playable (`actions.can_play_card`) checks its cost, its requirements
(`requirements.py`), whether its behavior can run, and its `bespoke_can_play` and `can_play`
hooks.

The behavior interpreter (`behavior.py`) runs a card's `behavior`, `action` or
`firstAction` data: production, stock, tiles, global parameters, drawing cards, adding and
removing card resources, choices between alternatives (`or`), costs to spend, and attacks on
other players' production or plants. Clauses from expansions that aren't modelled (colonies,
Turmoil, the Moon, Underworld) make the card unplayable instead of half-working.

### Hooks

Hooks are the hand-written rules, in `engine/hooks/`, one module per expansion. Each is a
function registered for a card and a hook name:

```python
@hook("ARCTIC_ALGAE", name="on_tile_placed")
def arctic_algae_tile(state, owner, active, space_id, board_type):
    ...
```

The hook names are the original server's method names in snake_case, and the engine calls
them at the same moments. `engine/hooks/README.md` lists every hook and its signature, and
`engine/hooks/STATUS.md` (generated by `tools/hook_status.py`) shows which cards are done.

Every card from Base, Corporate Era and Prelude that needs hooks has them: 71 cards,
including the standard projects and standard actions. The other expansions have empty
modules ready to fill in.

### Board, scoring and phases

- `board.py`: the Tharsis map, its 61 spaces and their placement bonuses, adjacency, and which
  spaces are legal for oceans, cities, greeneries and special tiles. Ganymede Colony and
  Phobos Space Haven are the two off-Mars spaces.
- `primitives.py`: the building blocks hooks use: stock, production, card resources,
  drawing and discarding, TR, the global parameters (with their bonus steps), tile
  placement with its bonuses, payment, and trigger dispatch.
- `scoring.py`: Tharsis milestones and awards, card VP, and the final score breakdown.
- `game.py`: setup (corporations, preludes, the first hand), the prelude phase, turns of one
  or two actions, production, research, and the final greenery conversion. The game ends
  after the generation in which temperature, oxygen and oceans are all at their maximum.

## Where it differs from the original

These are deliberate simplifications, each marked in the code with a `Diverges:` note:

- **Payment is automatic.** The original asks how to pay; this engine spends titanium and
  steel first, then other sources (such as Psychrophiles' microbes), then M€, then heat for
  Helion. It overpays by at most one unit.
- **Solo mode isn't modelled**, so games need 2 to 5 players and solo-only effects (Tharsis
  Republic's neutral cities, the Buffer Gas project) do nothing.
- **No draft.** `GameOptions.draft` exists but isn't used yet.
- **Research choices are capped** at what the player can afford at 3 M€ per card.
- **Turmoil isn't modelled**, so Reds costs never apply.
- **Robotic Workforce** copies a card's own production box but not an attack on another
  player's production.

## Adding an expansion

1. Run `python tools/hook_status.py --module <module>` to list the cards that need hooks.
2. Write them in `engine/hooks/<module>.py`, following `engine/hooks/README.md`.
3. Add any new behavior clauses to `behavior.py` and remove the module from `UNSUPPORTED`.
4. Add the module name to `GameOptions.modules` and test it with
   `python -m engine.main --modules base corpera prelude <module> --games 200`.

## Card data

The card data in `src/data/*.json` was generated from the original repository's card
definitions. `tools/extract_methods.py` adds two fields from a checkout of it:

```bash
python tools/extract_methods.py /path/to/terraforming-mars
```

- `methods`: the methods each card class defines (including ones inherited from shared
  parent cards), which is how the status tool knows which hooks a card needs.
- `gameModule`: the expansion the card belongs to.
