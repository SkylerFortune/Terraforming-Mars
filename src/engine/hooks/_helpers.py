"""Small helpers shared by the hook modules."""
from __future__ import annotations

from engine.cards import card


def card_tag_count(card_id: str, *tags: str) -> int:
    """How many of `tags` the card itself carries (the original's `tags.cardTagCount`)."""
    c = card(card_id)
    return sum(c.tags.count(t) for t in tags)


def has_positive_vp(card_id: str) -> bool:
    """True when the card's printed victory points are positive (fixed or per-resource)."""
    vp = card(card_id).victory_points
    if vp is None:
        return False
    if isinstance(vp, int):
        return vp > 0
    return True     # per-resource, per-tag and "special" VP are all printed as positive
