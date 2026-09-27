import json
import re
from pathlib import Path


GITHUB_DIR = Path("json_cards")
WEBSITE_FILE = Path("cards.json")
OUTPUT_FILE = Path("cards_unified.json")


def normalize_name(name):
    """Normalize card names so the two datasets can be matched."""
    if not name:
        return ""

    name = name.lower()
    name = name.replace("_", " ")
    name = re.sub(r"[^a-z0-9 ]", "", name)
    name = re.sub(r"\s+", " ", name)

    return name.strip()


def normalize_expansion(expansion):
    """Normalize expansion names to a consistent format."""
    if not expansion:
        return ""

    expansion = expansion.lower().strip()

    aliases = {
        "base": "base",
        "corporate era": "corporateEra",
        "corporateera": "corporateEra",
        "prelude": "prelude",
        "venus next": "venusNext",
        "venusnext": "venusNext",
        "colonies": "colonies",
        "turmoil": "turmoil",
        "promo": "promo",
    }

    return aliases.get(expansion, expansion)


def normalize_type(category):
    """Convert website card categories to our unified types."""
    if not category:
        return None

    categories = {
        "project": "project",
        "corporation": "corporation",
        "prelude": "prelude",
    }

    return categories.get(category.lower(), category.lower())


def load_github_cards():
    """Load all cards from the json_cards directory."""
    cards = []

    for file in GITHUB_DIR.glob("*.json"):
        with file.open("r", encoding="utf-8") as f:
            data = json.load(f)

        # Support either a list of cards or a single card.
        if isinstance(data, list):
            file_cards = data
        else:
            file_cards = [data]

        for card in file_cards:
            card["_source_file"] = file.name
            cards.append(card)

    return cards


def load_website_cards():
    with WEBSITE_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # cards.json may itself be a list.
    if isinstance(data, list):
        return data

    raise ValueError("Expected cards.json to contain a JSON array.")


def build_indexes(github_cards):
    """Create lookup indexes for GitHub cards."""
    by_name = {}

    for card in github_cards:
        name = normalize_name(card.get("name"))

        if name:
            by_name[name] = card

    return by_name


def unify_card(website_card, github_card):
    """Merge a website card and GitHub card into our unified schema."""

    expansion = normalize_expansion(
        website_card.get("exp")
        or github_card.get("expansion")
    )

    number = website_card.get("num")

    # Prefer the website's expansion/number ID.
    if expansion and number:
        card_id = f"{expansion}:{number}"
    else:
        card_id = normalize_name(
            website_card.get("name")
            or github_card.get("name")
        ).replace(" ", "_")

    unified = {
        "id": card_id,

        "name": (
            website_card.get("name")
            or github_card.get("name")
        ),

        "expansion": expansion,

        "number": number,

        "type": normalize_type(
            website_card.get("cat")
            or github_card.get("cardType")
        ),

        "behavior": github_card.get("cardType"),

        "cost": github_card.get("cost"),

        "tags": github_card.get("tags", []),

        "victoryPoints": github_card.get("victoryPoints"),

        "metadata": {
            "github": {
                "className": github_card.get("className"),
                "filePath": github_card.get("filePath"),
            },
            "website": {
                "image": website_card.get("img"),
                "thumbnail": website_card.get("thumb"),
            },
        },
    }

    return unified


def main():
    github_cards = load_github_cards()
    website_cards = load_website_cards()

    github_by_name = build_indexes(github_cards)

    unified_cards = []
    matched_github = set()

    for website_card in website_cards:
        name = normalize_name(website_card.get("name"))

        github_card = github_by_name.get(name)

        if github_card:
            matched_github.add(id(github_card))

            unified = unify_card(
                website_card,
                github_card,
            )

        else:
            # Website card with no GitHub match.
            unified = {
                "id": (
                    f"{normalize_expansion(website_card.get('exp'))}:"
                    f"{website_card.get('num')}"
                ),

                "name": website_card.get("name"),

                "expansion": normalize_expansion(
                    website_card.get("exp")
                ),

                "number": website_card.get("num"),

                "type": normalize_type(
                    website_card.get("cat")
                ),

                "behavior": None,
                "cost": None,
                "tags": [],
                "victoryPoints": None,

                "metadata": {
                    "github": None,
                    "website": {
                        "image": website_card.get("img"),
                        "thumbnail": website_card.get("thumb"),
                    },
                },
            }

            print(
                f"WARNING: No GitHub match for "
                f"'{website_card.get('name')}'"
            )

        unified_cards.append(unified)

    # Add GitHub-only cards so nothing gets lost.
    for github_card in github_cards:
        if id(github_card) in matched_github:
            continue

        expansion = normalize_expansion(
            github_card.get("expansion")
        )

        name = github_card.get("name")

        unified_cards.append({
            "id": f"{expansion}:{normalize_name(name).replace(' ', '_')}",

            "name": name,

            "expansion": expansion,

            "number": None,

            "type": None,

            "behavior": github_card.get("cardType"),

            "cost": github_card.get("cost"),

            "tags": github_card.get("tags", []),

            "victoryPoints": github_card.get("victoryPoints"),

            "metadata": {
                "github": {
                    "className": github_card.get("className"),
                    "filePath": github_card.get("filePath"),
                },
                "website": None,
            },
        })

        print(
            f"WARNING: GitHub-only card "
            f"'{name}'"
        )

    # Sort by expansion, then card number, then name.
    unified_cards.sort(
        key=lambda card: (
            card.get("expansion") or "",
            card.get("number") or "",
            card.get("name") or "",
        )
    )

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(
            unified_cards,
            f,
            indent=2,
            ensure_ascii=False,
        )

    print()
    print(f"GitHub cards:  {len(github_cards)}")
    print(f"Website cards: {len(website_cards)}")
    print(f"Unified cards: {len(unified_cards)}")
    print(f"Output:        {OUTPUT_FILE}")


if __name__ == "__main__":
    main()