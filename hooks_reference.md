# Terraforming Mars card hooks: reference

This document describes every hook that a card can implement by hand in the
Terraforming Mars server code (`src/server/cards`). It is based on the interface
comments in `ICard.ts`, the base classes (`Card`, `ActionCard`, `CorporationCard`,
`StandardProjectCard`), and real implementations on actual cards.

**How to read it**

- **Signature** is the TypeScript signature from the source.
- **Cards** is how many cards implement the hook, from the generated JSON. Variant
  cards (for example the Ares versions) that inherit a hook from a parent count too.
- **Verified vs inferred:** statements about *what a hook does* come from the source.
  The code that *calls* each hook (`Player`, `Game`, the behavior executor) was not in the
  zip, so *when* some hooks fire is inferred from implementations. Those spots are marked
  **(inferred)**.

---

## 1. The big idea: declarative `behavior` plus bespoke hooks

Most cards are described by data (`behavior`, `action`, `requirements`). The base class
runs that data for you. A hook exists for the part that data can't express. Cards are meant
to override the **`bespoke*`** versions and leave the base methods alone:

> Card subclasses should ideally not override `play` and `canPlay`. Instead, they should
> override `bespokeCanPlay` and `bespokePlay`. (`Card.ts`)

### Playing a card

```
canPlay(player)
  1. requirements satisfied?            (data)
  2. behavior can execute?              (data)
  3. bespokeCanPlay(player, options)    (hook)  -> false blocks the play

play(player)
  1. deduct reserve units               (Moon expansion)
  2. bespokePlayBefore(player)          (hook)
  3. execute behavior                   (data)
  4. bespokePlay(player)                (hook)  -> may return a PlayerInput (a prompt)
  5. trigger hooks fire for listeners   (onCardPlayed, onTilePlaced, ...)  (inferred)
```

### Using a card's action

```
canAct(player)
  1. action behavior can execute?       (data)
  2. bespokeCanAct(player)              (hook)

action(player)
  1. execute action behavior            (data)
  2. bespokeAction(player)              (hook, related, see section 9)
```

### Using a standard project

```
canAct(player)    -> player.canAfford(cost after discounts, canPayWith options)
payAndExecute     -> pay, record the project, onStandardProject on tableau cards, actionEssence
```

---

## 2. Summary table

| Hook | Kind | Cards |
| --- | --- | --- |
| `bespokePlay` | Play-time | 210 |
| `bespokeCanPlay` | Play-time | 116 |
| `play` | Play-time | 4 |
| `canPlay` | Play-time | 3 |
| `bespokeCanAct` | Play-time | 1 |
| `bespokePlayBefore` | Play-time | 1 |
| `action` | Action | 111 |
| `canAct` | Action | 111 |
| `actionEssence` | Action | 21 |
| `initialAction` | Action | 12 |
| `onCardPlayed` | Trigger | 45 |
| `onTilePlaced` | Trigger | 28 |
| `onNonCardTagAdded` | Trigger | 19 |
| `onCardPlayedByAnyPlayer` | Trigger | 9 |
| `onResourceAdded` | Trigger | 7 |
| `onIncreaseTerraformRatingByAnyPlayer` | Trigger | 5 |
| `onProductionPhase` | Trigger | 5 |
| `onScienceTagAdded` | Trigger | 5 |
| `onDiscard` | Trigger | 4 |
| `onColonyAddedByAnyPlayer` | Trigger | 3 |
| `onProductionGain` | Trigger | 3 |
| `gainsFromTilePlacement` | Trigger | 2 |
| `onClaim` | Trigger | 2 |
| `onIdentificationByAnyPlayer` | Trigger | 2 |
| `onStandardProject` | Trigger | 2 |
| `onGlobalParameterIncrease` | Trigger | 1 |
| `onNonCardTagAddedByAnyPlayer` | Trigger | 1 |
| `getCardDiscount` | Modifier | 11 |
| `canPayWith` | Modifier | 8 |
| `getStandardProjectDiscount` | Modifier | 7 |
| `getGlobalParameterRequirementBonus` | Modifier | 3 |
| `getVictoryPoints` | Scoring | 12 |
| `productionBox` | Other | 16 |
| `deserialize` | Other | 3 |
| `serialize` | Other | 3 |

