"""The hook registry: `HOOKS[card_id][hook_name] = function`."""
from typing import Callable

HOOKS: dict[str, dict[str, Callable]] = {}


def hook(*card_ids: str, name: str):
    """Register the decorated function as hook `name` for each of `card_ids`."""
    def deco(fn):
        for cid in card_ids:
            if name in HOOKS.setdefault(cid, {}):
                raise ValueError(f"duplicate {name} hook for {cid}")
            HOOKS[cid][name] = fn
        return fn
    return deco
