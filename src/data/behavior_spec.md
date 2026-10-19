# Terraforming Mars `behavior`: clause-by-clause spec for a Python port

Derived from `src/server/behavior/` (`Behavior.ts`, `Executor.ts`, `Counter.ts`,
`Countable.ts`, `AddResourcesToAnyCardExecutor.ts`) and `src/common/` (`constants.ts`,
`Units.ts`, `TRSource.ts`), checked against the generated card JSON.

**Scope.** A behavior is a JSON object with up to 25 keys (called *clauses* here). The same
format is used by `behavior` (on play), `action` (activated ability) and `firstAction`
(a corporation's opening action), and recursively inside `or` branches. 714 cards use at
least one. `text` and `title` keys are display text only and are ignored when executing.

**Verification markers.** Everything stated here is read from the files above unless marked
**[not in zip]**, which means the logic lives in a file you haven't supplied (board, player,
game, deferred actions) and I am describing it from its name or from how the executor calls it.

---

## 1. The overall shape of execution

An `Executor` has four entry points:

| Method | Purpose |
| --- | --- |
| `canExecute(behavior, player, card, canAffordOptions?)` | Can this behavior be performed right now? |
| `execute(behavior, player, card)` | Perform it |
| `onDiscard(behavior, player, card)` | Undo persistent effects when the card leaves play |
| `toTRSource(behavior, counter)` | How much TR it would give (for the Reds tax) |

### 1.1 Order in which clauses are executed

`execute` handles clauses in this fixed order, **not** in JSON key order:

| # | Clause | Immediate or deferred |
| --- | --- | --- |
| 1 | `or` | Deferred prompt (or runs at once when `autoSelect` and only one option) |
| 2 | `spend` | Pays now, or defers payment and runs the rest afterward (see 1.3) |
| 3 | `removeResourcesFromAnyCard` | Deferred; rest runs afterward only if not blocked (see 1.3) |
| 4 | `lose` | Immediate (in the types, **unused by current card data**) |
| 5 | `production` | Immediate |
| 6 | `stock` | Immediate |
| 7 | `standardResource` | Deferred prompt |
| 8 | `steelValue`, `titaniumValue`, `greeneryDiscount` | Immediate |
| 9 | `drawCard` | Immediate call into player (**[not in zip]**) |
| 10 | `global` | Immediate (temperature, then oxygen, then venus) |
| 11 | `tr` | Immediate |
| 12 | `addResources` | Deferred |
| 13 | `addResourcesToAnyCard` | Deferred |
| 14 | `decreaseAnyProduction` | Deferred |
| 15 | `removeAnyPlants` | Deferred |
| 16 | `colonies` | `buildColony` deferred; fleet, discount, offset immediate |
| 17 | `ocean`, `city`, `greenery`, `tile` | Deferred (except `city` with a fixed `space`) |
| 18 | `turmoil` | `influenceBonus` immediate; `sendDelegates` deferred |
| 19 | `moon` | Fixed-space tiles and rate changes immediate; others deferred |
| 20 | `underworld` | `identify`, `excavate` deferred; `corruption`, `markThisGeneration` immediate |
| 21 | `log` | Immediate |

"Deferred" means the effect is put on the game's queue of deferred actions and resolved
after the current step, with a priority **[not in zip]**. So the order things *resolve* can
differ from the order they were *requested*. Your Python engine needs a queue of pending
actions stored as plain data (see the earlier design notes), and it should match the original's
priority rules.

### 1.2 `canExecute` is mostly a pure check, but it adds warnings and can throw

It returns `false` when the behavior cannot be done. It also **adds warnings** to the card
(`card.addWarning(...)`) in several places without blocking, such as playing an ocean card
after all oceans are placed. Warnings are display-only. Separately, it **throws** on a negative
numeric `stock` value (see `stock` below). In Python, return them as a separate
value (for example `(ok, warnings)`) instead of mutating the card.