**Rule of thumb for a simulation:** *queries* (`can*`, `get*`, `productionBox`) must be pure
and fast. *Effects* (`bespokePlay`, `action`, ...) and *triggers* (`on*`) change the game.

---

## 3. Play-time hooks

### `bespokePlay`

- **Signature:** `bespokePlay(player: IPlayer): PlayerInput | undefined`
- **When:** at the end of `play`, after the card's declarative `behavior` has executed.
- **Does:** the custom part of a card's one-time effect. Returning a `PlayerInput` asks the
  player to make a choice; returning `undefined` means nothing more is needed.
- **Default:** returns `undefined`.
- **Cards:** 210 (events 64, automated 81, preludes 40, active 15, corporations 10).
- **Example:** *Eccentric Sponsor* defers a "play a card from hand" prompt and fizzles the
  prelude if no card is played.
- **Note:** the single biggest category of hand-written code. Many of these ask the player
  to choose something, so they need a "pending decision" model in an AI engine.

### `bespokeCanPlay`

- **Signature:** `bespokeCanPlay(player: IPlayer, canAffordOptions: CanAffordOptions): boolean`
- **When:** at the end of `canPlay`, after requirements and behavior checks pass.
- **Does:** adds a custom condition for being allowed to play the card. Returning `false`
  blocks the play.
- **Default:** returns `true`.
- **Cards:** 116 (automated 53, events 30, preludes 22, active 11).
- **Note:** pure query. The AI calls it constantly to build its list of legal actions.

### `bespokePlayBefore`

- **Signature:** `bespokePlayBefore(player: IPlayer): void`
- **When:** during `play`, after reserve units are deducted and **before** `behavior` executes.
- **Does:** runs custom logic ahead of the declarative effect.
- **Default:** does nothing.
- **Cards:** 1 (*Solar Storm* removes plants from players and defers a data removal).
- **Note:** only needed when the order relative to `behavior` matters.

### `play`

- **Signature:** `play(player: IPlayer): PlayerInput | undefined`
- **Does:** the base method that runs the whole play sequence above. Cards are *supposed* to
  override `bespokePlay` instead.
- **Cards:** 4 override it directly: *Oscar* (CEO), *Local Heat Trapping*, *Soil Enrichment*,
  *Project Eden*.
- **Warning:** overriding `play` without calling `super.play(player)` skips the base steps
  (reserve units and `behavior`). *Oscar* does this deliberately, since CEOs have no
  `behavior` to run.

### `canPlay`

- **Signature:** `canPlay(player: IPlayer, canAffordOptions?: CanAffordOptions): boolean`
- **Does:** base method that checks requirements, then behavior, then `bespokeCanPlay`.
- **Cards:** 3 override it directly: *Local Heat Trapping*, *Ecology Experts*,
  *Tunneling Operation*.
- **Example:** *Local Heat Trapping* works out where its 0-or-1 M€ cost could be paid from
  (heat, Stormcraft floaters, M€) because it has a custom affordability rule.

### `bespokeCanAct`

- **Signature:** `bespokeCanAct(player: IPlayer): boolean`
- **When:** at the end of `canAct` for `ActionCard` and `ActiveCorporationCard`.
- **Does:** adds a custom condition for using the card's action.
- **Default:** returns `true`.
- **Cards:** 1 (*Water Splitting Plant* checks that the player can afford the Reds TR cost
  of raising oxygen).

---

## 4. Action hooks

### `action`

- **Signature:** `action(player: IPlayer): PlayerInput | undefined`
- **Does:** performs the card's activated ability (blue-card action, corporation action, CEO
  action, standard action).
