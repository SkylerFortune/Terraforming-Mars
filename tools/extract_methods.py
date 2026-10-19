#!/usr/bin/env python3
"""Add `methods` and `gameModule` to the card JSON from a checkout of the original repo.

The card JSON in src/data/ was generated from terraforming-mars/terraforming-mars, but it
doesn't record which methods each card class overrides. Those overrides are the hooks that
have to be written by hand (see src/engine/hooks/README.md), so this script reads them from
the TypeScript sources and writes them back into the JSON:

  * `methods`     sorted names of the methods the card's class defines, including those it
                  inherits from another card class (for example EcologicalZoneAres inherits
                  from EcologicalZone). Methods from framework base classes such as `Card`,
                  `ActionCard` or `CorporationCard` are not included.
  * `gameModule`  the module of the manifest that registers the card. This tells the base
                  game (`base`) apart from Corporate Era (`corpera`), which share a folder.

Only those two keys are touched; everything else in the JSON is left as it is.

Usage (from the project root):

    git clone --depth 1 https://github.com/terraforming-mars/terraforming-mars /tmp/tm-upstream
    python tools/extract_methods.py /tmp/tm-upstream

Standard library only. Python 3.10+.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Framework classes: their methods run the card's data, so they aren't hand-written hooks.
FRAMEWORK_CLASSES = {
    "Card", "ActionCard", "CorporationCard", "ActiveCorporationCard", "PreludeCard",
    "ActivePreludeCard", "CeoCard", "StandardProjectCard", "StandardActionCard",
}

CLASS_RE = re.compile(r"^export (?:abstract )?class (\w+)(?: extends (\w+))?", re.M)
METHOD_RE = re.compile(
    r"^  (?:public |protected |private )?(?:static )?(?:override )?(?:async )?(\w+)\s*(?:<[^>]*>)?\(",
    re.M,
)
MANIFEST_RE = re.compile(r"new ModuleManifest\(\{\s*module:\s*'(\w+)'")
ENTRY_RE = re.compile(r"\[CardName\.(\w+)\]:\s*\{\s*Factory:\s*(\w+)")
SKIP_METHODS = {"constructor", "if", "for", "while", "switch", "return", "super"}


def class_bodies(source: str):
    """Yield (class name, parent, body) for each exported class in a file."""
    matches = list(CLASS_RE.finditer(source))
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(source)
        yield m.group(1), m.group(2), source[m.end():end]


def scan_classes(cards_dir: Path) -> dict[str, tuple[str | None, set[str]]]:
    classes: dict[str, tuple[str | None, set[str]]] = {}
    for path in cards_dir.rglob("*.ts"):
        if "render" in path.parts:
            continue
        for name, parent, body in class_bodies(path.read_text(encoding="utf-8")):
            methods = {m for m in METHOD_RE.findall(body) if m not in SKIP_METHODS}
            classes[name] = (parent, methods)
    return classes


def all_methods(cls: str, classes) -> set[str]:
    out: set[str] = set()
    seen = set()
    while cls and cls not in FRAMEWORK_CLASSES and cls in classes and cls not in seen:
        seen.add(cls)
        parent, methods = classes[cls]
        out |= methods
        cls = parent
    return out


def scan_manifests(cards_dir: Path) -> dict[str, str]:
    """CardName key -> module of the manifest that lists it."""
    modules: dict[str, str] = {}
    for path in cards_dir.rglob("*Manifest*.ts"):
        source = path.read_text(encoding="utf-8")
        blocks = list(MANIFEST_RE.finditer(source))
        for i, m in enumerate(blocks):
            end = blocks[i + 1].start() if i + 1 < len(blocks) else len(source)
            for key, _factory in ENTRY_RE.findall(source[m.end():end]):
                modules.setdefault(key, m.group(1))
    return modules


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("upstream", type=Path, help="checkout of terraforming-mars/terraforming-mars")
    ap.add_argument("--data", type=Path, default=Path("src/data"), help="card JSON folder")
    args = ap.parse_args(argv)

    cards_dir = args.upstream / "src" / "server" / "cards"
    if not cards_dir.is_dir():
        print(f"error: {cards_dir} not found", file=sys.stderr)
        return 1
    classes = scan_classes(cards_dir)
    modules = scan_manifests(cards_dir)

    missing_class, missing_module, total = [], [], 0
    for path in sorted(args.data.glob("*.json")):
        cards = json.loads(path.read_text(encoding="utf-8"))
        for card in cards:
            total += 1
            cls = card.get("class")
            if cls not in classes:
                missing_class.append(card["id"])
            card["methods"] = sorted(all_methods(cls, classes))
            module = modules.get(card["id"])
            if module is None:
                missing_module.append(card["id"])
            else:
                card["gameModule"] = module
        path.write_text(json.dumps(cards, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"updated {total} cards in {args.data}")
    if missing_class:
        print(f"{len(missing_class)} cards had no matching class: {', '.join(missing_class[:10])}")
    if missing_module:
        print(f"{len(missing_module)} cards are in no manifest: {', '.join(missing_module[:10])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