### 1.3 Behaviors that split in two

Two clauses stop and finish the rest of the behavior later:

- **`spend`**: after the payment resolves, the executor runs `{...behavior} minus 'spend'`.
- **`removeResourcesFromAnyCard`**: runs the remainder only if the removal was not blocked.

Because the remainder is "the behavior minus the processed key", the cost is paid first and
the reward follows. This is how e.g. *Martian Rails* ("spend 1 energy, gain M€") works. A
latent risk: keys handled **before** the split (`or`) would run again in the remainder.
No current card combines `or` with other top-level keys, so this doesn't occur in the data.

Behavior blocks in the data that mix `spend` with another clause: `stock` (19), `global` (15),
`addResourcesToAnyCard` (12), `addResources` (12), `production` (9), `underworld` (8),
`drawCard` (6), `tr` (5), `ocean` (4), and a few others.

---

## 2. Counting: how `Countable` values are evaluated

Many fields accept either a plain number or a *countable*, an object describing something
to count. Everything goes through one function. `count(c)`:

1. If `c` is a number, return it.
2. Otherwise start `total = 0` and add each matching term below. Several keys in one object
   all add up.
3. Apply `each` (multiply), then `per` (integer divide, rounding down).

```python
def count(state, pid, card, c, context="default") -> int:
    if isinstance(c, int):
        return c
    p = state.players[pid]
    total = 0

    # cities / greeneries: DEFAULT IS EVERY PLAYER'S; only all == False means "just mine"
    if "cities" in c:
        where = c["cities"].get("where", "everywhere")      # onmars | offmars | everywhere
        spaces = cities_on(state, where, owner=pid if c.get("all") is False else None)
        total += len(near_this(state, card, spaces) if "nextToThis" in c else spaces)
    if "greeneries" in c:
        spaces = greeneries(state, owner=pid if c.get("all") is False else None)
        total += len(near_this(state, card, spaces) if "nextToThis" in c else spaces)

    if "oceans" in c:                  # every ocean, including upgraded oceans and wetlands
        spaces = ocean_spaces(state, upgraded=True, wetlands=True)
        total += len(near_this(state, card, spaces) if "nextToThis" in c else spaces)

    if "floaters" in c:                # YOUR floaters across all your cards
        total += resources_of_type(p, "FLOATER")

    if "tag" in c:
        tags = c["tag"] if isinstance(c["tag"], list) else [c["tag"]]
        if len(tags) > 1:
            if c.get("others"): raise ValueError("others + multiple tags is unsupported")
            total += p.tags.multiple_count(tags)
            if card_not_in_tableau(p, card): total += card_tag_count(card, tags)
        else:
            t = tags[0]
            if not c.get("others"):
                total += p.tags.count(t, "default" if context == "default" else "raw")
                if card_not_in_tableau(p, card): total += card.tags.count(t)
            if c.get("all") is True or c.get("others") is True:
                total += sum(o.tags.count(t, "raw") for o in opponents(state, pid))

    if "resourcesHere" in c:
        total += card.resource_count

    if "colonies" in c:                # all truthy -> every colony on every tile, else yours
        total += all_colonies(state) if c.get("all") else my_colonies(state, pid)

    if "moon" in c:
        m = c["moon"]
        if "habitatRate" in m: total += state.moon.habitat_rate
        if "miningRate"  in m: total += state.moon.mining_rate
        if "logisticRate" in m: total += state.moon.logistic_rate
        for key, tile in (("habitat", "MOON_HABITAT"), ("mine", "MOON_MINE"), ("road", "MOON_ROAD")):
            if key in m:
                spaces = moon_spaces(state, tile, surface_only=True)
                total += len(near_this(state, card, spaces) if "nextToThis" in c else spaces)

    if "underworld" in c:
        u = c["underworld"]
        if "corruption" in u:
            total += sum(x.corruption for x in state.players) if c.get("all") is True else p.corruption
        if "excavationMarkers" in u:
            total += excavated(state, None if c.get("all") else pid)
        if "undergroundTokens" in u:
            total += (sum(len(x.tokens) for x in state.players) if c.get("all") else len(p.tokens))

    if "eventsPlayed" in c:
        total += sum(x.events_played for x in state.players) if c.get("all") is True else p.events_played

    if "turmoil" in c:
        t = c["turmoil"]
        if "partyLeaders" in t: total += party_leader_count(state, pid)
        if "max" in t:          total = min(total, t["max"])           # cap BEFORE influence
        if "influence" in t:
            infl = influence_of(state, pid)
            total += -infl if t["influence"].get("subtract") else infl

    if "each" in c: total *= c["each"]
    if "per"  in c: total //= c["per"]                                 # floor division
    return total
```