- **Default:** `ActionCard` and `ActiveCorporationCard` execute the card's data-defined
  `action` behavior and then call `bespokeAction`.
- **Cards:** 111 write their own `action` (active 44, CEO 34, corporation 25, preludes 5,
  standard actions 2, standard project 1).
- **Note:** cards whose action is purely data (for example *Birds*, *Ants*) do **not**
  appear in this count. They rely on the base class.

### `canAct`

- **Signature:** `canAct(player: IPlayer): boolean`
- **Does:** whether the action is available right now.
- **Default:** for action cards, the action behavior must be executable and
  `bespokeCanAct` must return `true`. For standard projects it checks
  `player.canAfford(...)` against the discounted cost.
- **Cards:** 111 (active 44, corporation 25, standard projects 19, CEO 16, preludes 5,
  standard actions 2).
- **Example:** *Search For Life* requires the player can afford 1 M€ and the deck can supply
  a card.

### `actionEssence`

- **Signature:** `protected abstract actionEssence(player: IPlayer): void`
- **Where:** `StandardProjectCard` only.
- **When:** called by `payAndExecute` after the player has paid and the project was recorded.
- **Does:** the actual effect of the standard project (build the greenery, raise temperature,
  and so on).
- **Cards:** 21 standard projects (the base set plus Moon, Venus and Underworld variants).

### `initialAction`

- **Signature:** `initialAction?(player: IPlayer): PlayerInput | undefined`
- **Where:** `ICorporationCard`.
- **When:** a corporation's free "first action" at the start of the game.
- **Default:** `CorporationCard` executes the card's data-defined `firstAction` behavior.
- **Cards:** 12 corporations override it (*Aridor* adds a colony tile, *Eris*, *Athena*, and
  others).
- **Related:** `initialActionText` holds the text shown for it.

---

## 5. Trigger hooks (reactions to game events)

All trigger hooks are optional. They run on the cards a player has in play (and corporation,
CEO) when the named event happens. Several take **both** a card owner and the player who
caused the event, so a card can react only to its owner or to anyone.

### Cards being played

#### `onCardPlayed`

- **Signature:** `onCardPlayed(player: IPlayer, card: ICard): PlayerInput | undefined | void`
- **When:** the card's **owner** plays a card (`card` is the card just played).
- **Cards:** 45 (active 21, corporations 21, preludes 2, CEO 1).
- **Example:** *Optimal Aerobraking* gives steel and heat when a space event is played.
- **Note:** the source comment says "Corps have a different callback", but 21 corporations
  implement this same hook, so the comment appears to be out of date.

#### `onCardPlayedByAnyPlayer`

- **Signature:** `onCardPlayedByAnyPlayer(thisCardOwner: IPlayer, card: ICard, activePlayer: IPlayer)`
- **When:** **any** player plays a card.
- **Cards:** 9.
- **Example:** *Solar Logistics* draws its owner a card whenever anyone plays a space event.

#### `onStandardProject`

- **Signature (on cards):** `onStandardProject(player: IPlayer, project: IStandardProjectCard): void`
- **When:** the owner uses a standard project. `StandardProjectCard.onStandardProject` loops
  over the owner's tableau and calls this on each card that defines it.
- **Cards:** 2 (*Credicor*, *Labor Trafficking*).
- **Note:** two different things share this name. The project's own method *broadcasts* the
  event, and the card hook *reacts* to it.

#### `onDiscard`

- **Signature:** `onDiscard?(player: IPlayer): void`
- **Does:** lets a card undo persistent effects when it leaves play. In the sample
  implementations: *Martian Lumber Corp* turns off paying with plants, *Lakefront Resorts*
  resets `player.oceanBonus`, *Exploitation Of Venus* clears a game-wide flag, *Price Wars*
  reverses its cost change.
