#!/usr/bin/env python3
"""Report which hand-written card hooks are implemented, missing, or tested.

Compares two things:

  * the generated card data (src/data/*.json), whose `methods` field says which hooks
    each card needs written by hand, and
  * the hook registry (engine.hooks.registry.HOOKS), which says which hooks exist.

It writes a deterministic Markdown report (no timestamps, so diffs in version control only
show real changes) and can fail a CI job when something is wrong.

Usage (from the project root):

    python tools/hook_status.py                    # write src/engine/hooks/STATUS.md
    python tools/hook_status.py --check            # also exit 1 on errors (typos, unknown cards)
    python tools/hook_status.py --require-complete # also exit 1 if any hook is still missing
    python tools/hook_status.py --module moon      # print one module's missing cards, write nothing

Standard library only. Python 3.10+.
"""
from __future__ import annotations

import argparse
import importlib
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------------------
# The hooks that must be written by hand, as named in the original TypeScript, with their
# kind. Anything else in a card's `methods` is a helper and is ignored here. Python names are
# the snake_case form (see to_snake).
# ---------------------------------------------------------------------------------------
HOOK_KINDS: dict[str, str] = {
    # play-time
    "bespokePlay": "play-time", "bespokeCanPlay": "play-time", "bespokePlayBefore": "play-time",
    "play": "play-time", "canPlay": "play-time", "bespokeCanAct": "play-time",
    # action
    "action": "action", "canAct": "action", "actionEssence": "action", "initialAction": "action",
    # trigger
    "onCardPlayed": "trigger", "onCardPlayedByAnyPlayer": "trigger", "onTilePlaced": "trigger",
    "onNonCardTagAdded": "trigger", "onNonCardTagAddedByAnyPlayer": "trigger",
    "onScienceTagAdded": "trigger", "onResourceAdded": "trigger",
    "onIncreaseTerraformRatingByAnyPlayer": "trigger", "onGlobalParameterIncrease": "trigger",
    "onProductionGain": "trigger", "onProductionPhase": "trigger",
    "onColonyAddedByAnyPlayer": "trigger", "onClaim": "trigger",
    "onIdentificationByAnyPlayer": "trigger", "onStandardProject": "trigger",
    "onDiscard": "trigger", "gainsFromTilePlacement": "trigger",
    # modifier
    "getCardDiscount": "modifier", "getStandardProjectDiscount": "modifier",
    "getGlobalParameterRequirementBonus": "modifier", "canPayWith": "modifier",
    # scoring / other
    "getVictoryPoints": "scoring", "productionBox": "other",
    "serialize": "other", "deserialize": "other",
}