Notes and quirks (all from `Counter.ts`):

- **Different defaults by kind.** `cities` and `greeneries` count **everyone's** unless
  `all: false`. `tag` counts only **yours** unless `all: true` or `others: true`. `colonies`
  and `underworld`/`eventsPlayed` count only yours unless `all` is set. The source itself calls
  this inconsistency out. `all: false` appears once in the data (a titanium `stock` clause).
- **`tag` with `all: true`** counts your tags *plus* each opponent's raw count. With
  `others: true` it counts opponents only.
- **The card being played counts itself.** If the card is not yet in your tableau (it is still
  being played), its own tags are added. If it is already in the tableau (for example when
  Robotic Workforce replays it), they are not added twice.
- **Wild tags and events.** In the `default` context your tag count follows action rules (wild
  tags count, per the source comment, and events are ignored). In `vps` and global-event
  contexts, and always for opponents, it counts `raw` tags with no wild substitution.
  How `tags.count` works internally is **[not in zip]**.
- **`nextToThis`** restricts tile counts to spaces adjacent to the tile this card placed. If the
  card has no tile on the board, the adjacent set is empty and the count is 0.
- **`includeEvents`** is declared on the type but **never read** by `Counter`, so it has no
  effect. It doesn't appear in any card data.
- `each` is applied before `per`; `per` rounds down.
- `countUnits(partial)` evaluates each of the six resource keys, treating missing ones as 0.

---

## 3. Constants used by behaviors

| Name | Value |
| --- | --- |
| `PRODUCTION_MINIMUMS` | M€ −5; steel, titanium, plants, energy, heat 0 |
| `MAX_OCEAN_TILES` | 9 (11 on Amazonis) |
| `MAX_TEMPERATURE` / `MIN_TEMPERATURE` | 8 / −30 (max 14 on Amazonis) |
| `MAX_OXYGEN_LEVEL` | 14 (18 on Amazonis) |
| `MAX_VENUS_SCALE` | 30 (33 on Amazonis) |
| `MAXIMUM_HABITAT_RATE`, `MAXIMUM_MINING_RATE`, `MAXIMUM_LOGISTIC_RATE` | 8 each |
| `DEFAULT_STEEL_VALUE`, `DEFAULT_TITANIUM_VALUE` | 2, 3 |

The six resources are `megacredits`, `steel`, `titanium`, `plants`, `energy`, `heat`.
`global` values are in **steps**, not degrees (temperature moves 2 °C per step).

---

## 4. Clause reference

Each entry gives the data shape, how often it appears in your data (cards using it),
what `canExecute` checks, and what `execute` does.

### Resources

#### `production` (333)

- **Shape:** `{resource: Countable}` for any of the six resources. Values can be negative.
- **canExecute:** `player.production.canAdjust(units)` must hold, evaluated with the counted
  units. This is where `PRODUCTION_MINIMUMS` applies. `canAdjust` itself is **[not in zip]**,
  so check that minimums are enforced as: new production ≥ minimum.
