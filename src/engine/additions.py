from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    input_path = Path("cards_unified.json")
    if not input_path.exists():
        raise FileNotFoundError(f"File not found: {input_path}")

    with input_path.open("r", encoding="utf-8") as f:
        cards = json.load(f)

    if not isinstance(cards, list):
        raise ValueError("Expected the top-level JSON value to be a list of cards.")

    updated = []
    for card in cards:
        if isinstance(card, dict):
            card = {
                **card,
                "effects": card["effects"] if isinstance(card.get("effects"), list) else [],
                "actions": card["actions"] if isinstance(card.get("actions"), list) else [],
                "on_play": card["on_play"] if isinstance(card.get("on_play"), list) else [],
                "requirements": card["requirements"] if isinstance(card.get("requirements"), list) else [],
            }
        updated.append(card)

    with input_path.open("w", encoding="utf-8") as f:
        json.dump(updated, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Updated {len(updated)} cards in {input_path}")


if __name__ == "__main__":
    main()