- **Default:** `Card.onDiscard` runs the behavior's discard handling, then `bespokeOnDiscard`.
- **Cards:** 4 override it directly.
- **Note:** the code that triggers this lives outside the cards folder. **(inferred)** It
  fires when a card is removed from a player's tableau.

### Tiles, tags, resources and rating

#### `onTilePlaced`

- **Signature:** `onTilePlaced(cardOwner: IPlayer, activePlayer: IPlayer, space: Space, boardType: BoardType): void`
- **When:** **any** player places a tile. Compare `cardOwner` with `activePlayer` to tell whose
  placement it was.
- **Cards:** 28 (active 13, corporations 13, CEOs 2). Note: the hook is named
  `onTilePlaced`; there is no `onTilePlayed`.
- **Example:** *Lakefront Resorts* defers a +1 M€ production gain when an ocean is placed,
  at a lower priority (`Priority.OPPONENT_TRIGGER`) when an opponent placed it.

#### `gainsFromTilePlacement`

- **Signature:** `gainsFromTilePlacement?(player: IPlayer, space: Space, tileType: TileType): {stock: Units, production: Units}`
- **Does:** *estimates* what `onTilePlaced` would give the player for placing a tile, without
  doing it. The source says it is used by cards that let a placement pay for their own cost.
  Manutech is applied by the caller.
- **Cards:** 2. *Polaris* returns +4 M€ stock (not during the Solar phase) and +1 M€
  production for an ocean. *Lakefront Resorts* returns +1 M€ production for an ocean.
- **Note:** a pure query. It must stay consistent with the matching `onTilePlaced`.

#### `onNonCardTagAdded` / `onNonCardTagAddedByAnyPlayer`

- **Signatures:** `onNonCardTagAdded(player: IPlayer, tag: Tag): void`,
  `onNonCardTagAddedByAnyPlayer(cardOwner: IPlayer, tag: Tag): void`
- **When:** a tag is gained from something other than playing a card. **(inferred)** *Faraday*
  pairs this with `onCardPlayed` and processes both through the same helper.
- **Cards:** 19 and 1.
- **Example:** *Saturn Systems* gains M€ production when anyone gets a Jovian tag this way.
- **Note:** tags gained by playing a card come through `onCardPlayed` /
  `onCardPlayedByAnyPlayer` instead, so tag-counting cards usually implement both.

#### `onScienceTagAdded`

- **Signature (observed):** `onScienceTagAdded(player: IPlayer, count: number): void`
- **When:** science tags are added. **(inferred)** It is not declared in `ICard.ts`, so its
  caller is not in the zip. The implementations take a `count`.
- **Cards:** 5 (*Demetron Labs* adds 2 data per tag, *Mars University* offers a discard and
  draw per tag, *Pharmacy Union* resolves diseases per tag, *Olympus Conference*,
  *Stem Field Subsidies*).

#### `onResourceAdded`

- **Signature:** `onResourceAdded?(player: IPlayer, playedCard: ICard, count: number): void`
- **When:** a resource is added to a card. `playedCard` is the card that received it, which
  can be this same card or another one.
- **Cards:** 7.
- **Example:** *Meat Industry* gives 2 M€ per animal added to any card.

#### `onIncreaseTerraformRatingByAnyPlayer`

- **Signature:** `onIncreaseTerraformRatingByAnyPlayer?(cardOwner: IPlayer, player: IPlayer, steps: number): void`
- **When:** anybody gains TR. `player` is who gained it, `steps` is how many.
- **Cards:** 5 (*Greta*, *United Nations Mission One*, *Aurorai*, *Anubis Securities*, ...).
- **Example:** *Greta* gives 4 M€ (up to 10 times) when its owner raises TR during the action
  phase, while its once-per-game action is active.

#### `onGlobalParameterIncrease`