- **execute:** add the counted units to production (logged).

#### `stock` (148)

- **Shape:** `{resource: Countable}`. Only non-negative values appear.
- **canExecute:** always passes. It **throws** if a plain numeric value is negative ("Not
  supporting negative units for now"). Counted values are allowed to be negative, unchecked.
- **execute:** add the counted units to the player's stock.

#### `lose` (0, supported but unused)

- **Shape:** `{production: CountableUnits}` or `{stock: CountableUnits}`.
- **execute:** subtracts, but clamps each unit to `max(0, min(counted, have − minimum))` so it
  never takes more than the player has and never "gains" from a negative count. Never blocks.

#### `standardResource` (4)

- **Shape:** a number, or `{count, same?}` (`same` defaults to `true`).
- **execute (deferred):** `same` true → the player picks **one** resource type and gains `count`
  of it. `same: false` → the player splits `count` across resource types.

### Paying costs

#### `spend` (83)

- **Shape:** exactly one of `megacredits`, `steel`, `titanium`, `plants`, `energy`, `heat`,
  `resourcesHere`, `resourceFromAnyCard: {type}`, `corruption`, `cards`, plus optional
  `canUseSteel` / `canUseTitanium` (only meaningful with `megacredits`).
- **canExecute:**
  - `megacredits`: `player.canAfford({cost, steel: canUseSteel, titanium: canUseTitanium, tr})`.
  - `steel`/`titanium`/`plants`/`energy`/`heat`: the player must have at least that many
    (heat uses `availableHeat()`, **[not in zip]**) and be able to afford it as reserved units.
  - `resourcesHere`: `card.resourceCount >= n`.
  - `resourceFromAnyCard`: at least one of your cards holds that resource type.
  - `corruption`: `player.corruption >= n`.
  - `cards`: at least `n` **other** cards in hand (the card itself doesn't count).
  - Every branch also requires `player.canAfford({cost: 0, tr})`, so if the rest of the
    behavior raises TR under a Reds policy, you must be able to pay the tax.
- **execute:** pay, then run the rest (see 1.3). The payment method differs:
  - `megacredits`: deferred payment prompt (title `payForCardAction`); remainder runs after.
  - `steel`/`titanium`: `player.pay(...)` immediately (this triggers Sol Bank); then continue.
  - `plants`/`energy`: deduct immediately; continue in the same call.
  - `heat`: deferred `spendHeat`; remainder runs after.
  - `resourcesHere`: remove from this card immediately; continue.
  - `resourceFromAnyCard`: deferred pick-a-card removal (unblockable); remainder runs after.
  - `corruption`: lose it immediately; continue.
  - `cards`: deferred select-and-discard of exactly `n` cards (other than this card); remainder
    runs after.
- **TODO in source:** "Spend is not combined with PredictedCost." Costs that get cheaper from
  other effects aren't predicted in `canExecute`.

#### `removeResourcesFromAnyCard` (4)

- **Shape:** `{type, count?: Countable (default 1), source?: 'self' | 'opponents' | 'all' (default 'self')}`.
- **canExecute:** at least one valid target card must exist, **except** in solo mode when the
  source isn't `self` (the attack still resolves in solo "as insurance").
- **execute (deferred):** remove `count` resources of `type`. For non-`self` sources the
  removal is **blockable** by the target. The rest of the behavior runs only if the response is
  `proceed` (*Predators*, *Floating Refinery*).

### Cards and resources on cards

#### `drawCard` (72)

- **Shape:** a number, or `{count, keep?, pay?, tag?, type?, resource?}`.
- **canExecute:** `projectDeck.canDraw(count)` must hold.
- **execute:** number → draw that many. Object with neither `keep` nor `pay` → draw `count`
  with optional filters (`tag`, `resource`, `type`: non-matching cards are discarded). With
  `keep` or `pay` → draw `count`, keep up to `keep`, and if `pay` the player may keep a
  card by paying (for example 3 M€). Exact draw rules are in `Player.drawCard` **[not in zip]**.
- **Data note:** `type: null` on *Crash Landing's* second `addResourcesToAnyCard` entry means
  "any resource type" (the source has `undefined` there).

#### `addResources` (65)

- **Shape:** a number or countable (also seen: `{tag, per}`).
- **execute (deferred):** add `count` resources to **this card**. Special case: if the game is
  in a Double Down replay of this prelude, log a message and add nothing.

#### `addResourcesToAnyCard` (61)

- **Shape:** one object, or an array of up to two objects without `mustHaveCard`. Fields:
  `count` (countable), `type`, `tag` (restrict to cards with that tag), `excludeThis`,
  `min` (only cards already holding at least that many), `robotCards`, `mustHaveCard`,
  `autoSelect`.
- **canExecute:** only when the (non-array) object has `mustHaveCard: true`: at least one
  target card must exist. If exactly one target exists and it is this card while the behavior
  also does `spend.resourcesHere`, it fails (the *Applied Science* self-loop).
- **execute (deferred):** for each entry with `count > 0`, queue a "choose a card and add
  `count`" action filtered by `type`, `tag`, `min` and `excludeThis`.
- **Quirk:** `autoSelect` appears on 12 cards but the executor **never reads it** (the source
  notes "I don't think this is actually used"). Any auto-selection happens inside the deferred
  action **[not in zip]**.

### Production and map attacks

#### `decreaseAnyProduction` (11)

- **Shape:** `{type: Resource, count: number}` (types seen: plants, heat, energy).
- **canExecute:** outside solo mode, at least one player must be able to have that production
  reduced by `count` (`canHaveProductionReduced`). If the **only** legal target is yourself, a
  warning is added but the play is allowed.
- **execute (deferred):** the player chooses a target and the production is reduced. Target
  selection is in the deferred action **[not in zip]**.

#### `removeAnyPlants` (13)

- **Shape:** a number.
- **execute (deferred):** queues a "remove plants from any player" action for that many plants
  (target selection is **[not in zip]**). No `canExecute` check.

### Global parameters and TR

#### `global` (72)

- **Shape:** `{temperature?, oxygen?, venus?}` in steps (oxygen can be −1 on one card).
- **canExecute:** never blocks. It adds warnings if that parameter is already at its maximum.
- **execute:** call `increaseTemperature`, `increaseOxygenLevel`, `increaseVenusScaleLevel` in
  that order. The TR and bonus handling is inside those methods **[not in zip]**.

#### `tr` (47)

- **Shape:** a number or countable (also `{per: 4}`, `{underworld: {undergroundTokens: {}}}`).
- **execute:** count it; `>= 0` raises TR by that amount, negative lowers it. Logged only when
  the value was an object.

### Tiles

For all four, `on` is a **placement rule** name; its definition lives in the board code
**[not in zip]**. Values in your data: `land`, `ocean`, `city`, `isolated`, `volcanic`,
`away-from-cities`, `upgradeable-ocean`, and `upgradeable-ocean-new-holland` (New Holland only).

#### `ocean` (26)

- **Shape:** `{count?: 2, on?, firstPlayerPlaces?: true}`.
- **canExecute:** never blocks; warns when all oceans are placed.
- **execute (deferred):** `count: 2` → two placements (prompts "first" and "second"
  ocean). `firstPlayerPlaces` → the first player chooses the space but **you** are credited
  (*Icy Impactors*). Otherwise one placement, optionally restricted by `on`.

#### `city` (28)

- **Shape:** `{space?, on?}`.
- **canExecute:** with no `space`, there must be at least one valid space for rule `on` (default
  `city`). With a fixed `space`, that space must be **empty** (it can already be occupied for
  *Star Vegas*, which is why it's a special case in the source comment).
- **execute:** fixed `space` → place the city now and tag the tile with this card. Otherwise a
  deferred placement.

#### `greenery` (6)

- **Shape:** `{on?}`.
- **canExecute:** at least one valid space for rule `on` (default `greenery`) **after** removing
  spaces around a Red city (a special rule in `filterSpacesAroundRedCity`).
- **execute (deferred):** place a greenery. Raising oxygen comes with the placement itself.

#### `tile` (25)

- **Shape:** `{type: TileType, on, title?, adjacencyBonus?}`.
- **canExecute:** at least one valid space for rule `on`.
- **execute (deferred):** place a special tile of `type`, associated with this card.
  `adjacencyBonus` is Ares-expansion data (`bonus` list, optional `cost`); its handling is
  **[not in zip]**.

### Persistent modifiers (reversed by `onDiscard`)

| Clause | Data | `execute` | `onDiscard` reverses |
| --- | --- | --- | --- |
| `steelValue` | `1` (3 cards) | `increaseSteelValue()` | `decreaseSteelValue()` |
| `titaniumValue` | `1` or `-1` (4 cards) | `±1` to titanium value | the opposite |
| `greeneryDiscount` | `1` (2 cards) | `plantsNeededForGreenery -= n` | `+= n` |
| `colonies.addTradeFleet` | number | grow fleet that many times | shrink fleet that many times |
| `colonies.tradeDiscount` | number | `tradeDiscount += n` | `-= n` |
| `colonies.tradeOffset` | number | `tradeOffset += n` | `-= n` |

`onDiscard` handles **only** these. Production, stock, tiles and TR are not undone.

### Expansion clauses

#### `colonies` (22)

- **Shape:** `{buildColony?: {allowDuplicates?}, addTradeFleet?, tradeDiscount?, tradeOffset?}`.
- **canExecute:** for `buildColony`, at least one playable colony tile must exist.
- **execute:** `buildColony` is a deferred prompt; the other three are immediate (table above).

#### `turmoil` (17)

- **Shape:** `{influenceBonus?: 1, sendDelegates?: {count, manyParties?}}`.
- **canExecute:** for `sendDelegates`, available delegates must be at least `count`.
- **execute:** `influenceBonus` adds permanent influence immediately. `sendDelegates` with
  `manyParties` → one prompt **per** delegate. Otherwise one prompt that sends all `count` to a
  single party.

#### `moon` (48)

- **Shape:** `{habitatTile?, mineTile?, roadTile?, tile?, habitatRate?, miningRate?, logisticRate?}`.
  The tile entries are objects with an optional `space` (a named Moon space).
- **canExecute:** for a tile without a fixed `space`, a valid space must exist (land for habitat
  and road, mine-eligible space for a mine).
- **execute:** a tile **without** `space` → deferred placement. A tile **with** `space` → place it
  immediately and, for habitat/mine/road, raise that rate by 1. `habitatRate`/`miningRate`/
  `logisticRate` raise the rate by the given amount immediately. `tile` (special Moon tiles)
  places without changing a rate.
- **Source quirk:** the maximum-rate warning compares the card's *increase* (for example 1) to the
  maximum of 8, not the current rate plus the increase, so it likely never fires. It is a warning
  only, so it doesn't affect legality.

#### `underworld` (57)

- **Shape:** `{identify?, excavate?, corruption?, markThisGeneration?}`.
  `identify` is a number or `{count, claim?}`; `excavate` is a number or
  `{count, ignorePlacementRestrictions?}`; `corruption` is a countable.
- **canExecute:** `identify` → `canIdentifyN(count)`; `excavate` → `canExcavateN(count)`.
- **execute:** `identify` is a deferred action; if `claim > 0`, the claim action (with the
  counted claim number) is queued **after** the identify resolves, using the spaces it identified.
  `excavate` is deferred. `corruption` is gained immediately (logged). `markThisGeneration` sets
  the card's `generationUsed` to the current generation (project cards only).

#### `or` (36)

- **Shape:** `{behaviors: [{title, ...behavior}], autoSelect?, title?}`.
- **canExecute:** at least one sub-behavior must be executable. All sub-behaviors are checked
  (so every warning gets set), not just the first success.
- **execute:** build one option per **executable** sub-behavior, labeled by its `title`. If
  exactly one option exists **and** `autoSelect` is true, run it immediately; otherwise queue a
  choice prompt (title from `or.title` if present). Choosing runs `execute` on that sub-behavior.
- **Port note:** the choice must be stored as data (card, field, option index) so a decision can
  be copied and resumed.

#### `log` (1 card: *Voltagon*)

- **Shape:** a string with `${player}` and `${card}` placeholders.
- **execute:** write a game-log line. No effect on state. In Python you can drop it.

---

## 5. TR prediction (Reds tax)

`toTRSource(behavior)` summarizes the TR the behavior would give. It exists only so
`canAfford` can include the extra cost when the Reds policy is active:

| Field | Value |
| --- | --- |
| `tr` | the `tr` clause, counted |
| `temperature` | `global.temperature` |
| `oxygen` | `global.oxygen` plus **1 if the behavior places a greenery** |
| `venus` | `global.venus` |
| `oceans` | `ocean.count ?? 1` when `ocean` is present |
| `moonHabitat` | `moon.habitatRate` + 1 if `habitatTile` |
| `moonMining` | `moon.miningRate` + 1 if `mineTile` |
| `moonLogistic` | `moon.logisticRate` + 1 if `roadTile` |

If your engine doesn't model Turmoil's Reds policy, you can skip this entirely.

---

## 6. Where the data and the code disagree, and other flags

1. **Fixed in the JSON.** *Floater Technology* had `count: '1 /* , mustHaveCard: true */'` because
   my extractor let an inline comment into the value. That's now `1`, and I regenerated the JSON
   files. It was the only such value (the diff changed that one card).
2. **`autoSelect` on `addResourcesToAnyCard`** is present in the data on 12 cards but unused by the
   executor.
3. **`or` plus other top-level clauses** is allowed by the type system but never occurs in the data.
4. **Declared but unused or absent from your data:** `lose`, `includeEvents`, and the Turmoil
   countable fields `max` and `influence` (they exist for global events, not cards).
5. **Not in the zip, so unverified here:** the deferred-action queue and its priorities;
   `Player.drawCard`; `production.canAdjust`; `availableHeat`; the placement rules behind each
   `on` value; `tags.count` and wild-tag handling; Ares `adjacencyBonus`; and how `increase*`
   methods award TR and bonuses. Send `deferredActions/`, `boards/`, `player/` and `turmoil/` if
   you want these specified as precisely as the rest.

## 7. Suggested Python structure

```python
CLAUSE_ORDER = ["or", "spend", "removeResourcesFromAnyCard", "lose", "production", "stock",
                "standardResource", "steelValue", "titaniumValue", "greeneryDiscount",
                "drawCard", "global", "tr", "addResources", "addResourcesToAnyCard",
                "decreaseAnyProduction", "removeAnyPlants", "colonies", "ocean", "city",
                "greenery", "tile", "turmoil", "moon", "underworld", "log"]

def execute(state, pid, card, behavior):
    for key in CLAUSE_ORDER:
        if key in behavior:
            state, stop = CLAUSES[key].run(state, pid, card, behavior)
            if stop:     # spend / removeResourcesFromAnyCard queued a continuation
                return state
    return state
```

A clause that must split the behavior (`spend`, `removeResourcesFromAnyCard`) queues a pending
step whose continuation is data, `("run_remainder", card_id, field, done_keys)`, and signals
`stop`. When that step resolves, it executes `behavior` minus the keys already handled. Use an
explicit set of done keys instead of copying the dict, so a clause can never run twice.