def to_snake(name: str) -> str:
    """bespokePlay -> bespoke_play. Idempotent, so already-snake_case data also works."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


HOOKS_BY_SNAKE: dict[str, str] = {to_snake(k): k for k in HOOK_KINDS}  # snake -> original name


# ---------------------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------------------
@dataclass
class CardStatus:
    id: str
    name: str
    module: str
    type: str
    needed: set[str]                       # snake_case hook names the data says it needs
    implemented: set[str] = field(default_factory=set)
    tested: bool = False

    @property
    def missing(self) -> set[str]:
        return self.needed - self.implemented

    @property
    def complete(self) -> bool:
        return not self.missing


@dataclass
class Problem:
    severity: str                          # "error" or "warning"
    code: str
    message: str


# ---------------------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------------------
def load_cards(cards_dir: Path) -> dict[str, CardStatus]:
    """Cards that need at least one hook written by hand."""
    files = sorted(cards_dir.glob("*.json"))
    if not files:
        sys.exit(f"error: no *.json files found in {cards_dir}")
    cards: dict[str, CardStatus] = {}
    for path in files:
        for raw in json.loads(path.read_text(encoding="utf-8")):
            methods = {to_snake(m) for m in (raw.get("methods") or {})}
            needed = methods & HOOKS_BY_SNAKE.keys()
            if not needed:
                continue
            cards[raw["id"]] = CardStatus(
                id=raw["id"], name=raw.get("name", raw["id"]),
                module=raw.get("module", ""), type=raw.get("type", ""), needed=needed)
    return cards


def load_registry(src: Path, module: str) -> dict[str, dict[str, object]]:
    """Import the hooks package (which runs all registrations) and return its HOOKS dict."""
    sys.path.insert(0, str(src.resolve()))
    try:
        pkg = importlib.import_module(module)
    except Exception as exc:  # noqa: BLE001 - report any import failure clearly
        sys.exit(f"error: could not import '{module}' from {src}: {exc!r}")
    for candidate in (pkg, getattr(pkg, "registry", None)):
        hooks = getattr(candidate, "HOOKS", None)
        if isinstance(hooks, dict):
            return hooks
    sys.exit(f"error: '{module}' (or '{module}.registry') has no HOOKS dict")


def find_tested(tests_dir: Path, card_ids: list[str]) -> set[str]:
    """A card counts as tested if a test function is named test_<card_id_lowercase>[_...].

    A test is credited to the *longest* matching card id, so `test_capital_ares_x` counts for
    CAPITAL_ARES and not for CAPITAL.
    """
    if not tests_dir.is_dir():
        return set()
    lowered = sorted(((cid.lower(), cid) for cid in card_ids), key=lambda p: -len(p[0]))
    tested: set[str] = set()
    for path in tests_dir.rglob("test_*.py"):
        for name in re.findall(r"^\s*def (test_\w+)", path.read_text(encoding="utf-8"), re.M):
            stem = name[len("test_"):]
            for low, cid in lowered:
                if stem == low or stem.startswith(low + "_"):
                    tested.add(cid)
                    break
    return tested


# ---------------------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------------------
def analyze(cards: dict[str, CardStatus], registry: dict[str, dict[str, object]]) -> list[Problem]:
    problems: list[Problem] = []
    for cid, hooks in sorted(registry.items()):
        card = cards.get(cid)
        if card is None:
            problems.append(Problem("error", "unknown-card",
                f"hooks registered for `{cid}`, which is not a card that needs hooks "
                f"(typo, or a fully data-driven card)"))
            continue
        for hook_name in sorted(hooks):
            if hook_name not in HOOKS_BY_SNAKE:
                problems.append(Problem("error", "unknown-hook",
                    f"`{cid}` registers `{hook_name}`, which is not a known hook name"))
            elif hook_name in card.needed:
                card.implemented.add(hook_name)
            else:
                problems.append(Problem("warning", "not-required",
                    f"`{cid}` registers `{hook_name}`, but the original card has no such method"))
    return problems


# ---------------------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------------------
def pct(done: int, total: int) -> str:
    return "n/a" if total == 0 else f"{100 * done / total:.0f}%"


def render(cards: dict[str, CardStatus], problems: list[Problem]) -> str:
    all_cards = sorted(cards.values(), key=lambda c: (c.module, c.name))
    total_needed = sum(len(c.needed) for c in all_cards)
    total_done = sum(len(c.needed - c.missing) for c in all_cards)
    complete = sum(c.complete for c in all_cards)
    tested = sum(c.tested for c in all_cards)
    errors = [p for p in problems if p.severity == "error"]
    warnings = [p for p in problems if p.severity == "warning"]

    out: list[str] = []
    w = out.append
    w("# Hooks status")
    w("")
    w("> Generated by `tools/hook_status.py`. Do not edit by hand; run the script to refresh it.")
    w("")
    w("## Summary")
    w("")
    w("| | |")
    w("|---|---|")
    w(f"| Cards that need hand-written hooks | {len(all_cards)} |")
    w(f"| Cards fully implemented | {complete} ({pct(complete, len(all_cards))}) |")
    w(f"| Hooks implemented | {total_done} of {total_needed} ({pct(total_done, total_needed)}) |")
    w(f"| Cards with at least one test | {tested} ({pct(tested, len(all_cards))}) |")
    w(f"| Errors / warnings | {len(errors)} / {len(warnings)} |")
    w("")

    # By module
    by_module: dict[str, list[CardStatus]] = defaultdict(list)
    for c in all_cards:
        by_module[c.module].append(c)
    w("## By module")
    w("")
    w("| Module | Cards | Complete | Hooks done | Hooks needed | Progress | Tested |")
    w("|---|---:|---:|---:|---:|---:|---:|")
    for mod in sorted(by_module):
        cs = by_module[mod]
        needed = sum(len(c.needed) for c in cs)
        done = sum(len(c.needed - c.missing) for c in cs)
        w(f"| {mod} | {len(cs)} | {sum(c.complete for c in cs)} | {done} | {needed} "
          f"| {pct(done, needed)} | {sum(c.tested for c in cs)} |")
    w("")

    # By hook
    needed_by_hook: Counter[str] = Counter()
    done_by_hook: Counter[str] = Counter()
    for c in all_cards:
        for h in c.needed:
            needed_by_hook[h] += 1
            if h not in c.missing:
                done_by_hook[h] += 1
    w("## By hook")
    w("")
    w("| Hook | Kind | Needed | Implemented | Missing |")
    w("|---|---|---:|---:|---:|")
    for h in sorted(needed_by_hook, key=lambda x: (-needed_by_hook[x], x)):
        kind = HOOK_KINDS[HOOKS_BY_SNAKE[h]]
        w(f"| `{h}` | {kind} | {needed_by_hook[h]} | {done_by_hook[h]} "
          f"| {needed_by_hook[h] - done_by_hook[h]} |")
    w("")

    # Problems
    w("## Problems")
    w("")
    if not problems:
        w("None.")
    else:
        for p in sorted(problems, key=lambda p: (p.severity != "error", p.code, p.message)):
            w(f"- **{p.severity}** `{p.code}`: {p.message}")
    w("")

    # Missing, by module
    w("## Missing hooks")
    w("")
    any_missing = False
    for mod in sorted(by_module):
        todo = [c for c in by_module[mod] if c.missing]
        if not todo:
            continue
        any_missing = True
        w(f"<details><summary><strong>{mod}</strong>: {len(todo)} cards still need hooks</summary>")
        w("")
        for c in todo:
            hooks = ", ".join(f"`{h}`" for h in sorted(c.missing))
            w(f"- {c.name} (`{c.id}`, {c.type}): {hooks}")
        w("")
        w("</details>")
        w("")
    if not any_missing:
        w("Nothing missing.")
        w("")
    return "\n".join(out).rstrip() + "\n"


def print_module(cards: dict[str, CardStatus], module: str) -> None:
    todo = sorted((c for c in cards.values() if c.module == module and c.missing),
                  key=lambda c: c.name)
    in_module = [c for c in cards.values() if c.module == module]
    if not in_module:
        known = ", ".join(sorted({c.module for c in cards.values()}))
        sys.exit(f"error: no cards in module '{module}'. Modules: {known}")
    print(f"{module}: {len(in_module) - len(todo)}/{len(in_module)} cards complete")
    for c in todo:
        print(f"  {c.name} ({c.id}): {', '.join(sorted(c.missing))}")


# ---------------------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--cards", type=Path, default=Path("src/data"), help="directory of card JSON files")
    ap.add_argument("--src", type=Path, default=Path("src"), help="directory containing the package")
    ap.add_argument("--hooks-module", default="engine.hooks", help="importable hooks package")
    ap.add_argument("--tests", type=Path, default=Path("tests"), help="tests directory to scan")
    ap.add_argument("--out", type=Path, default=Path("src/engine/hooks/STATUS.md"), help="report path")
    ap.add_argument("--module", help="print one module's missing cards and write nothing")
    ap.add_argument("--check", action="store_true", help="exit 1 if there are errors")
    ap.add_argument("--require-complete", action="store_true",
                    help="exit 1 if any needed hook is missing (implies --check)")
    ap.add_argument("--quiet", action="store_true", help="do not print the summary line")
    args = ap.parse_args(argv)

    cards = load_cards(args.cards)
    registry = load_registry(args.src, args.hooks_module)
    problems = analyze(cards, registry)
    for cid in find_tested(args.tests, list(cards)):
        cards[cid].tested = True

    if args.module:
        print_module(cards, args.module)
        return 0

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render(cards, problems), encoding="utf-8")

    errors = [p for p in problems if p.severity == "error"]
    missing_hooks = sum(len(c.missing) for c in cards.values())
    if not args.quiet:
        done = sum(len(c.needed) - len(c.missing) for c in cards.values())
        total = sum(len(c.needed) for c in cards.values())
        print(f"hooks: {done}/{total} implemented ({pct(done, total)}), "
              f"{sum(c.complete for c in cards.values())}/{len(cards)} cards complete, "
              f"{len(errors)} errors, {len(problems) - len(errors)} warnings -> {args.out}")
    for p in problems:
        if p.severity == "error":
            print(f"ERROR {p.code}: {p.message}", file=sys.stderr)

    if (args.check or args.require_complete) and errors:
        return 1
    if args.require_complete and missing_hooks:
        print(f"{missing_hooks} hooks still missing", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