- **Signature:** `onGlobalParameterIncrease?(player: IPlayer, parameter: GlobalParameter, steps: number): void`
- **When:** a global parameter goes up.
- **Cards:** 1 (*Venus Contract* gives 3 M€ per Venus step).
- **Note:** the interface doesn't document who `player` is. Check the caller before assuming
  it is the card's owner.

#### `onProductionGain`

- **Signature:** `onProductionGain?(player: IPlayer, resource: Resource, amount: number): void`
- **When:** `player` (the card owner) gains or loses production. `amount` can be negative.
- **Cards:** 3 (*Manutech* gains stock equal to production gained, *Thiolava Vents*,
  *Suitable Infrastructure*).

### Phases and map events

#### `onProductionPhase`

- **Signature:** `onProductionPhase?(player: IPlayer): void`
- **When:** during the production phase, for the card owner. The source says it is used to
  reset state between generations.
- **Cards:** 5.
- **Example:** *Pristar* gives 6 M€ and a resource if its owner did not raise TR this
  generation.

#### `onColonyAddedByAnyPlayer`

- **Signature:** `onColonyAddedByAnyPlayer?(cardOwner: IPlayer, colonyOwner: IPlayer): void`
- **When:** any player adds a colony.
- **Cards:** 3 (*Poseidon* gives +1 M€ production for each colony placed).

#### `onClaim`

- **Signature:** `onClaim?(player: IPlayer, isExcavate: boolean, space: Space | undefined): void`
- **When:** the card owner claims an underground resource (Underworld).
- **Cards:** 2 (*Voltagon* gains 2 energy, *Deepwater Dome*).

#### `onIdentificationByAnyPlayer`

- **Signature:** `onIdentificationByAnyPlayer?(cardOwner: IPlayer, identifyingPlayer: IPlayer | undefined, token: UndergroundResourceToken): void`
- **When:** any player identifies a space. `identifyingPlayer` is `undefined` for the neutral
  player (setup or global events).
- **Cards:** 2 (*Geologist Team* gains 1 TR, if affordable, when an ocean token is revealed).

---

## 6. Modifier hooks (queries that change costs and requirements)

These must have **no side effects**. They run whenever the game works out what a player can
do.

### `getCardDiscount`

- **Signature:** `getCardDiscount?(player: IPlayer, card: IProjectCard): number`
- **Returns:** the M€ discount the owner gets when playing `card`.
- **Cards:** 11.
- **Example:** *Cutting Edge Technology* returns 2 for any card that has requirements.
- **Alternative:** for simple cases there is a data field, `cardDiscount`, that does the same
  thing and is easier to render in the UI.

### `getStandardProjectDiscount`

- **Signature:** `getStandardProjectDiscount?(player: IPlayer, card: IStandardProjectCard): number`
- **Returns:** the M€ discount for a standard project. `StandardProjectCard.getAdjustedCost`
  sums these across the tableau and floors the cost at 0.
- **Cards:** 7.
- **Example:** *Labor Trafficking* returns 6 for the first standard project each generation
  (not Sell Patents).

### `getGlobalParameterRequirementBonus`

- **Signature:** `getGlobalParameterRequirementBonus(player: IPlayer, parameter: GlobalParameter): number`
- **Returns:** a +/- bonus to global parameter requirements for the given parameter.
- **Cards:** 3 (*Rogers*, *Anubis Securities*, *Ecology Experts*).
- **Example:** *Anubis Securities* returns 50 during its initial action, which is high
  enough to ignore any requirement.
- **Alternative:** simple fixed cases use the data field `globalParameterRequirementBonus`
  (for example, *Adaptation Technology* uses `{steps: 2}`).

### `canPayWith`

- **Signature:** `canPayWith(player: IPlayer): StandardProjectCanPayWith`
- **Where:** standard projects.
- **Returns:** extra resource types the player may use to pay. The result is spread into the
  affordability check in `canPlayOptions`. The default is `{}`.
- **Cards:** 8 standard projects.

---

## 7. Scoring

### `getVictoryPoints`

- **Signature:** `getVictoryPoints(player: IPlayer, context?: 'default' | 'projectWorkshop'): number`
- **Returns:** the card's VP right now.
- **Default:** returns the card's numeric `victoryPoints`, or evaluates a data-driven counter.
  Cards with `victoryPoints: 'special'` are expected to override this.
- **Cards:** 12.
- **Example:** *Search For Life* returns 3 if it has any resources on it, else 0.
- **Note:** `context` exists because Project Workshop inspects a card differently from normal
  end-of-game scoring.

---

## 8. Other hooks

### `productionBox`

- **Signature:** `productionBox?(player: IPlayer): Units`
- **Returns:** the production box contents of the card, as units.
- **Used by:** *Robotic Workforce* and *Cyberia Systems*, which copy another building card's
  production.
- **Cards:** 16.
- **Note:** the source says to prefer `behavior` over this, and to use `produce` only for
  special cases (for example *Small Open Pit Mine*).

### `serialize`

- **Signature:** `serialize?(serialized: SerializedCard): void`
- **Does:** writes extra per-card state into the saved game, beyond the fields the base class
  already saves.
- **Cards:** 3. *Self Replicating Robots* saves its target cards and their resource counts.
  *Pharmacy Union* saves `isDisabled`. *Aridor* also uses it.
- **Constraint (from the source):** store plain JSON only. Classes, objects and functions are
  serialized incorrectly.

### `deserialize`

- **Signature:** `deserialize?(serialized: SerializedCard): void`
- **Does:** the reverse. It rebuilds the card's extra state from a saved game.
- **Cards:** 3 (the same cards as `serialize`).
- **Port note:** if your Python game state is plain frozen data that you can copy and save
  directly, you may not need either hook.

---

## 9. Related methods not in the hook list

These appear in the source and are useful context:

| Name | What it is |
| --- | --- |
| `bespokeAction` | Called by `action` after the data-defined action behavior runs. The action-side twin of `bespokePlay`. Defaults to `undefined`. |
| `bespokeOnDiscard` | Called by `onDiscard` after behavior discard handling. Most cards override this instead of `onDiscard`. |
| `cardDiscount` | Data version of `getCardDiscount` for simple discounts. |
| `globalParameterRequirementBonus` | Data version of `getGlobalParameterRequirementBonus` (for example `{steps: 2}`). |
| `produce` | Applies the production change for a card's production box. |
| `computeTr` / `tr` | The TR a card is predicted to give when played. Used for Reds policy cost checks. |
| `getInfluenceBonus` | Declared on `ICard` for dynamic influence. No card in this directory implements it. |
| `getCheckLoops` | Loop guard for cards whose action lets a player replay a card. |
| `onCardPlayedFromAnyPlayer`, `onIncreaseTerraformRating`, `onIdentification`, `onColonyAdded` | Declared as `never` on purpose. They catch accidental misspellings of the real hook names at compile time. |

---

## 10. Notes for building a game engine from this

- **Many effects ask the player a question.** The original code returns `PlayerInput` objects
  and uses `game.defer(...)` / `player.defer(...)` queues with priorities (for example
  `Priority.OPPONENT_TRIGGER`). The order in which triggers resolve is a rules matter, so
  keep it deterministic.
- **Same hook, different cards:** `onCardPlayed` vs `onCardPlayedByAnyPlayer`, and
  `onNonCardTagAdded` vs `onNonCardTagAddedByAnyPlayer`, differ only in whether the owner
  alone or everyone triggers it. Tag-counting cards usually need both the card and non-card
  versions.
- **Pure vs effectful:** `can*`, `get*`, `gainsFromTilePlacement` and `productionBox` should
  never change state. Everything starting with `on`, `bespoke` (except `bespokeCan*`),
  `action`, `play` and `actionEssence` does.
- **Keep paired hooks consistent:** `gainsFromTilePlacement` must agree with `onTilePlaced`,
  and `canAct` with `action`.
